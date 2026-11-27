#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Decode the three EVM receipts and verify public runs against canonical blocks.

Run from track3 with Python 3.9+ and Node.js 18+:
    python3 scripts/verify_receipts.py evidence/local-run.json
    python3 scripts/verify_receipts.py evidence/public-run.json --save-snapshot public-checked.json
    python3 scripts/verify_receipts.py public-checked.json --offline
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import os
import subprocess
import sys
import tempfile
from urllib import error, parse, request

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "review" / "receipts.js"
ROLES = ("origin", "reactive", "destination")
SIZE_LIMIT = 8 * 1024 * 1024

# Delegate ABI parsing and canonical event checks to the same implementation as the browser.
BRIDGE = """
const fs = require('node:fs');
const api = require(process.argv[1]);
const input = JSON.parse(fs.readFileSync(0,'utf8'));
async function processInput() {
  if (input.action === 'manifest') return {run: api.manifest(input.run), networks: api.networks};
  if (input.action === 'offline') return api.verify(input.run, input.bodies);
  const rpc = async (role,method) => input.responses[role][method];
  return (await api.fetchPublic(input.run,rpc)).result;
}
processInput().then(result => process.stdout.write(JSON.stringify(result))).catch(error => {
  process.stderr.write(error.message);
  process.exitCode = 1;
});
"""


class VerificationError(ValueError):
    """A manifest or receipt is missing, inconsistent or unconfirmed."""


