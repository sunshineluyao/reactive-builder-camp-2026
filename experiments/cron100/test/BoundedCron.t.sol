// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.29;

import {BASE_SEPOLIA_CHAIN_ID, LASNA_CHAIN_ID, BoundedCron, CronReceiver} from "../src/BoundedCron.sol";
import {IReactive} from "@reactive/src/interfaces/IReactive.sol";
import {ISystemContract} from "@reactive/src/interfaces/ISystemContract.sol";

interface Vm {
    function chainId(uint256) external;
    function deal(address, uint256) external;
    function etch(address, bytes calldata) external;
    function expectRevert() external;
    function prank(address) external;
    function warp(uint256) external;
}

contract MockSystem {
    bytes32 public subscription;
    uint256 public requests;
    bool public rejectRequest;
    bool public rejectCancellation;
    mapping(uint256 => bytes) public payloads;

    function setFailures(bool requestFailure, bool cancellationFailure) external {
        rejectRequest = requestFailure;
        rejectCancellation = cancellationFailure;
    }

    function subscribe(uint256 chain, address emitter, uint256 t0, uint256 t1, uint256 t2, uint256 t3) external {
        require(subscription == bytes32(0), "already subscribed");
        subscription = keccak256(abi.encode(chain, emitter, t0, t1, t2, t3));
    }

    function unsubscribe(uint256 chain, address emitter, uint256 t0, uint256 t1, uint256 t2, uint256 t3) external {
        require(!rejectCancellation, "mock cancellation failure");
        require(subscription == keccak256(abi.encode(chain, emitter, t0, t1, t2, t3)), "filter changed");
        subscription = bytes32(0);
    }

    function requestCallbackV_1_0(ISystemContract.CallbackConfiguration_V_1_0 calldata config) external {
        require(!rejectRequest, "mock request failure");
        require(config.chainId == BASE_SEPOLIA_CHAIN_ID, "incorrect destination chain");
        require(config.recipient != address(0) && config.gasLimit == 300_000, "incorrect callback limits");
        payloads[++requests] = config.payload;
    }
}

contract BoundedCronTest {
    Vm private constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address private constant SYSTEM = 0x8888888888888888888888888888888888888888;
    uint256 private constant MINIMUM_RESERVE = 0.1 ether;

    MockSystem private system;
    BoundedCron private cron;
    CronReceiver private receiver;

    function setUp() public {
        vm.chainId(LASNA_CHAIN_ID);
        system = MockSystem(SYSTEM);
        vm.etch(SYSTEM, address(new MockSystem()).code);
        cron = new BoundedCron(MINIMUM_RESERVE);
        vm.deal(address(cron), 1 ether);

        vm.chainId(BASE_SEPOLIA_CHAIN_ID);
        receiver = new CronReceiver(address(cron));
        vm.chainId(LASNA_CHAIN_ID);
        cron.arm(address(receiver));
    }

    function testTwoDistinctTicksRecordTimestampsAndStop() public {
        _tick(100);
        _tick(200);
        _tick(300);
        require(cron.attempts() == 2 && system.requests() == 2, "only two requests");
        require(cron.stopped() && !cron.subscribed() && system.subscription() == 0, "subscription removed");
        require(
            keccak256(system.payloads(1)) == keccak256(abi.encodeCall(CronReceiver.record, (address(0), 1, 100))),
            "first payload"
        );
        require(
            keccak256(system.payloads(2)) == keccak256(abi.encodeCall(CronReceiver.record, (address(0), 2, 200))),
            "second payload"
        );
        vm.expectRevert();
        cron.arm(address(receiver));

        _deliver(1, 100, 1_000);
        _deliver(2, 200, 1_112);
        _deliver(1, 100, 1_300);
        require(receiver.executedAt(1) == 1_000 && receiver.executedAt(2) == 1_112, "original timestamps");
    }

    function testDuplicateAndUnrelatedTicksDoNotConsumeAttempts() public {
        _tick(100);
        _tick(100);
        IReactive.LogRecord memory log = _log(200);
        log.contractAddress = address(1);
        vm.prank(SYSTEM);
        cron.react(log);
        require(cron.attempts() == 1 && system.requests() == 1, "only the first matching tick");
    }

    function testLowReserveStopsWithoutRequestingCallback() public {
        vm.deal(address(cron), MINIMUM_RESERVE - 1);
        _tick(100);
        require(cron.stopped() && !cron.subscribed() && system.subscription() == 0, "low balance stopped");
        require(cron.attempts() == 0 && system.requests() == 0, "no callback on low balance");
    }

    function testRejectedRequestsCountTowardLimit() public {
        system.setFailures(true, false);
        _tick(100);
        _tick(200);
        _tick(300);
        require(cron.attempts() == 2 && system.requests() == 0, "two failed attempts");
        require(cron.stopped() && !cron.subscribed(), "failures stopped");
    }

    function testOwnerCanRetryFailedCancellation() public {
        system.setFailures(false, true);
        _tick(100);
        _tick(200);
        _tick(300);
        require(cron.stopped() && cron.subscribed() && system.requests() == 2, "local stop persists");

        system.setFailures(false, false);
        cron.stop();
        require(!cron.subscribed() && system.subscription() == 0, "cancellation retry succeeded");
    }

    function testOnlySystemCanSendTicksAndOnlyProxyCanRecordForCron() public {
        IReactive.LogRecord memory log = _log(100);
        vm.expectRevert();
        cron.react(log);

        vm.chainId(BASE_SEPOLIA_CHAIN_ID);
        address proxy = receiver.BASE_SEPOLIA_PROXY();
        vm.expectRevert();
        receiver.record(address(cron), 1, 100);
        vm.expectRevert();
        vm.prank(proxy);
        receiver.record(address(1), 1, 100);
        vm.expectRevert();
        vm.prank(proxy);
        receiver.record(address(cron), 3, 300);
    }

    function _tick(uint256 cronBlock) private {
        IReactive.LogRecord memory log = _log(cronBlock);
        vm.prank(SYSTEM);
        cron.react(log);
    }

    function _log(uint256 cronBlock) private view returns (IReactive.LogRecord memory log) {
        log.chainId = LASNA_CHAIN_ID;
        log.contractAddress = cron.CRON_EMITTER();
        log.topic0 = cron.CRON_TOPIC();
        log.blockNumber = cronBlock;
        log.data = "";
    }

    function _deliver(uint8 attempt, uint256 cronBlock, uint256 timestamp) private {
        vm.chainId(BASE_SEPOLIA_CHAIN_ID);
        vm.warp(timestamp);
        address proxy = receiver.BASE_SEPOLIA_PROXY();
        vm.prank(proxy);
        receiver.record(address(cron), attempt, cronBlock);
    }
}
