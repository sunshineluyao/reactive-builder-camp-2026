# Mini-experiment · Stop after two Cron100 callbacks

**English** · [简体中文](d5-cron100.md)

Option A, scheduled execution. Lasna’s `BoundedCron` subscribes to Cron100 and requests a callback at each of two new Cron blocks. On Base Sepolia, `CronReceiver` stores the run number, source Cron block and `block.timestamp`.

## On-chain submission evidence

| Item | Evidence |
| --- | --- |
| Lasna scheduler `BoundedCron` | [0x201E13106fDf34Fb8FEc9174D4e3DFd95b63CC2b](https://lasna.reactscan.net/address/0x201E13106fDf34Fb8FEc9174D4e3DFd95b63CC2b) · [Deployment](https://lasna.reactscan.net/tx/0xb685edbf16e21a5ffa06bc1614fec32cf4b549a8f7498d5333234a4398370e5b) |
| Base Sepolia receiver `CronReceiver` | [0x1F6C0517c73b8E36fEfe298dBb099a5377D9AE21](https://sepolia.basescan.org/address/0x1F6C0517c73b8E36fEfe298dBb099a5377D9AE21) · [Deployment](https://sepolia.basescan.org/tx/0xf2539ab5eed34d23ab9d12590699cf9b15dd4be20e4f60862b170099f6cd44e6) |
| Start Cron100 | [Lasna start transaction](https://lasna.reactscan.net/tx/0x2fcbbbb6e6b459620b412ac9f2dcfe75edcc8b009d57fcb03de02d1eee8c9d2d) |
| First trigger · Lasna block 8797900 | [Lasna execution](https://lasna.reactscan.net/tx/0xcf027168df6970bbf14de08b5f3231f2007ef2da8254d7452480cec1de52f52c) · [Base callback](https://sepolia.basescan.org/tx/0x5e81250cfe684865fb933836223078ce9d18add2f83d71b4fa9f0dbdd255e02f) · 16:31:47 Singapore time |
| Second trigger · Lasna block 8798000 | [Lasna execution](https://lasna.reactscan.net/tx/0x18357019ea70c69ad627fbb2f7980459b2c013eff35540acc8a3abdd0872feb6) · [Base callback](https://sepolia.basescan.org/tx/0x71358f482aeaeade2d6de0dee2d57c386de71f702d879949dfebc5a83fc6716e) · 16:33:34 Singapore time |
| Automatic stop | [Second request and CronStopped](https://lasna.reactscan.net/tx/0x18357019ea70c69ad627fbb2f7980459b2c013eff35540acc8a3abdd0872feb6) |

Both pairs of receipts were verified on November 20, 2026. The source block stored by each Base callback matched the corresponding Lasna request. The two destination timestamps were 107 seconds apart. Final state was `attempts() = 2`, `stopped() = true`, `subscribed() = false`.

[OpenFaucet](https://openfaucet.org/base-sepolia) supplied [0.014 Base Sepolia test ETH](https://sepolia.basescan.org/tx/0xbaf09a3b591d8bad4299da988656aee1c92a5e703974024428c5437564bd57f4). An [official Reactive faucet transaction](https://sepolia.basescan.org/tx/0xd22bdf121fa66fece4e0820052803afd5621ad133eeac5e5166709ba0ed3579b) exchanged test ETH for 1 lREACT.

The project compiled with Solidity 0.8.29. All six Foundry tests passed.

## Preventing runaway execution

Each fresh Cron block gets one request slot. Failed requests consume a slot. The second attempt stops new requests and calls `unsubscribe` with the original filter. A low balance stops it earlier. If unsubscription fails, the local stop remains effective and the administrator can call `stop()` again.

Each chain has its own test budget. The callback has a 300,000 gas limit. The Base receiver checks the official proxy and authorized Lasna contract, records each sequence once and records execution time with `block.timestamp`.

## Submit and reproduce

- [Copy-ready submission](d5-cron100-submission.en.txt) includes the addresses, both pairs of transaction links and safeguards.
- [Browser walkthrough](../experiments/cron100/README.en.md) covers MetaMask funding, Remix deployment, GitHub Actions and a two-network fund-flow diagram.
- [Glossary](../experiments/cron100/GLOSSARY.en.md) defines networks, costs, contracts, evidence and tools, with sources.
- [Contract](../experiments/cron100/src/BoundedCron.sol) · [Tests](../experiments/cron100/test/BoundedCron.t.sol)

## References

- [Cron100 and Omni subscriptions](https://dev.reactive.network/reactive-contracts#cron)
- [Base Sepolia proxy and chain ID](https://dev.reactive.network/origins-and-destinations#testnet-chains)
- [Callback fees and tracking](https://dev.reactive.network/economy#inspecting-callbacks)
- [Lasna faucet](https://dev.reactive.network/reactive-mainnet#reactive-faucet)
- [Lasna explorer](https://lasna.reactscan.net/) · [Base Sepolia explorer](https://sepolia.basescan.org/)
