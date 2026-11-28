"""Reproduce the retrospective market decision for the signed alert. Uses Python 3 and Node.

Run without arguments to verify the published files offline. --refresh fetches the three
public exchanges and regenerates evidence. No key, wallet or signing method is used.
"""

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from verify_receipts import verify_run

TRACK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TRACK / "model"))
from reference import assess

EVIDENCE = TRACK / "evidence" / "market"


def utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def get_record(url):
    for attempt in range(4):
        try:
            request = Request(
                url, headers={"User-Agent": "PegPulse-Research/1.0", "Accept": "application/json"}
            )
            with urlopen(request, timeout=25) as response:
                body = json.load(response)
            if isinstance(body, dict) and body.get("error"):
                raise ValueError(str(body["error"]))
            return {"url": url, "sha256": hashlib.sha256(json_bytes(body)).hexdigest(), "body": body}
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 3:
                raise
            time.sleep(2**attempt)


def validate_record(record, expected_url):
    if (
        record["url"] != expected_url
        or hashlib.sha256(json_bytes(record["body"])).hexdigest() != record["sha256"]
    ):
        raise ValueError("Provider URL or canonical JSON checksum mismatch")


def bar_urls(start, last):
    """start and last are inclusive UTC minute starts. Request fully closed candles only."""
    count = (last - start) // 60 + 1
    return {
        "USDC/USD": f"https://www.bitstamp.net/api/v2/ohlc/usdcusd/?step=60&limit={count}&end={last}",
        "USDT/USD": f"https://api.exchange.coinbase.com/products/USDT-USD/candles?start={utc(start)}&end={utc(last)}&granularity=60",
        "USDC/USDT": f"https://data-api.binance.vision/api/v3/klines?symbol=USDCUSDT&interval=1m&startTime={start * 1000}&endTime={(last + 60) * 1000 - 1}&limit={count}",
    }


def scaled(value, factor):
    decimal = Decimal(str(value))
    if not decimal.is_finite() or decimal <= 0:
        raise ValueError("Non-positive or non-finite market price")
    return int((decimal * factor).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def bars(pair, record, start, last):
    """Map close boundaries to scaled prices. Ignore empty candles; reject conflicting bars."""
    body = record["body"]
    if pair == "USDC/USD":
        if body["data"]["pair"] != pair:
            raise ValueError("Unexpected Bitstamp pair")
        raw = [(int(x["timestamp"]), x["close"], x["volume"]) for x in body["data"]["ohlc"]]
    elif pair == "USDT/USD":
        raw = [(x[0], x[4], x[5]) for x in body]
    else:
        raw = [(x[0] // 1000, x[4], x[5]) for x in body if x[6] == x[0] + 59999]
    prices = {}
    for opening, close, volume in raw:
        if opening % 60 or opening < start or opening > last or Decimal(str(volume)) <= 0:
            continue
        closing = opening + 60
        price = scaled(close, 10000 if pair == "USDC/USDT" else 1000000)
        if closing in prices and prices[closing] != price:
            raise ValueError("Conflicting candle at one timestamp")
        prices[closing] = price
    return dict(sorted(prices.items()))


def make_context(alert, tapes, urls):
    t = alert["observedAt"]
    refs = {}
    for pair in ("USDC/USD", "USDT/USD"):
        times = [stamp for stamp in tapes[pair] if 0 <= t - stamp <= 300]
        if times:
            stamp = max(times)
            refs[pair] = {"observedAt": stamp, "usdMicros": tapes[pair][stamp], "source": urls[pair]}
    hist = [
        {"observedAt": stamp, "priceBps": price, "source": urls["USDC/USDT"]}
        for stamp, price in sorted(tapes["USDC/USDT"].items())
        if 0 < t - stamp <= 900
    ]
    return {
        "schema": "stablecoin-evidence/v1",
        "alertId": alert["evidenceId"],
        "pair": "USDC/USDT",
        "provenance": "observed",
        "references": refs,
        "history": hist,
    }


def output(path, value, refresh):
    if refresh:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    elif json.loads(path.read_text()) != value:
        raise ValueError(f"Reproduction mismatch in {path.name}")


def event_replay(refresh=False, live=False, manifest=None):
    proof, _ = verify_run(
        json.loads((manifest or (EVIDENCE.parent / "public-run.json")).read_text()), offline=not live
    )
    if live and proof["verification"] != "public-rpc-verified":
        raise ValueError("Live assessment requires a public alert in canonical blocks")
    alert = proof["alert"]
    last = (alert["observedAt"] // 60 - 1) * 60
    start = last - 14 * 60
    urls = bar_urls(start, last)
    path = EVIDENCE / "provider-responses.json"
    if live or refresh:
        try:
            records = {key: get_record(url) for key, url in urls.items()}
        except (OSError, ValueError) as error:
            if not live:
                raise
            return {
                "alert": alert,
                "verification": proof["verification"],
                "marketDecision": assess(alert, None),
                "marketStatus": "provider-unavailable",
                "detail": str(error),
            }
    else:
        records = json.loads(path.read_text())
    for key, url in urls.items():
        validate_record(records[key], url)
    try:
        tapes = {key: bars(key, record, start, last) for key, record in records.items()}
        packet = make_context(alert, tapes, urls)
    except (KeyError, IndexError, TypeError, ValueError, ArithmeticError) as error:
        if not live:
            raise
        return {
            "alert": alert,
            "verification": proof["verification"],
            "marketDecision": assess(alert, None),
            "marketStatus": "invalid-provider-data",
            "detail": str(error),
        }
    result = assess(alert, packet)
    if not live and not result["inferenceRan"]:
        raise ValueError(
            "The observed market sources did not meet the frozen model’s evidence requirements"
        )
    report = {
        "alert": alert,
        "eventTimeUtc": utc(alert["observedAt"]),
        "mode": "retrospective-market-replay",
        "originalDecision": assess(alert, None),
        "marketDecision": result,
        "modelWeightsSha256": hashlib.sha256((TRACK / "model/weights.json").read_bytes()).hexdigest(),
        "sourceResponseSha256": {k: r["sha256"] for k, r in records.items()},
    }
    if live:
        return {
            "verification": proof["verification"],
            "alert": alert,
            "marketDecision": result,
            "context": packet,
            "sourceResponseSha256": report["sourceResponseSha256"],
        }
    output(path, records, refresh)
    output(EVIDENCE / "public-context.json", packet, refresh)
    output(EVIDENCE / "public-assessment.json", report, refresh)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--refresh", action="store_true", help="rebuild the archived public example")
    mode.add_argument(
        "--live", action="store_true", help="recheck the chains, fetch markets and run the model"
    )
    parser.add_argument("--run", type=Path, help="a public receipt manifest for --live")
    args = parser.parse_args()
    if args.run and not args.live:
        parser.error("--run requires --live")
    print(json.dumps(event_replay(args.refresh, args.live, args.run), indent=2))
