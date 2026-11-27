"""Reproduce the weights and compare the browser evaluator with the Python reference."""

import copy
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

TRACK = Path(__file__).resolve().parents[1]
MODEL_DIR = TRACK / "model"
sys.path.insert(0, str(MODEL_DIR))
import reference
import train


def browser_rows(rows):
    script = """
const fs = require('node:fs');
const api = require(process.argv[1]);
const rows = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(rows.map(row => api.assess(row.alert, row.context))));
"""
    run = subprocess.run([os.environ.get("NODE", "node"), "-e", script, str(MODEL_DIR / "runtime.js")],
                         input=json.dumps(rows), text=True, capture_output=True, check=True)
    return json.loads(run.stdout)


class EvidenceModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.examples = json.loads((MODEL_DIR / "cases.json").read_text())["cases"]
        cls.case = cls.examples[0]

    def assert_parity(self, cases):
        results = browser_rows(cases)
        for case, browser in zip(cases, results):
            py = reference.assess(case["alert"], case["context"])
            for field in ["decision", "code", "inferenceRan", "modelVersion"]:
                self.assertEqual(py[field], browser[field], (case.get("name"), field))
            if py["score"] is None:
                self.assertIsNone(browser["score"])
                self.assertIsNone(browser["features"])
            else:
                self.assertAlmostEqual(py["score"], browser["score"], delta=1e-12)
                for key, value in py["features"].items():
                    self.assertAlmostEqual(value, browser["features"][key], delta=1e-10)
        return results

    def test_frozen_weights_retrain_and_match_both_encodings(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d)
            train.write_assets(train.fit(), output)
            for name in ("weights.json", "weights.js"):
                self.assertEqual((output / name).read_bytes(), (MODEL_DIR / name).read_bytes())

    def test_classic_browser_scripts_and_synthetic_context_builder(self):
        script = """
const fs = require('node:fs'), vm = require('node:vm'), path = require('node:path');
const root = process.argv[1], ctx = vm.createContext({});
for (const filename of ['weights.js', 'runtime.js']) {
  vm.runInContext(fs.readFileSync(path.join(root, filename), 'utf8'), ctx);
}
const {cases} = JSON.parse(fs.readFileSync(path.join(root, 'cases.json'), 'utf8'));
for (const item of cases.slice(0, 4)) {
  const packet = ctx.StablecoinAI.demoContext(item.alert, item.name);
  if (packet.provenance !== 'synthetic' || item.expected !== ctx.StablecoinAI.assess(item.alert, packet).decision)
    throw new Error(item.name);
  if (JSON.stringify(item.context) !== JSON.stringify(packet)) throw new Error('Example drift in ' + item.name);
}
"""
        subprocess.run([os.environ.get("NODE", "node"), "-e", script, str(MODEL_DIR)], check=True)

    def test_reference_cases_and_interpretable_evidence(self):
        rows = self.assert_parity(self.examples)
        for case, result in zip(self.examples, rows):
            self.assertEqual(result["decision"], case["expected"])
        self.assertEqual([r["inferenceRan"] for r in rows], [True, True, False, False, False])
        self.assertGreater(rows[0]["score"], rows[1]["score"])
        self.assertEqual(rows[0]["features"]["pairDeviationBps"], 70)
        self.assertEqual(rows[0]["features"]["usdDeviationBps"], 96)
        self.assertEqual(rows[0]["features"]["persistence"], 1)
        self.assertEqual(rows[0]["provenance"], "synthetic")
        self.assertEqual({item["role"] for item in rows[0]["evidence"]},
                         {"USDC/USD", "USDT/USD", "USDC/USDT history", "alert event"})
        self.assertTrue(all(x["reasonZh"] for x in rows))

    def test_only_independent_references_can_change_the_decision(self):
        unchanged_alert = self.case["alert"]
        unchanged_history = self.case["context"]["history"]
        near_par = dict(self.case["context"], references=self.examples[1]["context"]["references"])
        decisions = self.assert_parity([self.case, dict(alert=unchanged_alert, context=near_par)])
        self.assertEqual(unchanged_history, near_par["history"])
        self.assertEqual([d["features"]["persistence"] for d in decisions], [1.0, 1.0])
        self.assertEqual([d["decision"] for d in decisions], ["escalate", "observe"])

    def test_import_example_binds_to_bundled_local_evm_receipts(self):
        event = json.loads((TRACK / "evidence" / "local-run.json").read_text())["alert"]
        packet = json.loads((MODEL_DIR / "context-example.json").read_text())
        result, = self.assert_parity([dict(alert=event, context=packet)])
        self.assertEqual(result["decision"], "escalate")
        self.assertEqual(result["provenance"], "synthetic")

    def test_strict_threshold_on_both_sides_and_invalid_event(self):
        prices = [0, 9930, 9950, 9951, 10000, 10050, 10051, 20001, True, "9930", 9930.25]
        cases = [dict(alert={**self.case["alert"], "priceBps": p}, context=self.case["context"]) for p in prices]
        rows = self.assert_parity(cases)
        expected = ["invalid_event", "model_decision", "no_threshold_crossing", "no_threshold_crossing",
                    "no_threshold_crossing", "no_threshold_crossing", "model_decision", "invalid_event",
                    "invalid_event", "invalid_event", "invalid_event"]
        self.assertEqual([r["code"] for r in rows], expected)

    def test_abstention_on_bad_timing_identity_and_sources(self):
        cases = []
        def add(ctx, code):
            cases.append(dict(alert=self.case["alert"], context=ctx, expected=code))
        base = self.case["context"]
        event_time = self.case["alert"]["observedAt"]
        add(None, "context_mismatch")
        add(dict(base, schema="unknown/v1"), "context_mismatch")
        add(dict(base, alertId="a different event"), "context_mismatch")
        add(dict(base, provenance="observed"), "missing_reference")  # observed references require HTTPS
        add(dict(base, references={}), "missing_reference")
        for key, val, code in (("observedAt", event_time + 1, "stale_reference"),
                               ("observedAt", event_time - 301, "stale_reference"),
                               ("usdMicros", True, "missing_reference"),
                               ("source", "fixture:usd-reference/trailing\n", "missing_reference"),
                               ("source", "https://user:password@example.org/evidence", "missing_reference")):
            ctx = copy.deepcopy(base)
            ctx["references"]["USDC/USD"][key] = val
            add(ctx, code)
        add(dict(base, history=[]), "missing_history")
        add(dict(base, history=list(reversed(base["history"]))), "invalid_history")
        ctx = copy.deepcopy(base)
        for item in ctx["history"]:
            item["observedAt"] -= 300
        add(ctx, "stale_history")
        rows = self.assert_parity(cases)
        self.assertEqual([r["code"] for r in rows], [c["expected"] for c in cases])
        self.assertTrue(all(r["labelZh"] == "证据不足" and not r["inferenceRan"] for r in rows))

    def test_portability_over_generated_inputs(self):
        rng = random.Random(20261127)
        cases = []
        for _ in range(60):
            ctx = copy.deepcopy(self.case["context"])
            for q in ctx["references"].values():
                q["usdMicros"] = 1000000 + rng.randint(-14099, 14099)
            for h in ctx["history"]:
                h["priceBps"] = rng.randint(9880, 10120)
            p = 10000 + rng.choice((-1, 1)) * rng.randint(51, 210)
            cases.append(dict(alert={**self.case["alert"], "priceBps": p}, context=ctx))
        self.assert_parity(cases)

    def test_declared_observed_packet_supports_source_urls(self):
        ctx = copy.deepcopy(self.case["context"])
        ctx["provenance"] = "observed"
        for key, q in ctx["references"].items():
            q["source"] = "https://example.org/reference/" + key
        for i, q in enumerate(ctx["history"]):
            q["source"] = "https://example.org/pool/" + str(i)
        results = self.assert_parity([dict(alert=self.case["alert"], context=ctx)])
        self.assertTrue(results[0]["inferenceRan"])
        self.assertEqual(results[0]["provenance"], "observed")


if __name__ == "__main__":
    unittest.main()
