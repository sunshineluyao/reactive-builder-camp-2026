// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.29;

import {AbstractReactive} from "https://github.com/Reactive-Network/reactive-lib-omni/blob/3ade0dcf1d27e67e5783ef807e73a1b9e0c0cce8/src/base/AbstractReactive.sol";

contract BoundedTransferMonitor is AbstractReactive {
    uint256 public constant SEPOLIA_CHAIN_ID = 11_155_111;
    uint256 public constant LASNA_CHAIN_ID = 5_318_007;
    uint256 public constant TRANSFER_TOPIC = uint256(keccak256("Transfer(address,address,uint256)"));

    address public immutable token;
    uint256 public immutable minimumAmount;
    uint64 public immutable maximumTransfers;

    uint64 public count;
    uint256 public lastOriginTxHash;
    bool public subscribed;

    error WrongChain();
    error InvalidConfiguration();

    event TransferCounted(uint256 indexed originTxHash, address indexed sender, address indexed recipient, uint256 amount, uint64 count);
    event MonitoringStopped(uint64 count);

    constructor(address token_, uint256 minimumAmount_, uint64 maximumTransfers_) payable {
        if (block.chainid != LASNA_CHAIN_ID) revert WrongChain();
        if (token_ == address(0) || minimumAmount_ == 0 || maximumTransfers_ == 0 || msg.value == 0) {
            revert InvalidConfiguration();
        }

        token = token_;
        minimumAmount = minimumAmount_;
        maximumTransfers = maximumTransfers_;
        SYSTEM.subscribe(SEPOLIA_CHAIN_ID, token_, TRANSFER_TOPIC, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
        subscribed = true;
    }

    function react(LogRecord calldata log_) external onlySystem {
        if (
            !subscribed || log_.opCode != 3 || log_.chainId != SEPOLIA_CHAIN_ID
                || log_.contractAddress != token || log_.topic0 != TRANSFER_TOPIC || log_.data.length != 32
        ) return;

        uint256 amount = abi.decode(log_.data, (uint256));
        if (amount < minimumAmount) return;

        uint64 total = ++count;
        lastOriginTxHash = log_.txHash;
        emit TransferCounted(log_.txHash, address(uint160(log_.topic1)), address(uint160(log_.topic2)), amount, total);

        if (total == maximumTransfers) {
            subscribed = false;
            SYSTEM.unsubscribe(SEPOLIA_CHAIN_ID, token, TRANSFER_TOPIC, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
            emit MonitoringStopped(total);
        }
    }
}
