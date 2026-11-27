#!/usr/bin/env python3
"""Run the release bytecode on three private Anvil nodes and verify its event-to-callback path.

Use Foundry 1.7.1 (anvil and cast), solc 0.8.29 and Python 3.10+. No public RPC or wallet.
Default output is a fresh local manifest in the working directory. Use --out to select a location.
"""
import argparse
import contextlib
import itertools
import json
from pathlib import Path
import shutil
import socket
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
GENESIS = 1795608000
CHAINS = {"origin": 11155111, "reactive": 5318007, "destination": 84532}
SYSTEM = "0x8888888888888888888888888888888888888888"
PROXY = "0x476f44b11f5c942c58f4c8e3d0300e5710743585"
RECORD = "(uint256,address,uint256,uint256,uint256,uint256,bytes,uint256,uint256,uint256,uint256,uint256)"
PRICE_EVENT = "PriceObserved(uint256,uint256)"
ROUTED_EVENT = "QuoteRouted(bytes32,bytes32,uint256,uint256,uint256)"
ALERT_EVENT = "PriceDeviation(bytes32,bytes32,uint256,uint256,uint256)"
QUEUED_EVENT = "LocalCallbackQueued(address,uint256,address,bytes)"


def verify(condition, message):
    if not condition:
        raise RuntimeError(message)


class Tools:
    def __init__(self, directory):
        def find(name):
            path = str(Path(directory, name).resolve()) if directory else shutil.which(name)
            if not path or not Path(path).is_file():
                raise SystemExit(f"Install {name} or provide its directory with --tools-dir.")
            return path
        self.anvil, self.cast, self.solc = map(find, ("anvil", "cast", "solc"))

    def cmd(self, *args):
        return subprocess.check_output([self.cast, *map(str, args)], text=True).strip()

    def calldata(self, signature, *args):
        return self.cmd("calldata", signature, *args)

    def contracts(self):
        subprocess.run(["python3", str(ROOT / "scripts/build_contracts.py"), "--solc", self.solc, "--check"],
                       check=True)
        source = ROOT / "tests/LocalTransport.sol"
        # Fix the Solidity source-unit name used in the filmed rehearsal. Otherwise the
        # metadata embeds the checkout path, changing the local transport's state root.
        unit = "buildcamp/track3/tests/LocalTransport.sol"
        spec = {"language": "Solidity", "sources": {unit: {"content": source.read_text()}},
                "settings": {"optimizer": {"enabled": True, "runs": 200}, "evmVersion": "cancun",
                             "outputSelection": {"*": {"*": ["evm.deployedBytecode.object"]}}}}
        compiled = subprocess.check_output([self.solc, "--standard-json"], input=json.dumps(spec), text=True)
        result = json.loads(compiled[compiled.index("{"):])["contracts"][unit]
        return {name: "0x" + artifact["evm"]["deployedBytecode"]["object"]
                for name, artifact in result.items()}


class Chain:
    def __init__(self, port, chain_id, clock):
        self.url = f"http://127.0.0.1:{port}"
        self.rpc_id = itertools.count(1)
        self.chain_id = chain_id
        self.clock = clock
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def rpc(self, method, params=None):
        body = {"jsonrpc": "2.0", "id": next(self.rpc_id), "method": method, "params": params or []}
        request = urllib.request.Request(self.url, json.dumps(body).encode(),
                                         {"Content-Type": "application/json"})
        with self.opener.open(request, timeout=5) as response:
            data = json.load(response)
        if "error" in data:
            raise RuntimeError(f"{method}: {data['error']['message']}")
        return data["result"]

    def send(self, sender, data, *, to=None, good=True, value=0):
        self.rpc("evm_setNextBlockTimestamp", [next(self.clock)])
        tx = {"from": sender, "data": data, "gas": hex(6_000_000), "gasPrice": hex(2_000_000_000),
              "value": hex(value)}
        if to:
            tx["to"] = to
        tx_hash = self.rpc("eth_sendTransaction", [tx])
        for _ in range(50):
            receipt = self.rpc("eth_getTransactionReceipt", [tx_hash])
            if receipt:
                verify(int(receipt["status"], 16) == int(good),
                       f"Unexpected status on local chain {self.chain_id} for {tx_hash}")
                return receipt
            time.sleep(0.05)
        raise RuntimeError(f"Local receipt timed out on {self.chain_id}")


