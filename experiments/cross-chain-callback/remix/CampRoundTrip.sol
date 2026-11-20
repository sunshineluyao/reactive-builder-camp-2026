// SPDX-License-Identifier: MIT
// Remix bundle of the ETHPanda × Reactive Network Builder Camp starter.
// Upstream: https://github.com/ethpanda-org/reactive-builder-camp/tree/87675f45bdaf7b944028bd6231e463f869b453c8/starter/src
// The contract bodies are unchanged. Imports are resolved at the SDK revision in starter/foundry.lock.

pragma solidity 0.8.29;

import { IReactive } from "https://github.com/Reactive-Network/reactive-lib-omni/blob/3ade0dcf1d27e67e5783ef807e73a1b9e0c0cce8/src/interfaces/IReactive.sol";
import { ISystemContract } from "https://github.com/Reactive-Network/reactive-lib-omni/blob/3ade0dcf1d27e67e5783ef807e73a1b9e0c0cce8/src/interfaces/ISystemContract.sol";
import { AbstractReactive } from "https://github.com/Reactive-Network/reactive-lib-omni/blob/3ade0dcf1d27e67e5783ef807e73a1b9e0c0cce8/src/base/AbstractReactive.sol";
import { IPayable } from "https://github.com/Reactive-Network/reactive-lib-omni/blob/3ade0dcf1d27e67e5783ef807e73a1b9e0c0cce8/src/interfaces/IPayable.sol";
import { AbstractCallback } from "https://github.com/Reactive-Network/reactive-lib-omni/blob/3ade0dcf1d27e67e5783ef807e73a1b9e0c0cce8/src/base/AbstractCallback.sol";

/// @title CampOrigin — 源链上的「事件发射器」（部署在 Sepolia 等源链）
/// @notice 三步走的第 1 步：在源链发出一个事件。真实项目里这一步通常是别人的合约
///         （ERC-20 Transfer、Uniswap Sync…），这里用一个最小合约方便自己触发。
contract CampOrigin {
    /// @dev topic0 = keccak256("Ping(address,uint256)")；who 是 indexed → topic1；value 在 data 里
    event Ping(address indexed who, uint256 value);

    function ping(uint256 value) external {
        emit Ping(msg.sender, value);
    }
}

