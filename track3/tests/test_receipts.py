# SPDX-License-Identifier: MIT
"""Verify receipt identities, reactive correlations and public/offline provenance."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("receipt_verifier", ROOT / "scripts" / "verify_receipts.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)

RUN = json.loads((ROOT / "evidence" / "local-run.json").read_text())
OTHER_HASH = "0x" + "ca" * 32
OTHER_ADDRESS = "0x" + "73" * 20


def event_log(data, role):
    address = data[role]["address"].lower()
    return next(log for log in data["receipts"][role]["logs"] if log["address"].lower() == address)


def replace_word(log, index, value):
    data = log["data"][2:]
    start = 64 * index
    log["data"] = "0x" + data[:start] + f"{value:064x}" + data[start + 64:]


def public_copy():
    copied = copy.deepcopy(RUN)
    copied["mode"] = "public-testnet"
    return copied


def rpc_from(data, reorg=None):
    """Serve deterministic normalized test responses for the RPC verification branch."""
    def call(_url, role, method, params):
        if method == "eth_chainId":
            return hex(data[role]["chainId"])
        raw = data["receipts"][role]
        if method == "eth_getTransactionReceipt":
            assert params == [data[role]["txHash"]]
            return raw
        assert method == "eth_getBlockByNumber"
        assert params == [hex(int(raw["blockNumber"], 16)), False]
        index = int(raw["transactionIndex"], 16)
        block = {"hash": raw["blockHash"], "number": raw["blockNumber"], "timestamp": raw["blockTimestamp"],
                 "transactions": [OTHER_HASH] * index + [raw["transactionHash"]]}
        if role == "destination" and reorg == "hash":
            block["hash"] = OTHER_HASH
        if role == "origin" and reorg == "time":
            block["timestamp"] = "0x1"
        if role == "destination" and reorg == "position":
            block["transactions"].insert(0, OTHER_HASH)
        return block
    return call


class ReceiptVerificationTests(unittest.TestCase):
    def assert_invalid(self, data, contains=""):
        with self.assertRaises(verifier.VerificationError) as failure:
            verifier.verify_run(data, offline=True)
        self.assertIn(contains, str(failure.exception))

    def test_local_receipts_match_without_public_links(self):
        result, _ = verifier.verify_run(RUN)
        self.assertEqual(result["verification"], "local-evm-rehearsal")
        self.assertEqual(result["alert"]["priceBps"], 9930)
        self.assertEqual(result["alert"]["evidenceId"], event_log(RUN, "destination")["topics"][1])
        self.assertNotIn("transactionUrl", result["legs"]["reactive"])
        self.assertNotEqual(RUN["receipts"]["destination"]["to"].lower(), RUN["destination"]["address"].lower())

    def test_canonical_ethereum_signature_and_solidity_event_id_vectors(self):
        script = """const p=require(process.argv[1]);console.log(JSON.stringify([
          p.keccak(new Uint8Array()),p.keccak(new TextEncoder().encode('Transfer(address,address,uint256)')),
          p.eventId(11155111,'0xcff2801b0c6da21aab20d4da2f2651df48bfd3d51fcc2ac96223bd2837448460',0)]))"""
        output = subprocess.check_output(["node", "-e", script, str(verifier.ENGINE)], text=True)
        self.assertEqual(json.loads(output), [
            "0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470",
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
            "0x1244d50a17152f9b3122ba08a736e1c330f158c9659c9af8b2ac46355832fffe"])

    def test_reverted_missing_or_wrong_receipt(self):
        for role in verifier.ROLES:
            for field, value in [("status", "0x0"), ("transactionHash", OTHER_HASH), ("blockHash", OTHER_HASH),
                                 ("blockNumber", None), ("logs", [])]:
                with self.subTest(role=role, field=field):
                    data = copy.deepcopy(RUN)
                    data["receipts"][role][field] = value
                    self.assert_invalid(data)
            data = copy.deepcopy(RUN)
            del data["receipts"][role]
            self.assert_invalid(data, "missing")

    def test_exact_log_identity(self):
        changes = {"address": OTHER_ADDRESS, "removed": True, "transactionHash": OTHER_HASH,
                   "blockHash": OTHER_HASH, "transactionIndex": "0x5", "data": "0x00"}
        for field, value in changes.items():
            with self.subTest(field=field):
                data = copy.deepcopy(RUN)
                event_log(data, "reactive")[field] = value
                self.assert_invalid(data)
        for index in (0, 1, 2):
            with self.subTest(topic=index):
                data = copy.deepcopy(RUN)
                event_log(data, "destination")["topics"][index] = OTHER_HASH
                self.assert_invalid(data)

    def test_repeated_event_requires_specific_log_index(self):
        data = copy.deepcopy(RUN)
        source = copy.deepcopy(event_log(data, "origin"))
        source["logIndex"] = "0x9"
        data["receipts"]["origin"]["logs"].append(source)
        self.assert_invalid(data, "exactly one")
        data["origin"]["logIndex"] = int(event_log(RUN, "origin")["logIndex"], 16)
        result, _ = verifier.verify_run(data)
        self.assertEqual(result["alert"]["evidenceId"], RUN["alert"]["evidenceId"])
        data["origin"]["logIndex"] = 9
        self.assert_invalid(data)

    def test_mismatched_origin_index_quote_and_time_in_forwarded_data(self):
        for role in ("reactive", "destination"):
            for index, value in enumerate((8, 9929, 1_745_000_000)):
                with self.subTest(role=role, word=index):
                    data = copy.deepcopy(RUN)
                    replace_word(event_log(data, role), index, value)
                    self.assert_invalid(data, "mismatch")

    def test_strict_threshold_including_both_edges(self):
        for price in (0, 9950, 10000, 10050, 20001):
            with self.subTest(price=price):
                data = copy.deepcopy(RUN)
                replace_word(event_log(data, "origin"), 0, price)
                self.assert_invalid(data, "threshold")

    def test_coordinates_mode_and_payload_shape(self):
        for role, field, invalid in (("origin", "txHash", "0x12"), ("destination", "txHash", "0x" + "00" * 32),
                                     ("reactive", "address", "0x" + "00" * 20),
                                     ("reactive", "chainId", 1), ("destination", "logIndex", False)):
            with self.subTest(role=role, field=field):
                data = public_copy()
                data[role][field] = invalid
                self.assert_invalid(data)
        data = copy.deepcopy(RUN)
        data["mode"] = "production"
        self.assert_invalid(data, "mode")
        data = copy.deepcopy(RUN)
        event_log(data, "origin")["topics"].append(OTHER_HASH)
        self.assert_invalid(data, "indexed parameters")

    def test_public_offline_mode_ignores_asserted_verification(self):
        data = public_copy()
        data["snapshot"] = {"verification": "public-rpc-verified"}
        result, _ = verifier.verify_run(data, offline=True,
                                        request_rpc=lambda *args: self.fail("Offline run contacted an RPC"))
        self.assertEqual(result["verification"], "offline-public-snapshot")

    def test_public_branch_uses_rpc_bodies_and_canonical_blocks(self):
        data = public_copy()
        manifest = {key: value for key, value in data.items() if key != "receipts"}
        result, receipts = verifier.verify_run(manifest, request_rpc=rpc_from(data))
        self.assertEqual(receipts, data["receipts"])
        self.assertEqual(result["verification"], "public-rpc-verified")
        self.assertEqual(result["legs"]["reactive"]["transactionUrl"],
                         "https://lasna.reactscan.net/tx/" + data["reactive"]["txHash"])
        for reorg in ("hash", "position", "time"):
            with self.subTest(reorg=reorg), self.assertRaisesRegex(verifier.VerificationError, "canonical"):
                verifier.verify_run(data, request_rpc=rpc_from(data, reorg))

    def test_missing_rpc_chain_identity_never_falls_back(self):
        data = public_copy()
        def wrong_network(_url, _role, method, _params):
            self.assertEqual(method, "eth_chainId")
            return "0x1"
        with self.assertRaisesRegex(verifier.VerificationError, "another network"):
            verifier.verify_run(data, request_rpc=wrong_network)

    def test_cli_exit_codes_and_snapshot_output(self):
        with tempfile.TemporaryDirectory() as name:
            work = Path(name)
            manifest_path = work / "evidence.json"
            snapshot_path = work / "checked.json"
            manifest_path.write_text(json.dumps(RUN))
            result = subprocess.run([sys.executable, str(ROOT / "scripts/verify_receipts.py"),
                                     str(manifest_path), "--json", "--save-snapshot", str(snapshot_path)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["verification"], "local-evm-rehearsal")
            saved = snapshot_path.read_bytes()
            self.assertEqual(json.loads(saved)["receipts"], RUN["receipts"])
            manifest_path.write_text("{}")
            result = subprocess.run([sys.executable, str(ROOT / "scripts/verify_receipts.py"),
                                     str(manifest_path), "--save-snapshot", str(snapshot_path)],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(snapshot_path.read_bytes(), saved)


if __name__ == "__main__":
    unittest.main()
