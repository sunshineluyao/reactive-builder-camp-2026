"""Train the synthetic demonstration network using only the Python standard library.

Run `python3 model/train.py` from track3. No remote data or model API is used.
"""

import argparse
import json
import math
import random
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parent
VERSION = "sc-triage-mlp-v1"
SEED = 72517
FEATURES = ["pairDeviationBps", "usdDeviationBps", "alignedUsdPairBps", "persistence"]
SCALES = [200.0, 150.0, 150.0, 1.0]
HIDDEN_SIZE = 6
EPOCHS = 70


def encoded(values):
    return [min(1.0, max(0.0, value / scale)) for value, scale in zip(values, SCALES)]


def reference_policy(usd_deviation, aligned, persistence):
    return usd_deviation >= 85 or (usd_deviation >= 38 and aligned >= 26 and persistence >= 0.4)


def synthetic_rows(count, seed):
    """Sample correlated but varied observations, including independent USD evidence."""
    rng = random.Random(seed)
    rows = []
    for _ in range(count):
        direction = rng.choice((-1, 1))
        pair_move = direction * rng.uniform(51, 200)
        regime = rng.randrange(4)
        if regime == 0:
            usdc, usdt = rng.gauss(0, 9), rng.gauss(0, 9)
        elif regime == 1:
            usdc, usdt = direction * rng.uniform(12, 145), rng.gauss(0, 10)
        elif regime == 2:
            usdc, usdt = rng.gauss(0, 10), -direction * rng.uniform(12, 145)
        else:
            usdc, usdt = rng.uniform(-140, 140), rng.uniform(-140, 140)
        persistence = rng.randrange(6) / 5
        usd_deviation = max(abs(usdc), abs(usdt))
        usd_pair = 10000 * ((10000 + usdc) / (10000 + usdt) - 1)
        aligned = max(0.0, direction * usd_pair)
        # A documented annotation policy supplies training targets in lieu of market labels.
        label = int(reference_policy(usd_deviation, aligned, persistence))
        rows.append((encoded([abs(pair_move), usd_deviation, aligned, persistence]), label))
    return rows


def forward(x, weights):
    hidden = [
        math.tanh(b + sum(a * value for a, value in zip(row, x)))
        for row, b in zip(weights["hiddenWeights"], weights["hiddenBias"])
    ]
    logit = weights["outputBias"] + sum(a * h for a, h in zip(weights["outputWeights"], hidden))
    return hidden, 1.0 / (1.0 + math.exp(-logit))


def fit():
    rng = random.Random(SEED)
    training = synthetic_rows(1200, SEED + 1)
    weights = {
        "hiddenWeights": [[rng.uniform(-0.55, 0.55) for _ in FEATURES] for _ in range(HIDDEN_SIZE)],
        "hiddenBias": [0.0] * HIDDEN_SIZE,
        "outputWeights": [rng.uniform(-0.55, 0.55) for _ in range(HIDDEN_SIZE)],
        "outputBias": 0.0,
    }
    for epoch in range(EPOCHS):
        rng.shuffle(training)
        lr = 0.045 / (1 + epoch / 35)
        for x, target in training:
            hidden, score = forward(x, weights)
            delta = score - target  # sigmoid plus binary cross-entropy
            for j, activation in enumerate(hidden):
                grad = delta * weights["outputWeights"][j] * (1 - activation * activation)
                weights["outputWeights"][j] -= lr * delta * activation
                weights["hiddenBias"][j] -= lr * grad
                for k, value in enumerate(x):
                    weights["hiddenWeights"][j][k] -= lr * grad * value
            weights["outputBias"] -= lr * delta
    # The public artifact fixes all coefficients to 10 decimal places.
    rounded = {
        "hiddenWeights": [[round(k, 10) for k in row] for row in weights["hiddenWeights"]],
        "hiddenBias": [round(k, 10) for k in weights["hiddenBias"]],
        "outputWeights": [round(k, 10) for k in weights["outputWeights"]],
        "outputBias": round(weights["outputBias"], 10),
    }
    holdout = synthetic_rows(400, SEED + 2)
    hits = sum((forward(x, rounded)[1] >= 0.5) == y for x, y in holdout)
    return {
        "version": VERSION,
        "featureOrder": FEATURES,
        "normalizationScales": SCALES,
        "training": {"data": "synthetic", "seed": SEED, "epochs": EPOCHS,
                     "trainRows": len(training), "holdoutRows": len(holdout), "holdoutCorrect": hits},
        **rounded,
    }


def write_assets(model, output):
    output.mkdir(parents=True, exist_ok=True)
    literal = json.dumps(model, indent=2, ensure_ascii=True, allow_nan=False)
    (output / "weights.json").write_text(literal + "\n", encoding="utf-8")
    script = (
        "// Generated from train.py. Values match weights.json exactly.\n"
        "(function (root) {\n  \"use strict\";\n  const model = " + literal + ";\n"
        "  if (typeof module === \"object\" && module.exports) module.exports = model;\n"
        "  root.StablecoinRiskWeights = model;\n})(globalThis);\n"
    )
    (output / "weights.js").write_text(script, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=MODEL_DIR, type=Path)
    args = parser.parse_args()
    result = fit()
    write_assets(result, args.output)
    print(json.dumps(result["training"], sort_keys=True))
