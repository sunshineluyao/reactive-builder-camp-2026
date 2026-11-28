"""Compare the frozen review policy with referring every crossing, on seven fixed UTC windows.

Run offline by default. --refresh acquires public venue responses and rebuilds the comparison.
"""

import argparse
import collections
import concurrent.futures
import gzip
import json
from datetime import datetime
from decimal import Decimal

from market_evidence import (
    EVIDENCE,
    assess,
    bar_urls,
    bars,
    get_record,
    json_bytes,
    make_context,
    output,
    scaled,
    validate_record,
)

from train import reference_policy

DAYS = ["2023-03-10", "2023-03-11", "2023-03-12", "2023-03-13", "2023-03-14", "2023-03-15", "2026-11-27"]
ROLES = ("USDC/USD", "USDT/USD")
PAIR = "USDC/USDT"
ARCHIVE = EVIDENCE / "comparison-sources.json.gz"


def trade_url(cursor):
    return f"https://api.kraken.com/0/public/Trades?pair=USDCUSDT&since={cursor}&count=1000"


def trade_tape(start, end, records=None):
    """Rebuild closes from ordered trades, and prove that the tape reaches the window end."""
    earliest = str(start * 10**9 - 1)
    cursor, collected, closes, last_id = earliest, [], {}, -1
    for idx in range(120):
        url = trade_url(cursor)
        record = get_record(url) if records is None else records[idx]
        validate_record(record, url)
        data = record["body"]["result"]
        rows = data["USDCUSDT"]
        collected.append(record)
        if not rows or int(data["last"]) <= int(cursor):
            raise ValueError("Kraken tape ended before the requested window")
        for price, volume, ts, _, _, _, trade_id in rows:
            if trade_id <= last_id:
                continue  # overlapping boundary trade
            last_id = trade_id
            if start <= ts < end and Decimal(volume) > 0:
                closing = (int(ts) // 60 + 1) * 60
                closes[closing] = scaled(price, 10000)
        if rows[-1][2] >= end:
            if records is not None and len(records) != idx + 1:
                raise ValueError("Unexpected Kraken pages")
            return closes, collected, trade_url(earliest)
        cursor = data["last"]
    raise ValueError("Partial trade tape")


def review_day(day, saved=None):
    first = int(datetime.fromisoformat(day + "T13:00:00+00:00").timestamp())
    start, last = first - 16 * 60, first + 63 * 60
    urls = bar_urls(start, last)
    refs = {role: get_record(urls[role]) for role in ROLES} if saved is None else saved["references"]
    for role in ROLES:
        validate_record(refs[role], urls[role])
    tapes = {role: bars(role, refs[role], start, last) for role in ROLES}
    tapes[PAIR], pages, urls[PAIR] = trade_tape(
        start, last + 60, None if saved is None else saved["trades"]
    )
    counts = collections.Counter(
        dict.fromkeys(
            (
                "scheduled",
                "observed",
                "crossings",
                "futureUnavailable",
                "comparable",
                "persistent",
                "baselineReferrals",
                "modelReferrals",
                "baselineUnnecessary",
                "modelUnnecessary",
                "modelMissed",
                "modelAbstentions",
                "persistentAbstentions",
                "modelObserved",
                "ruleReferrals",
                "ruleUnnecessary",
                "ruleMissed",
                "ruleAbstentions",
                "rulePersistentAbstentions",
            ),
            0,
        )
    )
    counts["scheduled"] = 60
    for ts in range(first, first + 3600, 60):
        p = tapes[PAIR].get(ts)
        if p is None:
            continue
        counts["observed"] += 1
        if abs(p - 10000) <= 50:
            continue
        counts["crossings"] += 1
        future = [tapes[PAIR].get(ts + k * 60) for k in range(1, 6)]
        if None in future:
            counts["futureUnavailable"] += 1
            continue
        counts["comparable"] += 1
        direction = 1 if p > 10000 else -1
        positive = sum(direction * (q - 10000) > 50 for q in future) >= 3
        alert = {"evidenceId": "kraken-minute-" + str(ts), "observedAt": ts, "priceBps": p}
        classification = assess(alert, make_context(alert, tapes, urls))
        action, features = classification["decision"], classification["features"]
        if features is None:
            counts["ruleAbstentions"] += 1
            counts["rulePersistentAbstentions"] += int(positive)
        else:
            refer = reference_policy(
                features["usdDeviationBps"], features["alignedUsdPairBps"], features["persistence"]
            )
            counts["ruleReferrals"] += int(refer)
            counts["ruleUnnecessary"] += int(refer and not positive)
            counts["ruleMissed"] += int(not refer and positive)
        counts["persistent"] += int(positive)
        counts["baselineReferrals"] += 1
        counts["baselineUnnecessary"] += int(not positive)
        counts["modelReferrals"] += int(action == "escalate")
        counts["modelUnnecessary"] += int(action == "escalate" and not positive)
        counts["modelMissed"] += int(action == "observe" and positive)
        counts["modelAbstentions"] += int(action == "insufficient")
        counts["persistentAbstentions"] += int(action == "insufficient" and positive)
        counts["modelObserved"] += int(action == "observe")
    return day, {"references": refs, "trades": pages}, dict(counts)


def compare(refresh=False, write_summary=False):
    inputs = {} if refresh else json.loads(gzip.decompress(ARCHIVE.read_bytes()))
    if not refresh and set(inputs) != set(DAYS):
        raise ValueError("Unexpected comparison dates")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        tasks = [pool.submit(review_day, day, inputs.get(day)) for day in DAYS]
        days = {}
        total = collections.Counter()
        for task in tasks:
            day, records, counts = task.result()
            inputs[day] = records
            days[day] = counts
            total.update(counts)
    result = {
        "modelVersion": assess({}, None)["modelVersion"],
        "windowUtc": "13:00–13:59 inclusive, closing boundaries",
        "originVenue": "Kraken USDC/USDT",
        "references": ["Bitstamp USDC/USD", "Coinbase Exchange USDT-USD"],
        "outcome": "At least 3 of the next 5 consecutive traded minute closes are beyond 50 bp in the trigger direction. All 5 are required.",
        "days": days,
        "total": dict(total),
    }
    if refresh:
        ARCHIVE.write_bytes(gzip.compress(json_bytes(inputs), compresslevel=9, mtime=0))
    output(EVIDENCE / "comparison.json", result, refresh or write_summary)
    return result


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--refresh", action="store_true")
    cli.add_argument("--write-summary", action="store_true", help="rebuild counts from archived prices")
    args = cli.parse_args()
    print(json.dumps(compare(args.refresh, args.write_summary), indent=2))
