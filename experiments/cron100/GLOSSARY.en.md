# Cron100 experiment glossary

**English** · [简体中文](GLOSSARY.md)

Follow the terms in experiment order. The last column links to primary documentation or the implementation.

## 1. Networks, accounts and wallets

| Term | Meaning in this experiment | Sources and further reading |
| --- | --- | --- |
| Blockchain / EVM | Each chain stores transactions and state. Both networks support the Ethereum Virtual Machine, which executes the compiled Solidity contracts. | [ethereum.org](https://ethereum.org/developers/docs/evm/) |
| Testnet / mainnet | Testnets are networks for rehearsing deployments. This experiment uses test tokens on Lasna and Base Sepolia. | [ethereum.org](https://ethereum.org/developers/docs/networks/) |
| Base Sepolia | Base's test network, chain ID 84532. It uses native test ETH and hosts the receiver. | [docs.base.org](https://docs.base.org/get-started/connect-to-base) |
| Ethereum Sepolia | Ethereum's test network, chain ID 11155111. It has a separate balance and transaction history from Base Sepolia. | [ethereum.org](https://ethereum.org/developers/docs/networks/#sepolia) |
| Reactive Network / Lasna | Reactive executes contracts in response to on-chain events. The scheduled contract runs on Lasna, chain ID 5318007. | [dev.reactive.network](https://dev.reactive.network/reactive-mainnet) |
| MetaMask | Browser wallet for choosing the chain and signing deployment and activation transactions. | [support.metamask.io](https://support.metamask.io/configure/networks/) |
| Account / public address / contract address | A public 0x address can be shared. A wallet signs using a private key. A contract address identifies deployed code. The same wallet address has a separate balance on each chain. | [ethereum.org](https://ethereum.org/developers/docs/accounts/) |
| Recovery phrase / private key | A recovery phrase can restore accounts. A private key controls an account and signs transactions. You only need the public address for faucets and evidence lookups. | [support.metamask.io](https://support.metamask.io/start/user-guide-secret-recovery-phrase-password-and-private-keys/) |
| RPC / chain ID | An RPC endpoint connects the wallet or application to a node. The chain ID identifies the network when selecting it or signing. | [eips.ethereum.org](https://eips.ethereum.org/EIPS/eip-1474) · [docs.base.org](https://docs.base.org/get-started/connect-to-base) |
| Block explorer | Search by address, hash or block number. Use Reactscan for Lasna and BaseScan for Base Sepolia. | [lasna.reactscan.net](https://lasna.reactscan.net/) · [sepolia.basescan.org](https://sepolia.basescan.org/) |

## 2. Funds, native test tokens and fees

| Term | Meaning in this experiment | Sources and further reading |
| --- | --- | --- |
| Faucet / OpenFaucet | A faucet provides test tokens. OpenFaucet performs small proofs of work in the browser and sends earned test ETH to a public address on the chosen network. | [openfaucet.org](https://openfaucet.org/) |
| Base Sepolia ETH | The network's native test token pays for deployment and destination callbacks. | [docs.base.org](https://docs.base.org/get-started/connect-to-base) |
| Chainlink LINK | LINK is a Chainlink token available from its test faucet. The Cron receiver pays Base Sepolia gas with native test ETH. | [faucets.chain.link](https://faucets.chain.link/) · [ethereum.org](https://ethereum.org/developers/docs/gas/) |
| Reactive faucet / lREACT | The faucet receives Base Sepolia ETH and sends native test lREACT on Lasna. At the exercise rate of 100 lREACT per ETH, 0.01 test ETH yields 1 lREACT. | [dev.reactive.network](https://dev.reactive.network/reactive-mainnet#reactive-faucet) |
| wei / ether / Value | Wei is the smallest EVM accounting unit. One ether is 10¹⁸ wei. Remix’s Value field uses these units for the selected chain’s native token, lREACT on Lasna. | [docs.soliditylang.org](https://docs.soliditylang.org/en/v0.8.29/units-and-global-variables.html#ether-units) · [Contract tests](https://remix-ide.readthedocs.io/en/latest/run.html) |
| Gas / gas limit | Gas measures computation. A gas limit bounds gas units. The experiment requests a 300,000-unit limit per callback. The fee also depends on the gas used and its price. | [ethereum.org](https://ethereum.org/developers/docs/gas/) · [dev.reactive.network](https://dev.reactive.network/economy) |
| Wallet and contract balances | The wallet funds deployment and activation. Value attached to a constructor becomes that contract’s balance and pays Lasna execution or Base Sepolia callback fees. | [dev.reactive.network](https://dev.reactive.network/economy) |
| minimumReserve / reserve / debt | The scheduler checks minimumReserve before opening a request. The exercise uses 0.1 lREACT. The system contract or callback proxy accounts for Reactive reserves and debts. | [Contract source](src/BoundedCron.sol) · [dev.reactive.network](https://dev.reactive.network/economy) |

## 3. Contracts, events and cross-chain execution

| Term | Meaning in this experiment | Sources and further reading |
| --- | --- | --- |
| Smart contract / Solidity | A smart contract is a program deployed on a chain. This experiment implements its contracts in Solidity. | [ethereum.org](https://ethereum.org/developers/docs/smart-contracts/) · [docs.soliditylang.org](https://docs.soliditylang.org/en/v0.8.29/) |
| Deployment / constructor / payable | Deployment creates a contract address and runs the constructor once. A payable constructor can receive native tokens on deployment. | [docs.soliditylang.org](https://docs.soliditylang.org/en/v0.8.29/contracts.html) |
| Origin / destination | Lasna emits the Cron100 event and issues the request. Base Sepolia receives the callback and writes the record. | [dev.reactive.network](https://dev.reactive.network/origins-and-destinations) |
| BoundedCron / CronReceiver | BoundedCron subscribes, counts and stops on Lasna. CronReceiver records the source block and destination timestamp of each run on Base Sepolia. | [Contract source](src/BoundedCron.sol) |
| System contract / callback proxy | The Lasna system contract handles subscriptions and requests. The official Base Sepolia proxy delivers the callback. Both entry points check the authorized caller. | [dev.reactive.network](https://dev.reactive.network/reactive-contracts) · [dev.reactive.network](https://dev.reactive.network/origins-and-destinations#testnet-chains) |
| Block / block number / Cron100 | A block contains ordered chain records. Its number identifies its position. Lasna emits Cron100 every 100 blocks. Elapsed wall-clock time can vary. | [ethereum.org](https://ethereum.org/developers/docs/blocks/) · [dev.reactive.network](https://dev.reactive.network/reactive-contracts#cron) |
| Subscribe / unsubscribe | A subscription filters the origin chain, emitter and topics. The scheduler uses the same filters to unsubscribe when the attempt or balance rule applies. | [dev.reactive.network](https://dev.reactive.network/reactive-contracts) · [Contract source](src/BoundedCron.sol) |
| LogRecord / react | The system passes matching events to react as LogRecord values. The scheduler reads LogRecord.blockNumber and checks the origin chain ID, emitter and topic. | [dev.reactive.network](https://dev.reactive.network/reactive-contracts) · [Contract source](src/BoundedCron.sol) |
| requestCallbackV_1_0 / callback | Supply the destination chain, receiver, gas limit and calldata. Here the payload contains the run number and source block. | [dev.reactive.network](https://dev.reactive.network/economy) · [Contract source](src/BoundedCron.sol) |
| arm / stop | The deployer calls arm to bind the receiver and start the subscription. Use stop to end early or retry a failed unsubscribe. | [Contract source](src/BoundedCron.sol) |
| attempts / stopped / subscribed | Read these fields to see attempts consumed, whether requests have stopped and whether the subscription remains. A normal finish reads 2, true, false. | [Contract source](src/BoundedCron.sol) · [Recorded exercise](../../assignments/d5-cron100.en.md) |
| Deduplication / idempotence | The scheduler requests at most once per source block. A duplicate callback for one run preserves the first destination record. | [Contract tests](test/BoundedCron.t.sol) |
| record / executedAt / block.timestamp | After checking its caller, record saves the Base Sepolia block’s Unix timestamp in seconds. Query executedAt for the first recorded time for a run. | [docs.soliditylang.org](https://docs.soliditylang.org/en/v0.8.29/units-and-global-variables.html#block-and-transaction-properties) · [Contract source](src/BoundedCron.sol) |

## 4. Transaction evidence and verification

| Term | Meaning in this experiment | Sources and further reading |
| --- | --- | --- |
| Transaction / transaction hash | A transaction is an operation submitted to a chain. Its hash identifies it. The Lasna request and Base Sepolia execution have separate hashes. | [ethereum.org](https://ethereum.org/developers/docs/transactions/) |
| Receipt / Success | The receipt contains execution status, gas and logs. Verify both success on the destination chain and the expected receiver event. | [eips.ethereum.org](https://eips.ethereum.org/EIPS/eip-1474#eth_gettransactionreceipt) |
| Event / log / topic | Events are structured receipt logs. For these non-anonymous events, topic 0 is the Keccak-256 event-signature hash. In CronRecorded, topics 1 and 2 index the run and source block. | [docs.soliditylang.org](https://docs.soliditylang.org/en/v0.8.29/abi-spec.html#events) |
| CallbackRequested / CallbackRequestFailed | The Lasna scheduler emits these after request submission or a failed call, respectively. Both consume an attempt. | [Contract source](src/BoundedCron.sol) |
| CronRecorded / CronStopped | CronRecorded confirms a destination run. CronStopped confirms Lasna unsubscribed. Match the run and source block across both chains. | [Contract source](src/BoundedCron.sol) · [Recorded exercise](../../assignments/d5-cron100.en.md) |
| Reactive Executions / Callbacks | Reactscan lists Lasna executions and destination callbacks in separate tabs. Use them to match transactions for each request. | [lasna.reactscan.net](https://lasna.reactscan.net/address/0x201E13106fDf34Fb8FEc9174D4e3DFd95b63CC2b?screen=reactive_executions) · [lasna.reactscan.net](https://lasna.reactscan.net/address/0x201E13106fDf34Fb8FEc9174D4e3DFd95b63CC2b?screen=callbacks) |

## 5. Browser development, tests and deployment

| Term | Meaning in this experiment | Sources and further reading |
| --- | --- | --- |
| Repository / fork / branch / commit | A repository stores file history. A fork is a copy in your account. A branch isolates an experiment and a commit records a traceable change. | [GitHub source](https://docs.github.com/en/get-started/learning-about-github/github-glossary) |
| github.dev | GitHub's browser editor. Open it by pressing the period key on a repository page to edit and commit files. | [GitHub source](https://docs.github.com/en/codespaces/the-githubdev-web-based-editor) |
| GitHub Actions / workflow / runner | Actions executes YAML workflows. A hosted runner installs tools, runs tests and prepares the experiment’s Remix source. | [GitHub source](https://docs.github.com/en/actions/get-started/understand-github-actions) · [cron100.yml](../../.github/workflows/cron100.yml) |
| workflow_dispatch / Run workflow / Summary | workflow_dispatch enables manual runs. Select the branch, start it and open Summary to find the run status and copy-ready Remix material. | [GitHub source](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow) |
| Foundry / Forge / unit test | Foundry provides contract tools. Forge runs six tests in Actions covering repeats, retries, permissions and the two-attempt cap. | [getfoundry.sh](https://getfoundry.sh/forge/testing) · [Contract tests](test/BoundedCron.t.sol) |
| SDK / pinned dependency | An SDK supplies reusable interfaces and base contracts. The project pins a specific Reactive SDK commit so builds share the same dependency. | [GitHub source](https://github.com/Reactive-Network/reactive-lib-omni/tree/3ade0dcf1d27e67e5783ef807e73a1b9e0c0cce8) |
| Remix / Browser Extension / Add Contract | Remix is a browser Solidity IDE. Browser Extension connects the wallet. Add Contract loads the interface of an existing address. | [Contract tests](https://remix-ide.readthedocs.io/en/latest/run.html) |
| Solidity compiler / Cancun / optimizer runs | The compiler produces bytecode and ABI. The guide and Actions use Solidity 0.8.29, the Cancun EVM and 200 optimizer runs. | [docs.soliditylang.org](https://docs.soliditylang.org/en/v0.8.29/using-the-compiler.html) · [foundry.toml](foundry.toml) |
| ABI | A machine-readable contract interface. Remix uses the ABI to show constructor arguments, function buttons and return values. | [docs.soliditylang.org](https://docs.soliditylang.org/en/v0.8.29/abi-spec.html) |
| GitHub Copilot Chat | An optional assistant for reading code and tests on GitHub. Run the Actions tests to check contract changes. | [GitHub source](https://docs.github.com/en/copilot/how-tos/copilot-on-github/chat-with-copilot/chat-in-github) |
| Mermaid | GitHub renders these diagrams from text. The fee-flow diagram groups the two networks and tracks each native test token separately. | [GitHub source](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams) · [Experiment guide](README.en.md#how-test-funds-move) |
