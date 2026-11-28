# Day 4 · Trace a cross-chain callback in three steps

**English** · [简体中文](README.md)

This exercise follows **Base Sepolia → Lasna → Base Sepolia**. Your CampOrigin emits Ping, CampReactive processes it on Lasna, and CampCallback records the result on Base Sepolia. The wallet and funding setup from Day 5 can be reused. Archive this Ping and the rejected direct wallet call as separate Day 4 evidence.

~~~mermaid
flowchart TD
    O["Base Sepolia · CampOrigin"] -->|"Ping with value 500"| R["Lasna · CampReactive.react()"]
    R -->|"Request a callback"| P["Base Sepolia · official callback proxy"]
    P -->|"Call onEvent"| C["Base Sepolia · CampCallback"]
    W["MetaMask test wallet"] -.->|"Direct call rejected"| C
~~~

## 1. Prepare MetaMask and test tokens

1. Use the Day 5 test account. Confirm chain IDs **84532** for Base Sepolia and **5318007** for Lasna. Each wallet transaction uses the selected network’s test currency. [Network setup and funding](../cron100/README.en.md#1-add-the-two-networks-to-metamask)
2. Allow **0.001 test ETH plus Base gas** and **0.15 lREACT plus Lasna gas**. To fund both, the exercise suggests about 0.02 Base Sepolia test ETH from OpenFaucet. Sending 0.01 test ETH on Base Sepolia to the official faucet at **0x2afaFD298b23b62760711756088F75B7409f5967** funds the same Lasna address with 1 lREACT. [OpenFaucet](https://openfaucet.org/) · [Reactive faucet](https://dev.reactive.network/reactive-mainnet#reactive-faucet)

## 2. Compile the three contracts in Remix

1. [Open CampRoundTrip.sol in Remix](https://app.remix.live/#url=https://github.com/sunshineluyao/reactive-builder-camp-2026/blob/main/experiments/cross-chain-callback/remix/CampRoundTrip.sol). It combines three reference contracts and pins the SDK. If the link opens the homepage, use the **GitHub** import option with the [source URL](remix/CampRoundTrip.sol).
2. Under **Compile**, choose Solidity **0.8.29**, EVM **cancun** and **Optimizer** with **200 runs**. Compile and check that all three contracts appear.
3. Under **Deploy & Run Transactions**, select **Browser Extension** and connect the MetaMask test wallet. Check that Remix and MetaMask show the intended network. [Remix deployment](https://remix-ide.readthedocs.io/en/latest/run.html) · [Official template](https://github.com/ethpanda-org/reactive-builder-camp/tree/87675f45bdaf7b944028bd6231e463f869b453c8/starter)

## 3. Deploy and bind the contracts

Select each contract in Remix, enter Value and the constructor arguments, then confirm in MetaMask. Copy each address from **Deployed Contracts**. Set Value to **wei** to use the integers below.

| Order | MetaMask network | Contract | Value in wei | Constructor arguments |
| --- | --- | --- | --- | --- |
| 1 | Base Sepolia | CampOrigin | 0 | None |
| 2 | Reactive Lasna | CampReactive | 150000000000000000 (0.15 lREACT) | See next table |
| 3 | Base Sepolia | CampCallback | 1000000000000000 (0.001 test ETH) | Official Base proxy in proxy_, step 2 address in reactive_ |

| CampReactive argument | Value |
| --- | --- |
| originChainId_ | 84532 |
| originContract_ | CampOrigin address from step 1 |
| originTopic0_ | 114684359751101065429392085520984714040648842024659507369580916668773914000541 |
| destChainId_ | 84532 |
| threshold_ | 100 |
| limit_ | 1 |

The Base Sepolia callback proxy is **0x476F44b11F5C942c58f4c8E3d0300E5710743585**. The decimal originTopic0_ above represents the **Ping(address,uint256)** signature hash **0xfd8d0c1dc3ab254ec49463a1192bb2423b3b851adedec1aa94dcd362dc063c9d**. [Official proxy list](https://dev.reactive.network/origins-and-destinations#testnet-chains)

Switch back to **Lasna** and reset Remix Value to **0**. Call **setRecipient** on CampReactive with the step 3 CampCallback address. Read **recipient** to verify the binding.

To reload an instance after switching networks, select the contract and use **Deployed Contracts → Add Contract** with its address. Older Remix versions call this **At Address**.

## 4. Trigger one Ping and collect the three transactions

On Base Sepolia, call **ping(500)** on CampOrigin with Value **0**. Copy the successful BaseScan link. Because 500 meets the threshold of 100, Lasna requests the destination callback.

| Evidence | Where to look | Expected result |
| --- | --- | --- |
| 1 · Source event | BaseScan transaction for ping(500), also accessible from Remix | Successful receipt with a CampOrigin Ping event. |
| 2 · Lasna execution | CampReactive → **Reactive Executions** in Reactscan. Match the source hash from step 1. | Seen and CallbackRequested in one Lasna execution. Copy its explorer URL. |
| 3 · Destination callback | Open **Callbacks** on the same Lasna address, then the corresponding Base Sepolia transaction. | Successful Base receipt with Handled. Read count() = 1 and lastValue() = 500. |

Use the source hash to link the receipts. Seen and Handled both contain originTxHash. If the explorer lacks decoded fields, the first 32 data bytes hold the source hash. [Lasna Reactscan](https://lasna.reactscan.net/) · [Base Sepolia BaseScan](https://sepolia.basescan.org/) · [Track callbacks](https://dev.reactive.network/economy#inspecting-callbacks)

## 5. Check that direct wallet calls are rejected

1. On Base Sepolia, open your deployed **CampCallback** in Remix, set **Value = 0**, and expand **onEvent**.
2. Use your CampReactive address, 84532, 0 and 500. Using the correct Reactive address isolates the caller-authorization check.
3. Gas estimation normally reports **NotAuthorized** or **execution reverted**. Capture the function, network and error, then dismiss the request. If a failed transaction was already broadcast, save its BaseScan link. Verify that **count()** remains **1**.

A direct call sets msg.sender to the wallet. The official Base proxy alone passes onlyServiceProvider. An authorized callback also passes onlyCallbackSender for the injected Reactive address. [Callback authorization](https://dev.reactive.network/callback-contracts)

## 6. Submit the evidence

The [recorded receipts, image and workflow](../../assignments/d4-cross-chain-callback.en.md) accompany the [copy-ready answer](../../assignments/d4-cross-chain-callback-submission.en.txt). If you redeploy, use your own transaction URLs and failure screenshot.

~~~text
A cross-chain callback in three steps
Path: Base Sepolia → Lasna → Base Sepolia
Source CampOrigin.ping(500): [BaseScan transaction URL]
Lasna CampReactive.react(): [Reactscan transaction URL]
Destination CampCallback.onEvent(): [BaseScan transaction URL]
Failure evidence: [rejected direct-call screenshot or failed transaction URL]
Reason: a direct wallet call fails onlyServiceProvider, which accepts the official Base Sepolia callback proxy.
~~~

If only Ping appears, check the subscribed source address, chain ID and topic. If Lasna executed, check the recipient, official target proxy and receiver balance. The two BaseScan transactions refer to different stages on the same network. [Template troubleshooting](https://github.com/ethpanda-org/reactive-builder-camp/blob/87675f45bdaf7b944028bd6231e463f869b453c8/starter/README.md#4-常见报错)
