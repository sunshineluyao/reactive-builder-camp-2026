# 场景小实验 · 两次 Cron100 回调后停止

选择 **A. 定时执行**。Lasna 上的 `BoundedCron` 订阅 `Cron100`，在两个新的 Cron 区块各请求一次回调。Base Sepolia 上的 `CronReceiver` 记录运行序号、源 Cron 区块号和 `block.timestamp`。

## 链上提交凭证

| 项目 | 凭证 |
| --- | --- |
| Lasna 定时合约 `BoundedCron` | 待部署 |
| Base Sepolia 接收合约 `CronReceiver` | 待部署 |
| 第 1 次触发 | 待核验 Lasna 请求交易及 Base Sepolia `CronRecorded(1, ...)` 交易 |
| 第 2 次触发 | 待核验 Lasna 请求交易及 Base Sepolia `CronRecorded(2, ...)` 交易 |

本地 Solidity 0.8.29 已编译，6 项 Foundry 测试通过。公开测试网凭证在部署并收到两次回调后更新。

## 如何防止无限执行或耗尽余额

Lasna 只处理新的 Cron 区块，同一区块的重复通知不增加次数。每次请求占用一个名额，请求失败也计入。第二次尝试后合约停止发出新请求，并用原订阅条件调用 `unsubscribe`。余额低于设定的底线时提前停止。若取消订阅失败，本地停止状态仍有效，管理员可调用 `stop()` 完成取消。

两条链的费用分别从预先划定的测试预算支付。每次回调的 gas 上限是 300,000。Base Sepolia 接收端校验官方回调代理和授权的 Lasna 合约，每个序号只写入一次，并用 `block.timestamp` 记录执行时间。

## 本地复现

从仓库根目录执行。依赖固定在 Reactive Omni 官方示例所用的版本。

```bash
cd experiments/cron100
git clone https://github.com/Reactive-Network/reactive-lib-omni.git lib/reactive-lib-omni
git -C lib/reactive-lib-omni checkout --detach 3ade0dcf1d27e67e5783ef807e73a1b9e0c0cce8
forge test --root . -vv
```

合约 [BoundedCron.sol](../experiments/cron100/src/BoundedCron.sol) · 测试 [BoundedCron.t.sol](../experiments/cron100/test/BoundedCron.t.sol)

## 测试网部署与核验

在 `experiments/cron100` 中，用已有测试币的 Foundry 测试账户依次部署两份合约。下面的金额是本实验使用的测试预算。Lasna 合约启动时至少要保留 0.1 lREACT。

```bash
export LASNA_RPC=https://lasna-rpc.rnk.dev/
export BASE_RPC=https://base-sepolia-rpc.publicnode.com
export TEST_ACCOUNT=cron100-testnet

test "$(cast chain-id --rpc-url "$LASNA_RPC")" = 5318007
test "$(cast chain-id --rpc-url "$BASE_RPC")" = 84532
forge create src/BoundedCron.sol:BoundedCron --root . --broadcast \
  --rpc-url "$LASNA_RPC" --account "$TEST_ACCOUNT" --value 0.6ether \
  --constructor-args 100000000000000000

# 将第一个部署回执中的地址填入 CRON_ADDR，然后部署接收合约。
forge create src/BoundedCron.sol:CronReceiver --root . --broadcast \
  --rpc-url "$BASE_RPC" --account "$TEST_ACCOUNT" --value 0.002ether \
  --constructor-args "$CRON_ADDR"

# 将第二个部署回执中的地址填入 RECEIVER_ADDR，然后启动。
cast send "$CRON_ADDR" 'arm(address)' "$RECEIVER_ADDR" \
  --rpc-url "$LASNA_RPC" --account "$TEST_ACCOUNT"
```

等待两次有效 Cron100。把 `LASNA_START_BLOCK` 和 `BASE_START_BLOCK` 分别设为启动和接收合约部署的区块号，读取事件及最终状态。

```bash
cast logs --rpc-url "$LASNA_RPC" --from-block "$LASNA_START_BLOCK" --to-block latest \
  --address "$CRON_ADDR" 'CallbackRequested(uint8,uint256)'
cast logs --rpc-url "$BASE_RPC" --from-block "$BASE_START_BLOCK" --to-block latest \
  --address "$RECEIVER_ADDR" 'CronRecorded(uint8,uint256,uint256)'
cast call "$CRON_ADDR" 'attempts()(uint8)' --rpc-url "$LASNA_RPC"
cast call "$CRON_ADDR" 'subscribed()(bool)' --rpc-url "$LASNA_RPC"
cast call "$RECEIVER_ADDR" 'executedAt(uint8)(uint256)' 1 --rpc-url "$BASE_RPC"
cast call "$RECEIVER_ADDR" 'executedAt(uint8)(uint256)' 2 --rpc-url "$BASE_RPC"
```

预期 `attempts()` 为 `2`，`subscribed()` 为 `false`，两个 `executedAt` 均为非零时间戳。核对两条 `CronRecorded` 各自的序号和源区块号，再从区块浏览器复制实际 Lasna 与 Base Sepolia 交易链接。

- [Cron100 与 Omni 订阅](https://dev.reactive.network/reactive-contracts#cron)
- [Base Sepolia 回调代理及链 ID](https://dev.reactive.network/origins-and-destinations#testnet-chains)
- [回调费用及交易链路查询](https://dev.reactive.network/economy#inspecting-callbacks)
- [Lasna 测试币 faucet](https://dev.reactive.network/reactive-mainnet#reactive-faucet)
- [Lasna 浏览器](https://lasna.reactscan.net/) · [Base Sepolia 浏览器](https://sepolia.basescan.org/)