def engine(action, **values):
    try:
        result = subprocess.run(
            ["node", "-e", BRIDGE, str(ENGINE)], input=json.dumps({"action": action, **values}, allow_nan=False),
            text=True, capture_output=True, timeout=20, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise VerificationError("The verifier requires an available Node.js 18+ executable.") from exc
    if result.returncode:
        raise VerificationError(result.stderr.strip() or "The receipt engine could not verify this run.")
    return json.loads(result.stdout)


def rpc_result(url, role, method, params):
    target = parse.urlsplit(url)
    if target.scheme not in ("https", "http") or not target.hostname:
        raise VerificationError(f"{role} RPC requires an HTTP or HTTPS endpoint.")
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    req = request.Request(url, data=json.dumps(payload).encode(), headers={
        "Content-Type": "application/json", "User-Agent": "reactive-track3-receipt-review/1",
    })
    try:
        with request.urlopen(req, timeout=18) as response:
            body = response.read(SIZE_LIMIT + 1)
    except (OSError, ValueError, error.URLError) as exc:
        raise VerificationError(f"{role} RPC could not complete {method}.") from exc
    if len(body) > SIZE_LIMIT:
        raise VerificationError(f"{role} RPC response exceeds the size limit.")
    try:
        response = json.loads(body)
    except (ValueError, UnicodeError) as exc:
        raise VerificationError(f"{role} RPC returned invalid JSON for {method}.") from exc
    if (not isinstance(response, dict) or response.get("jsonrpc") != "2.0" or
            type(response.get("id")) is not int or response["id"] != 1 or
            "error" in response or "result" not in response):
        raise VerificationError(f"{role} RPC returned an invalid response for {method}.")
    return response["result"]


def fetch_leg(role, coordinates, url, call):
    chain = call(url, role, "eth_chainId", [])
    if not isinstance(chain, str) or not chain.startswith("0x"):
        raise VerificationError(f"{role} RPC reported an invalid chain ID.")
    try:
        chain_id = int(chain, 16)
    except ValueError as exc:
        raise VerificationError(f"{role} RPC reported an invalid chain ID.") from exc
    if chain_id != coordinates["chainId"]:
        raise VerificationError(f"{role} RPC belongs to another network.")
    receipt = call(url, role, "eth_getTransactionReceipt", [coordinates["txHash"]])
    if not isinstance(receipt, dict) or not isinstance(receipt.get("blockNumber"), str):
        raise VerificationError(f"No confirmed {role} receipt with a block number.")
    number = receipt["blockNumber"]
    try:
        if not number.startswith("0x") or not 0 <= int(number, 16) <= 2**53 - 1:
            raise ValueError()
        number = hex(int(number, 16))
    except ValueError as exc:
        raise VerificationError(f"{role} receipt block number is invalid.") from exc
    block = call(url, role, "eth_getBlockByNumber", [number, False])
    return {"eth_chainId": chain, "eth_getTransactionReceipt": receipt, "eth_getBlockByNumber": block}


def verify_run(data, *, offline=False, endpoints=None, request_rpc=rpc_result):
    """Return (structured summary, raw bodies). Offline public data never gains live status."""
    normalized = engine("manifest", run=data)
    run, networks = normalized["run"], normalized["networks"]
    if run["mode"] == "local-evm" or offline:
        bodies = data.get("receipts")
        verification = "local-evm-rehearsal" if run["mode"] == "local-evm" else "offline-public-snapshot"
        summary = engine("offline", run=run, bodies=bodies)
    else:
        endpoints = endpoints or {}
        with ThreadPoolExecutor(max_workers=3) as pool:
            pending = {role: pool.submit(fetch_leg, role, run[role],
                                        endpoints.get(role) or networks[role]["rpc"], request_rpc)
                       for role in ROLES}
            responses = {role: pending[role].result() for role in ROLES}
        summary = engine("live", run=run, responses=responses)
        bodies = {role: responses[role]["eth_getTransactionReceipt"] for role in ROLES}
        verification = "public-rpc-verified"
    summary["verification"] = verification
    if run["mode"] == "public-testnet":
        for role in ROLES:
            leg = summary["legs"][role]
            base = networks[role]["explorer"]
            leg["transactionUrl"] = f"{base}/tx/{leg['txHash']}"
            leg["contractUrl"] = f"{base}/address/{leg['address']}"
    return summary, bodies


def save_snapshot(path, data, bodies, verification):
    snapshot = {**data, "receipts": bodies, "snapshot": {
        "checkedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "verification": verification}}
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, prefix=".receipts-", delete=False,
                                         encoding="utf-8") as out:
            temporary = Path(out.name)
            json.dump(snapshot, out, indent=2, ensure_ascii=False)
            out.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("manifest", type=Path, help="version 1 evidence manifest")
    parser.add_argument("--offline", action="store_true", help="inspect saved receipts without proving public inclusion")
    parser.add_argument("--json", action="store_true", help="print machine-readable verification results")
    parser.add_argument("--save-snapshot", metavar="PATH", type=Path, help="write a portable manifest with the raw receipts")
    for role in ROLES:
        parser.add_argument(f"--{role}-rpc", metavar="URL", help=f"override the {role} RPC used for public verification")
    args = parser.parse_args()
    overrides = {role: getattr(args, role+"_rpc") for role in ROLES if getattr(args, role+"_rpc")}
    try:
        if args.manifest.stat().st_size > SIZE_LIMIT:
            raise VerificationError("Evidence manifest exceeds the 8 MiB size limit.")
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
        result, bodies = verify_run(data, offline=args.offline, endpoints=overrides)
        if args.save_snapshot:
            save_snapshot(args.save_snapshot, data, bodies, result["verification"])
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print({
                "local-evm-rehearsal": "Local EVM rehearsal | private-chain receipts match",
                "offline-public-snapshot": "Offline public snapshot | saved receipts match, public inclusion unconfirmed",
                "public-rpc-verified": "Public testnet | receipts and canonical blocks match the selected RPCs",
            }[result["verification"]])
            if overrides and result["verification"] == "public-rpc-verified":
                print("User-supplied RPCs:", ", ".join(sorted(overrides)))
            alert = result["alert"]
            print(f"Event {alert['evidenceId']} | price {alert['priceBps']} bp | observedAt {alert['observedAt']}")
            for role, leg in result["legs"].items():
                print(f"{role:12} chain {leg['chainId']}  block {leg['blockNumber']}  log {leg['logIndex']}")
                print(f"  contract {leg['address']}\n  tx {leg['txHash']}")
                if "transactionUrl" in leg:
                    print(" ", leg["transactionUrl"])
        return 0
    except (VerificationError, OSError, ValueError, TypeError, RecursionError) as exc:
        print(f"Evidence unverified. {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
