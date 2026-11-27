"""Independent Python reference for the browser decision and score.

Usage: python3 model/reference.py model/cases.json
"""

import json
import math
import re
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
MODEL = json.loads((DIR / "weights.json").read_text(encoding="utf-8"))
MAX_SAFE_INT = 2**53 - 1


def integer(value):
    return type(value) in (int, float) and abs(value) <= MAX_SAFE_INT and value == int(value)


def price_ok(value):
    return integer(value) and 1 <= value <= 20000


def source_ok(value, provenance):
    if not isinstance(value, str) or not 0 < len(value) <= 1000 or value.strip() != value:
        return False
    if provenance == "synthetic" and re.fullmatch(r"fixture:[a-z0-9/_:.+-]+", value, re.I):
        return True
    match = re.fullmatch(r"https://([a-zA-Z0-9.-]+)(?::([0-9]{1,5}))?(?:[/?#][^\s\\]*)?", value)
    return bool(match and (not match[2] or int(match[2]) <= 65535) and all(
        re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?", part) for part in match[1].split(".")))


def score(features):
    inputs = [min(1.0, max(0.0, features[key] / scale)) for key, scale in
              zip(MODEL["featureOrder"], MODEL["normalizationScales"])]
    activations = [math.tanh(bias + sum(w * x for w, x in zip(row, inputs)))
                   for row, bias in zip(MODEL["hiddenWeights"], MODEL["hiddenBias"])]
    logit = MODEL["outputBias"] + sum(w * a for w, a in zip(MODEL["outputWeights"], activations))
    return 1 / (1 + math.exp(-logit))


def assess(alert, context):
    """Return the decision, code, score and feature values shared with runtime.js."""
    def outcome(decision, code, value=None, features=None):
        return {"decision": decision, "code": code, "score": value, "features": features,
                "inferenceRan": value is not None, "modelVersion": MODEL["version"]}

    alert = alert if isinstance(alert, dict) else {}
    t, p, event_id = (alert.get(k) for k in ("observedAt", "priceBps", "evidenceId"))
    if not (integer(t) and t > 0 and price_ok(p) and isinstance(event_id, str)
            and event_id.strip() and len(event_id) <= 512):
        return outcome("insufficient", "invalid_event")
    distance = abs(p - 10000)
    if distance <= 50:
        return outcome("observe", "no_threshold_crossing")
    if not isinstance(context, dict) or context.get("schema") != "stablecoin-evidence/v1" or (
        context.get("pair") != "USDC/USDT" or context.get("alertId") != event_id or
        context.get("provenance") not in ("synthetic", "observed")
    ):
        return outcome("insufficient", "context_mismatch")
    refs = []
    for asset in ("USDC/USD", "USDT/USD"):
        quotes = context.get("references")
        q = quotes.get(asset) if isinstance(quotes, dict) else None
        if (not isinstance(q, dict) or not integer(q.get("usdMicros")) or not 0 < q["usdMicros"] <= 10000000
            or not source_ok(q.get("source"), context["provenance"])):
            return outcome("insufficient", "missing_reference")
        if not integer(q.get("observedAt")) or not 0 < q["observedAt"] <= t or t - q["observedAt"] > 300:
            return outcome("insufficient", "stale_reference")
        refs.append(q["usdMicros"])
    history = context.get("history")
    if not isinstance(history, list) or not 2 <= len(history) <= 24:
        return outcome("insufficient", "missing_history")
    previous, persistent = 0, 0
    direction = 1 if p > 10000 else -1
    for q in history:
        if (not isinstance(q, dict) or not price_ok(q.get("priceBps")) or
            not source_ok(q.get("source"), context["provenance"]) or
            not integer(q.get("observedAt")) or not previous < q["observedAt"] < t or t - q["observedAt"] > 900):
            return outcome("insufficient", "invalid_history")
        previous = q["observedAt"]
        persistent += int(direction * (q["priceBps"] - 10000) > 50)
    if t - previous > 300:
        return outcome("insufficient", "stale_history")
    usdc, usdt = refs
    features = {
        "pairDeviationBps": distance,
        "usdDeviationBps": max(abs(1000000 - usdc), abs(1000000 - usdt)) / 100,
        "alignedUsdPairBps": max(0.0, direction * (usdc / usdt - 1) * 10000),
        "persistence": persistent / len(history),
    }
    value = score(features)
    return outcome("escalate" if value >= 0.5 else "observe", "model_decision", value, features)


if __name__ == "__main__":
    packet = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if "cases" in packet:
        for case in packet["cases"]:
            print(json.dumps({"case": case["name"], **assess(case["alert"], case["context"])}, ensure_ascii=False))
    else:
        print(json.dumps(assess(packet["alert"], packet.get("context")), ensure_ascii=False, indent=2))
