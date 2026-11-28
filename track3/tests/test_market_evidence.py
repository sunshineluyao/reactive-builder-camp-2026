"""Offline regression checks for time alignment and the public decision's provenance."""

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

TRACK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TRACK / "scripts"))
import market_evidence as market
from market_benchmark import compare


class MarketReplayTests(unittest.TestCase):
    def test_same_signed_event_has_separate_original_and_observed_decisions(self):
        result = market.event_replay()
        self.assertEqual(
            (result["originalDecision"]["decision"], result["marketDecision"]["decision"]),
            ("insufficient", "observe"),
        )
        inputs = json.loads((market.EVIDENCE / "public-context.json").read_text())
        self.assertEqual(inputs["alertId"], result["alert"]["evidenceId"])
        script = "const [a,p]=JSON.parse(require('fs').readFileSync(0));console.log(JSON.stringify(require('./model/runtime.js').assess(a,p)));"
        js = json.loads(
            subprocess.check_output(
                ["node", "-e", script], input=json.dumps([result["alert"], inputs]), cwd=TRACK, text=True
            )
        )
        self.assertTrue(js["inferenceRan"])
        self.assertEqual(js["decision"], result["marketDecision"]["decision"])
        self.assertAlmostEqual(js["score"], result["marketDecision"]["score"], places=11)

    def test_uses_closed_traded_bars_and_preceding_history(self):
        record = {"body": [[120, 0, 0, 0, 1.4, 5], [60, 0, 0, 0, 0.9, 0], [0, 0, 0, 0, 1.001, 7]]}
        self.assertEqual(market.bars("USDT/USD", record, 0, 60), {60: 1001000})
        sample = {"observedAt": 1000, "evidenceId": "example"}
        tapes = {
            "USDC/USD": {650: 1000000, 1002: 900000},
            "USDT/USD": {990: 999990},
            "USDC/USDT": {100: 10001, 999: 10002, 1000: 9930, 1001: 9900},
        }
        packet = market.make_context(sample, tapes, dict.fromkeys(tapes, "https://example.org/market"))
        self.assertNotIn("USDC/USD", packet["references"])
        self.assertEqual([x["observedAt"] for x in packet["history"]], [100, 999])

    def test_archived_sources_are_bound_to_queries_and_checksums(self):
        items = json.loads((market.EVIDENCE / "provider-responses.json").read_text())
        original = items["USDC/USD"]
        altered = copy.deepcopy(original)
        altered["body"]["data"]["ohlc"][-1]["close"] = "1.25"
        with self.assertRaises(ValueError):
            market.validate_record(altered, original["url"])
        with self.assertRaises(ValueError):
            market.validate_record(original, "https://example.org/other")

    def test_historical_comparison_reconciles_and_abstentions_remain_explicit(self):
        totals = compare()["total"]
        self.assertEqual(totals["crossings"], totals["comparable"] + totals["futureUnavailable"])
        self.assertEqual(
            totals["comparable"],
            totals["modelReferrals"] + totals["modelObserved"] + totals["modelAbstentions"],
        )
        self.assertEqual(
            totals["persistent"],
            totals["modelReferrals"]
            - totals["modelUnnecessary"]
            + totals["modelMissed"]
            + totals["persistentAbstentions"],
        )

    def test_live_path_withholds_score_on_market_outage_and_rejects_local_receipts(self):
        archive = market.event_replay()["alert"]
        with (
            patch.object(
                market,
                "verify_run",
                return_value=({"alert": archive, "verification": "public-rpc-verified"}, None),
            ),
            patch.object(market, "get_record", side_effect=OSError("service unavailable")),
        ):
            row = market.event_replay(live=True)
            self.assertFalse(row["marketDecision"]["inferenceRan"])
            self.assertEqual(row["marketStatus"], "provider-unavailable")
        with self.assertRaisesRegex(ValueError, "requires a public alert"):
            market.event_replay(live=True, manifest=TRACK / "evidence/local-run.json")