/// @title CampReactive — 共学模板的 Reactive 侧合约（部署在 Lasna / Reactive 主网）
/// @notice 订阅「源链某合约的某个事件」，在 react() 里做判断，满足条件就请求目标链回调。
///         这是「事件 → react() → 回调」三步走里的第 2 步。
/// @dev    Omni 写法要点：
///         1. 通过 SYSTEM（0x8888…8888）订阅与请求回调；
///         2. react() 必须加 onlySystem；
///         3. 回调 payload 的第一个参数必须是 address 占位（address(0)），网络会替换成本合约地址。
contract CampReactive is AbstractReactive {
    error NotOwner();
    error ZeroAddress();

    /// @notice 每次收到匹配事件时发出，方便在 Reactscan 上看到 react() 真的被调用了
    event Seen(uint256 indexed originChainId, address indexed originContract, uint256 txHash, uint256 value);
    /// @notice 请求回调时发出
    event CallbackRequested(uint256 indexed destChainId, address indexed recipient, uint256 value);

    address public immutable OWNER;
    uint256 public immutable ORIGIN_CHAIN_ID;
    address public immutable ORIGIN_CONTRACT;
    uint256 public immutable ORIGIN_TOPIC_0;
    uint256 public immutable DEST_CHAIN_ID;
    uint64 public constant CALLBACK_GAS_LIMIT = 1_000_000;

    /// @notice 目标链上的回调合约（部署顺序：先部署本合约 → 再部署回调合约 → 回来 setRecipient）
    address public recipient;
    /// @notice 只有 data 里解码出的数值 >= threshold 才回调（「满足条件 Y」）
    uint256 public threshold;
    /// @notice 剩余可处理次数，归零后自动退订，防止测试币被不停扣光
    uint256 public remaining;

    uint256 public lastTxHash;
    uint256 public lastReactBlock;

    modifier onlyOwner() {
        if (msg.sender != OWNER) revert NotOwner();
        _;
    }

    /// @param originChainId_  源链 chainId，例如 Ethereum Sepolia 11155111
    /// @param originContract_ 源链上要监听的合约
    /// @param originTopic0_   事件签名 keccak256，例如 Ping(address,uint256)
    /// @param destChainId_    目标链 chainId（和回调合约所在链一致）
    /// @param threshold_      回调阈值
    /// @param limit_          最多处理多少次事件
    constructor(
        uint256 originChainId_,
        address originContract_,
        uint256 originTopic0_,
        uint256 destChainId_,
        uint256 threshold_,
        uint256 limit_
    ) payable {
        OWNER = msg.sender;
        ORIGIN_CHAIN_ID = originChainId_;
        ORIGIN_CONTRACT = originContract_;
        ORIGIN_TOPIC_0 = originTopic0_;
        DEST_CHAIN_ID = destChainId_;
        threshold = threshold_;
        remaining = limit_;

        SYSTEM.subscribe(originChainId_, originContract_, originTopic0_, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
    }

    function setRecipient(address recipient_) external onlyOwner {
        if (recipient_ == address(0)) revert ZeroAddress();
        recipient = recipient_;
    }

    function setThreshold(uint256 threshold_) external onlyOwner {
        threshold = threshold_;
    }

    /// @notice 充值 + 调整剩余次数（余额耗尽产生欠款后，合约会静默停止）
    function topUp(uint256 limit_) external payable onlyOwner {
        remaining = limit_;
    }

    /// @inheritdoc IReactive
    function react(LogRecord calldata log_) external onlySystem {
        // 多个订阅时先按 topic0 分流；这里只有一个订阅，做一次防御性检查即可
        if (log_.topic0 != ORIGIN_TOPIC_0) return;
        if (remaining == 0) return;

        // 示例事件：Ping(address indexed who, uint256 value) → topic1 = who，data = abi.encode(value)
        uint256 value = log_.data.length >= 32 ? abi.decode(log_.data, (uint256)) : 0;

        lastTxHash = log_.txHash;
        lastReactBlock = block.number;
        emit Seen(log_.chainId, log_.contractAddress, log_.txHash, value);

        // 注意：不要用 revert 过滤事件，revert 照样收费；用 return。
        if (value < threshold || recipient == address(0)) return;

        remaining -= 1;
        if (remaining == 0) {
            SYSTEM.unsubscribe(ORIGIN_CHAIN_ID, ORIGIN_CONTRACT, ORIGIN_TOPIC_0, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
        }

        // 第一个参数 address(0) 是占位符，Callback Proxy 会把它替换成本合约地址，供目标链鉴权
        bytes memory payload = abi.encodeWithSignature(
            "onEvent(address,uint256,uint256,uint256)", address(0), log_.chainId, log_.txHash, value
        );
        emit CallbackRequested(DEST_CHAIN_ID, recipient, value);
        SYSTEM.requestCallbackV_1_0(
            ISystemContract.CallbackConfiguration_V_1_0({
                chainId: DEST_CHAIN_ID,
                recipient: recipient,
                gasLimit: CALLBACK_GAS_LIMIT,
                payload: payload
            })
        );
    }
}

/// @title CampCallback — 共学模板的目标链回调合约（部署在 Sepolia / Base Sepolia / Unichain Sepolia）
/// @notice 只接受「本链 Callback Proxy」发来的、且 payload 里注入的 reactive 地址等于 _CALLBACK_SENDER 的调用。
///         这是三步走的第 3 步，也是黑客松评审的硬门槛：链上必须能看到这笔回调交易。
/// @dev    回调由接收方用目标链原生币付费（ETH），所以部署时要带 value；
///         _CALLBACK_SENDER 不可更改，填错只能重新部署。
contract CampCallback is AbstractCallback {
    /// @notice 回调到达时发出；拿这笔交易哈希去交黑客松
    event Handled(address indexed reactive, uint256 indexed originChainId, uint256 originTxHash, uint256 value, uint256 count);

    uint256 public count;
    uint256 public lastValue;
    uint256 public lastOriginTxHash;

    /// @param proxy_    本链的 Callback Proxy 地址（见 docs/cheatsheet.md）
    /// @param reactive_ 允许给本合约发回调的 Reactive 合约地址
    constructor(IPayable proxy_, address reactive_) payable AbstractCallback(proxy_, reactive_) {}

    /// @notice 被 Callback Proxy 调用的函数。第一个参数由网络注入，不是你在 payload 里填的 address(0)。
    function onEvent(address reactive_, uint256 originChainId_, uint256 originTxHash_, uint256 value_)
        external
        onlyServiceProvider
        onlyCallbackSender(reactive_)
    {
        count += 1;
        lastValue = value_;
        lastOriginTxHash = originTxHash_;
        emit Handled(reactive_, originChainId_, originTxHash_, value_, count);
    }
}
