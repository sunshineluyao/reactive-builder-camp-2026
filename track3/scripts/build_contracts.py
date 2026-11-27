"""Compile the three deployable contracts with solc 0.8.29 (no source dependencies)."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "contracts" / "StablecoinAlerts.sol"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--solc", default="solc")
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
version = subprocess.check_output([args.solc, "--version"], text=True)
if "0.8.29+commit.ab55807c" not in version:
    raise SystemExit("This release uses solc 0.8.29+commit.ab55807c")
options = {
    "optimizer": {"enabled": True, "runs": 200}, "evmVersion": "cancun",
    "metadata": {"bytecodeHash": "none"},
    "outputSelection": {"*": {"*": ["abi", "evm.bytecode.object", "evm.methodIdentifiers"]}},
}
spec = {"language": "Solidity", "sources": {SOURCE.name: {"content": SOURCE.read_text()}}, "settings": options}
process = subprocess.run([args.solc, "--standard-json"], input=json.dumps(spec), text=True, capture_output=True, check=True)
output = json.loads(process.stdout[process.stdout.index("{"):])
errors = [e["formattedMessage"] for e in output.get("errors", []) if e["severity"] == "error"]
if errors:
    raise SystemExit("\n".join(errors))
built = output["contracts"][SOURCE.name]
contracts = {}
for name in ("QuoteSource", "ReactiveAlert", "AlertSink"):
    entry = built[name]
    contracts[name] = {"abi": entry["abi"], "bytecode": "0x" + entry["evm"]["bytecode"]["object"],
                       "methodIdentifiers": entry["evm"]["methodIdentifiers"]}
artifact = {"compiler": "0.8.29+commit.ab55807c", "evmVersion": "cancun",
            "sourceSha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(), "contracts": contracts}
body = json.dumps(artifact, ensure_ascii=False, separators=(",", ":")) + "\n"
target = ROOT / "site" / "contracts.json"
if args.check:
    if target.read_text() != body:
        raise SystemExit("Compiled artifact differs from site/contracts.json")
    print("Checked three ABI and bytecode artifacts")
else:
    target.write_text(body)
    print("Wrote", target.name)
