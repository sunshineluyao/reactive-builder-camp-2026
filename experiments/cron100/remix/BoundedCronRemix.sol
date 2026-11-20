// Generated from src/BoundedCron.sol. Deploy with Remix on the designated testnets.
// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.29;

import {AbstractReactive} from "https://github.com/Reactive-Network/reactive-lib-omni/blob/3ade0dcf1d27e67e5783ef807e73a1b9e0c0cce8/src/base/AbstractReactive.sol";
import {AbstractCallback} from "https://github.com/Reactive-Network/reactive-lib-omni/blob/3ade0dcf1d27e67e5783ef807e73a1b9e0c0cce8/src/base/AbstractCallback.sol";
import {IPayable} from "https://github.com/Reactive-Network/reactive-lib-omni/blob/3ade0dcf1d27e67e5783ef807e73a1b9e0c0cce8/src/interfaces/IPayable.sol";
import {ISystemContract} from "https://github.com/Reactive-Network/reactive-lib-omni/blob/3ade0dcf1d27e67e5783ef807e73a1b9e0c0cce8/src/interfaces/ISystemContract.sol";

uint256 constant LASNA_CHAIN_ID = 5_318_007;
uint256 constant BASE_SEPOLIA_CHAIN_ID = 84_532;
uint8 constant MAX_ATTEMPTS = 2;

contract BoundedCron is AbstractReactive {
    address public constant CRON_EMITTER = 0x0000000000000000000000000000000000fffFfF;
    uint256 public constant CRON_TOPIC = 0xb49937fb8970e19fd46d48f7e3fb00d659deac0347f79cd7cb542f0fc1503c70;
    uint64 public constant CALLBACK_GAS_LIMIT = 300_000;

    address public immutable owner;
    uint256 public immutable minimumReserve;
    address public recipient;
    uint256 public lastCronBlock;
    uint8 public attempts;
    bool public stopped;
    bool public subscribed;

    error WrongChain();
    error InvalidConfiguration();
    error NotOwner();
    error CannotArm();
    error BelowMinimumReserve();

    event CronArmed(address indexed recipient);
    event CallbackRequested(uint8 indexed attempt, uint256 indexed cronBlock);
    event CallbackRequestFailed(uint8 indexed attempt, uint256 indexed cronBlock, bytes reason);
    event CronStopped(uint8 attempts);
    event CronUnsubscribeFailed(bytes reason);

    constructor(uint256 minimumReserve_) payable {
        if (block.chainid != LASNA_CHAIN_ID) revert WrongChain();
        if (minimumReserve_ == 0) revert InvalidConfiguration();
        owner = msg.sender;
        minimumReserve = minimumReserve_;
    }

    // Arm only once, after deploying and funding the destination receiver.
    function arm(address recipient_) external {
        if (msg.sender != owner) revert NotOwner();
        if (recipient != address(0) || stopped) revert CannotArm();
        if (recipient_ == address(0)) revert InvalidConfiguration();
        if (address(this).balance < minimumReserve) revert BelowMinimumReserve();

        recipient = recipient_;
        SYSTEM.subscribe(LASNA_CHAIN_ID, CRON_EMITTER, CRON_TOPIC, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE);
        subscribed = true;
        emit CronArmed(recipient_);
    }

    function react(LogRecord calldata log_) external onlySystem {
        if (!subscribed || stopped || attempts >= MAX_ATTEMPTS) return;
        if (log_.chainId != LASNA_CHAIN_ID || log_.contractAddress != CRON_EMITTER || log_.topic0 != CRON_TOPIC) {
            return;
        }

        // Lasna Cron100 logs can have empty data. The network supplies the source block in LogRecord.
        uint256 cronBlock = log_.blockNumber;
        if (cronBlock <= lastCronBlock) return;
        if (address(this).balance < minimumReserve) {
            _stop();
            return;
        }

        lastCronBlock = cronBlock;
        uint8 attempt = ++attempts;
        ISystemContract.CallbackConfiguration_V_1_0 memory config = ISystemContract.CallbackConfiguration_V_1_0({
            chainId: BASE_SEPOLIA_CHAIN_ID,
            recipient: recipient,
            gasLimit: CALLBACK_GAS_LIMIT,
            payload: abi.encodeCall(CronReceiver.record, (address(0), attempt, cronBlock))
        });

        // A reverted request still uses one attempt, so failures cannot reset the budget.
        try SYSTEM.requestCallbackV_1_0(config) {
            emit CallbackRequested(attempt, cronBlock);
        } catch (bytes memory reason) {
            emit CallbackRequestFailed(attempt, cronBlock, reason);
        }

        if (attempt == MAX_ATTEMPTS) _stop();
    }

    function stop() external {
        if (msg.sender != owner) revert NotOwner();
        _stop();
    }

    function _stop() private {
        stopped = true;
        if (!subscribed) return;

        try SYSTEM.unsubscribe(
            LASNA_CHAIN_ID, CRON_EMITTER, CRON_TOPIC, REACTIVE_IGNORE, REACTIVE_IGNORE, REACTIVE_IGNORE
        ) {
            subscribed = false;
            emit CronStopped(attempts);
        } catch (bytes memory reason) {
            // Keep the local stop in effect and let the owner retry cancellation.
            emit CronUnsubscribeFailed(reason);
        }
    }
}

contract CronReceiver is AbstractCallback {
    address public constant BASE_SEPOLIA_PROXY = 0x476F44b11F5C942c58f4c8E3d0300E5710743585;

    mapping(uint8 => uint256) public executedAt;

    error WrongChain();
    error InvalidSender();
    error InvalidAttempt();

    event CronRecorded(uint8 indexed attempt, uint256 indexed cronBlock, uint256 timestamp);

    constructor(address reactive_) payable AbstractCallback(IPayable(payable(BASE_SEPOLIA_PROXY)), reactive_) {
        if (block.chainid != BASE_SEPOLIA_CHAIN_ID) revert WrongChain();
        if (reactive_ == address(0)) revert InvalidSender();
    }

    function record(address reactive_, uint8 attempt, uint256 cronBlock)
        external
        onlyServiceProvider
        onlyCallbackSender(reactive_)
    {
        if (attempt == 0 || attempt > MAX_ATTEMPTS) revert InvalidAttempt();
        if (executedAt[attempt] != 0) return;

        uint256 timestamp = block.timestamp;
        executedAt[attempt] = timestamp;
        emit CronRecorded(attempt, cronBlock, timestamp);
    }
}