@contextlib.contextmanager
def node(binary, chain_id, clock):
    with socket.socket() as temp:
        temp.bind(("127.0.0.1", 0))
        port = temp.getsockname()[1]
    process = subprocess.Popen([binary, "--host", "127.0.0.1", "--port", str(port), "--chain-id",
                                str(chain_id), "--timestamp", str(GENESIS), "--hardfork", "cancun",
                                "--accounts", "4", "--threads", "1", "--silent"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    chain = Chain(port, chain_id, clock)
    try:
        for attempt in range(100):
            if process.poll() is not None:
                raise RuntimeError(f"Anvil exited before starting local chain {chain_id}.")
            try:
                detected = chain.rpc("eth_chainId")
            except (OSError, ValueError):
                if attempt == 99:
                    raise
                time.sleep(0.05)
                continue
            verify(int(detected, 16) == chain_id, "Wrong local chain ID")
            yield chain
            break
    finally:
        process.terminate()
        try:
            process.wait(timeout=4)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def word(v):
    return f"{int(v, 16) if isinstance(v, str) else v:064x}"


def topic_events(receipt, addr, topic):
    return [e for e in receipt["logs"] if e["address"].lower() == addr.lower()
            and e["topics"] and e["topics"][0].lower() == topic.lower()]


def single(events, description):
    verify(len(events) == 1, f"Expected one {description}, received {len(events)}")
    return events[0]


def arguments_for_event(log, chain_id):
    topics = list(log["topics"]) + ["0x0"] * (4-len(log["topics"]))
    entries = [chain_id, log["address"], *topics, log["data"], log["blockNumber"],
               0, log["blockHash"], log["transactionHash"], log["logIndex"]]
    return "(" + ",".join(map(str, entries)) + ")"


def payload_from_queue(log, observer, destination, chain_id):
    sender, target_id, recipient = log["topics"][1:]
    verify(int(sender, 16) == int(observer, 16) and int(target_id, 16) == chain_id
           and int(recipient, 16) == int(destination, 16), "Incorrect callback routing")
    raw = bytes.fromhex(log["data"][2:])
    offset = int.from_bytes(raw[:32], "big")
    length = int.from_bytes(raw[offset:offset+32], "big")
    data = raw[offset+32:offset+32+length]
    verify(len(data) == length and data[4:36] == bytes(32), "Invalid callback address placeholder")
    return "0x" + data.hex()


def exercise(tools):
    harness = tools.contracts()
    artifacts = json.loads((ROOT / "site/contracts.json").read_text())["contracts"]
    topics = {s: tools.cmd("keccak", s) for s in (PRICE_EVENT, ROUTED_EVENT, ALERT_EVENT, QUEUED_EVENT)}
    clock = itertools.count(GENESIS + 1)
    checks = []
    with contextlib.ExitStack() as stack:
        src, mid, dst = [stack.enter_context(node(tools.anvil, chain, clock)) for chain in CHAINS.values()]
        s_owner = src.rpc("eth_accounts")[0]
        r_owner = mid.rpc("eth_accounts")[1]
        d_owner = dst.rpc("eth_accounts")[2]
        observer_client = mid.rpc("eth_accounts")[3]
        dst_client = dst.rpc("eth_accounts")[3]
        mid.rpc("anvil_setCode", [SYSTEM, harness["LocalOmni"]])
        dst.rpc("anvil_setCode", [PROXY, harness["LocalProxy"]])

        deployment = {}
        def deploy(chain, owner, name, words="", value=0):
            receipt = chain.send(owner, artifacts[name]["bytecode"] + words, value=value)
            deployment[name] = receipt["transactionHash"]
            return receipt["contractAddress"]
        origin = deploy(src, s_owner, "QuoteSource")
        reactive = deploy(mid, r_owner, "ReactiveAlert", word(origin), value=15 * 10**16)
        sink = deploy(dst, d_owner, "AlertSink", word(PROXY) + word(reactive), value=10**15)
        binding = mid.send(r_owner, tools.calldata("bindDestination(address)", sink), to=reactive)

        def emit_price(value):
            receipt = src.send(s_owner, tools.calldata("publish(uint256)", value), to=origin)
            event = single(topic_events(receipt, origin, topics[PRICE_EVENT]), PRICE_EVENT)
            verify(int(event["data"][2:66], 16) == value, "Source quote differs from input")
            return receipt, event

        def relay_source(event):
            data = tools.calldata(f"deliver(address,{RECORD})", reactive,
                                  arguments_for_event(event, CHAINS["origin"]))
            return mid.send(observer_client, data, to=SYSTEM)

        def count():
            data = tools.calldata("alertCount()")
            return int(dst.rpc("eth_call", [{"to": sink, "data": data}, "latest"]), 16)

        for value in (9990, 9950, 10050):
            _, event = emit_price(value)
            receipt = relay_source(event)
            verify(not topic_events(receipt, reactive, topics[ROUTED_EVENT]), "Quiet or boundary quote routed")
            verify(not topic_events(receipt, SYSTEM, topics[QUEUED_EVENT]) and count() == 0,
                   "Quiet or boundary quote produced a callback")
            checks.append({"name": f"quiet-{value}", "priceBps": value, "alertCount": 0, "status": "passed"})

        source_receipt, source_log = emit_price(9930)
        reactive_receipt = relay_source(source_log)
        route_log = single(topic_events(reactive_receipt, reactive, topics[ROUTED_EVENT]), ROUTED_EVENT)
        queue = single(topic_events(reactive_receipt, SYSTEM, topics[QUEUED_EVENT]), QUEUED_EVENT)
        payload = payload_from_queue(queue, reactive, sink, CHAINS["destination"])
        data = tools.calldata("forward(address,address,bytes)", reactive, sink, payload)
        target_receipt = dst.send(dst_client, data, to=PROXY)
        alert = single(topic_events(target_receipt, sink, topics[ALERT_EVENT]), ALERT_EVENT)
        tx_hash = source_receipt["transactionHash"]
        index = int(source_log["logIndex"], 16)
        evidence_id = tools.cmd("keccak", "0x" + word(CHAINS["origin"]) + word(tx_hash) + word(index))
        verify(route_log["topics"][1:] == alert["topics"][1:] == [evidence_id, tx_hash],
               "The three receipts must refer to the same source event")
        timestamp = int(source_log["data"][66:130], 16)
        expected = "0x" + word(index) + word(9930) + word(timestamp)
        verify(route_log["data"] == alert["data"] == expected and count() == 1,
               "Reactive and receiver results differ from source quote")
        checks.append({"name": "outside-band", "priceBps": 9930, "alertCount": 1, "status": "passed"})
        duplicate = relay_source(source_log)
        verify(not topic_events(duplicate, SYSTEM, topics[QUEUED_EVENT]), "Duplicate source queued another callback")
        second = dst.send(dst_client, data, to=PROXY)
        verify(not topic_events(second, sink, topics[ALERT_EVENT]) and count() == 1,
               "Duplicate callback changed destination state")
        checks.extend([{"name": "duplicate-source", "status": "passed", "alertCount": 1},
                       {"name": "duplicate-callback", "status": "passed", "alertCount": 1}])

        src.send(src.rpc("eth_accounts")[3], tools.calldata("publish(uint256)", 9930), to=origin, good=False)
        mid.send(observer_client, tools.calldata(f"react({RECORD})",
                 arguments_for_event(source_log, CHAINS["origin"])), to=reactive, good=False)
        dst.send(dst_client, payload, to=sink, good=False)
        bad_sender_data = tools.calldata("forward(address,address,bytes)", dst_client, sink, payload)
        dst.send(dst_client, bad_sender_data, to=PROXY, good=False)
        verify(count() == 1, "A rejected call changed destination state")
        checks.extend({"name": name, "status": "passed"} for name in
                      ("publisher-authorization", "system-authorization", "proxy-authorization", "sender-authorization"))
        manifest = {
            "version": 1, "mode": "local-evm",
            "transport": "Three private Anvil nodes. Solidity bytecode executes on each. LocalOmni and LocalProxy emulate cross-network delivery. Addresses and hashes below exist on these private chains only.",
            "compiler": "0.8.29+commit.ab55807c", "evm":"cancun",
            "alert": {"evidenceId": evidence_id, "originTx": tx_hash, "logIndex": index,
                      "priceBps": 9930, "observedAt": timestamp, "alertCount": 1},
            "origin": {"chainId": CHAINS["origin"], "address": origin, "txHash": tx_hash,
                       "deployTx": deployment["QuoteSource"]},
            "reactive": {"chainId": CHAINS["reactive"], "address": reactive,
                         "txHash": reactive_receipt["transactionHash"], "deployTx": deployment["ReactiveAlert"],
                         "bindingTx": binding["transactionHash"]},
            "destination": {"chainId": CHAINS["destination"], "address": sink, "proxy": PROXY,
                            "txHash": target_receipt["transactionHash"], "deployTx": deployment["AlertSink"]},
            "receipts": {"origin": source_receipt, "reactive": reactive_receipt, "destination": target_receipt},
            "checks": checks
        }
        return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tools-dir", help="Directory containing anvil, cast and solc (default: PATH)")
    p.add_argument("--out", type=Path, default=Path("local-run.generated.json"))
    args = p.parse_args()
    manifest = exercise(Tools(args.tools_dir))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"PASS: {len(manifest['checks'])} checks, three real local EVM receipts; {args.out}")


if __name__ == "__main__":
    main()
