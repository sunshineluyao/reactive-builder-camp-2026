// SPDX-License-Identifier: MIT
pragma solidity 0.8.29;

import {IOmni, ServiceFees, QuoteSource, ReactiveAlert, AlertSink} from "../contracts/StablecoinAlerts.sol";
import {LocalOmni, LocalProxy} from "./LocalTransport.sol";

interface Vm {
    function deal(address account, uint256 balance) external;
    function etch(address target, bytes calldata code) external;
    function prank(address sender) external;
    function expectRevert(bytes4 selector) external;
    function expectEmit(bool topic1, bool topic2, bool topic3, bool data, address emitter) external;
    function expectCall(address target, bytes calldata data) external;
    function expectCall(address target, bytes calldata data, uint64 count) external;
}

// Only the two network services are simulated. All alert and payment decisions run in the release contracts.
abstract contract FeeLedger {
    mapping(address => uint256) public debt;
    bool private rejectFees;

    function setDebt(address payer, uint256 amount) external { debt[payer] = amount; }
    function rejectPayments() external { rejectFees = true; }

    receive() external payable {
        require(!rejectFees, "service refused settlement");
        uint256 due = debt[msg.sender];
        if (due != 0) debt[msg.sender] = due > msg.value ? due - msg.value : 0;
    }
}

contract TestOmni is LocalOmni, FeeLedger {}
contract TestProxy is LocalProxy, FeeLedger {}

abstract contract GuardFixture {
    Vm internal constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address internal constant SYSTEM = 0x8888888888888888888888888888888888888888;
    address internal constant PROXY = 0x476F44b11F5C942c58f4c8E3d0300E5710743585;
    uint256 internal constant ORIGIN = 11155111;
    bytes32 internal constant TX_HASH = keccak256("signed test quote");
    uint256 internal constant OBSERVED_AT = 1_795_786_692;
    QuoteSource internal source;
    ReactiveAlert internal router;
    AlertSink internal sink;

    function setUp() public {
        vm.etch(SYSTEM, type(TestOmni).runtimeCode);
        vm.etch(PROXY, type(TestProxy).runtimeCode);
        vm.deal(address(this), 2 ether);
        source = new QuoteSource();
        router = new ReactiveAlert{value: 0.15 ether}(address(source));
        sink = new AlertSink{value: 0.001 ether}(PROXY, address(router));
        router.bindDestination(address(sink));
    }

    function quote(uint256 price, uint256 index) internal view returns (ReactiveAlert.LogRecord memory item) {
        item.chainId = ORIGIN;
        item.contractAddress = address(source);
        item.topic0 = uint256(keccak256("PriceObserved(uint256,uint256)"));
        item.data = abi.encode(price, OBSERVED_AT);
        item.txHash = uint256(TX_HASH);
        item.logIndex = index;
    }

    function eventId(uint256 index) internal pure returns (bytes32) {
        return keccak256(abi.encode(ORIGIN, TX_HASH, index));
    }

    function route(ReactiveAlert.LogRecord memory item) internal {
        vm.prank(SYSTEM);
        router.react(item);
    }

    function payload(uint256 index) internal pure returns (bytes memory) {
        return abi.encodeCall(AlertSink.record, (address(0), ORIGIN, TX_HASH, index, 9930, OBSERVED_AT));
    }

    function deliver(uint256 index) internal {
        TestProxy(payable(PROXY)).forward(address(router), address(sink), payload(index));
    }

    function charge(ServiceFees payer, uint256 amount) internal {
        address service = payer.service();
        vm.prank(service);
        payer.pay(amount);
    }

    function fund(ServiceFees payer, uint256 amount) internal {
        (bool success,) = payable(address(payer)).call{value: amount}("");
        require(success, "top-up failed");
    }
}

contract AlertGuardTest is GuardFixture {
    function testCrossingQueuesExpectedCallbackAndRecordsOneAlert() public {
        vm.expectEmit(false, false, false, true, address(source));
        emit QuoteSource.PriceObserved(9930, block.timestamp);
        source.publish(9930);

        IOmni.Request memory request = IOmni.Request(84532, address(sink), 400_000, payload(2));
        vm.expectCall(SYSTEM, abi.encodeCall(IOmni.requestCallbackV_1_0, (request)));
        route(quote(9930, 2));
        vm.expectEmit(true, true, false, true, address(sink));
        emit AlertSink.PriceDeviation(eventId(2), TX_HASH, 2, 9930, OBSERVED_AT);
        deliver(2);
        require(router.routed(eventId(2)) && sink.recorded(eventId(2)) && sink.alertCount() == 1);
    }

    function testControlAndBothBoundariesStayQuiet() public {
        route(quote(9990, 0));
        route(quote(9950, 1));
        route(quote(10050, 2));
        require(router.sent() == 0 && !router.routed(eventId(2)));
        route(quote(9949, 3));
        route(quote(10051, 4));
        require(router.sent() == 2);
    }

    function testWrongNetworkEmitterTopicAndMissingTxAreIgnored() public {
        ReactiveAlert.LogRecord memory item = quote(9930, 2);
        item.chainId = 1;
        route(item);
        item = quote(9930, 2);
        item.contractAddress = address(this);
        route(item);
        item = quote(9930, 2);
        item.topic0 = 0;
        route(item);
        item = quote(9930, 2);
        item.txHash = 0;
        route(item);
        require(router.sent() == 0 && !router.routed(eventId(2)));
    }

    function testOnlyPublisherSystemAndAuthorizedProxySenderCanAct() public {
        vm.expectRevert(QuoteSource.NotPublisher.selector);
        vm.prank(address(123));
        source.publish(9930);
        ReactiveAlert.LogRecord memory item = quote(9930, 2);
        vm.expectRevert(ServiceFees.WrongService.selector);
        router.react(item);
        vm.expectRevert(ServiceFees.WrongService.selector);
        sink.record(address(router), ORIGIN, TX_HASH, 2, 9930, OBSERVED_AT);
        bytes memory callData = payload(2);
        vm.expectRevert(AlertSink.WrongSender.selector);
        TestProxy(payable(PROXY)).forward(address(this), address(sink), callData);
        require(router.sent() == 0 && sink.alertCount() == 0);
    }

    function testDuplicateSourceAndCallbackAreHandledOncePerLog() public {
        IOmni.Request memory request = IOmni.Request(84532, address(sink), 400_000, payload(2));
        vm.expectCall(SYSTEM, abi.encodeCall(IOmni.requestCallbackV_1_0, (request)), 1);
        route(quote(9930, 2));
        route(quote(9930, 2));
        deliver(2);
        deliver(2);
        require(router.sent() == 1 && sink.alertCount() == 1);
        route(quote(9930, 3));
        deliver(3);
        require(router.sent() == 2 && sink.alertCount() == 2);
    }

    function testSinkRechecksChainAndThresholdAtDelivery() public {
        vm.prank(PROXY);
        vm.expectRevert(AlertSink.WrongOrigin.selector);
        sink.record(address(router), 1, TX_HASH, 2, 9930, OBSERVED_AT);
        vm.prank(PROXY);
        vm.expectRevert(AlertSink.WrongOrigin.selector);
        sink.record(address(router), ORIGIN, TX_HASH, 2, 9950, OBSERVED_AT);
        require(!sink.recorded(eventId(2)) && sink.alertCount() == 0);
    }

    function testTwentiethRequestUnsubscribesAndBlocksTheNext() public {
        for (uint256 i = 0; i < 20; ++i) route(quote(9930, i));
        (uint256 chain,,) = TestOmni(payable(SYSTEM)).subscribers(address(router));
        require(router.sent() == 20 && chain == 0);
        route(quote(9930, 20));
        require(router.sent() == 20 && !router.routed(eventId(20)));
    }

    function testEmptyRouterPausesAndTopUpResumesWithinBudget() public {
        for (uint256 i = 0; i < 3; ++i) charge(router, 0.05 ether);
        require(address(router).balance == 0 && router.remainingFeeBudget() == 0.15 ether);
        ReactiveAlert.LogRecord memory item = quote(9930, 2);
        vm.expectRevert(ServiceFees.InsufficientFeeBalance.selector);
        route(item);
        require(router.sent() == 0 && !router.routed(eventId(2)));
        fund(router, 0.01 ether);
        require(router.remainingFeeBudget() == 0.15 ether);
        route(item);
        require(router.routed(eventId(2)) && router.sent() == 1);
    }

    function testDestinationRevertKeepsSourceAndAllowsOneAuthorizedRedelivery() public {
        route(quote(9930, 2));
        for (uint256 i = 0; i < 4; ++i) charge(sink, 0.00025 ether);
        vm.expectRevert(ServiceFees.InsufficientFeeBalance.selector);
        deliver(2);
        require(router.routed(eventId(2)) && !sink.recorded(eventId(2)) && sink.alertCount() == 0);
        route(quote(9930, 2));
        require(router.sent() == 1);
        fund(sink, 0.0001 ether);
        deliver(2);
        deliver(2);
        require(sink.recorded(eventId(2)) && sink.alertCount() == 1);
    }
}

contract FeeBudgetTest is GuardFixture {
    function testPerPaymentLimitsAllowExactBoundaryOnBothNetworks() public {
        checkPerPayment(router, 0.05 ether, 0.30 ether);
        checkPerPayment(sink, 0.00025 ether, 0.002 ether);
    }

    function checkPerPayment(ServiceFees payer, uint256 single, uint256 lifetime) private {
        require(payer.maxFeePerPayment() == single && payer.lifetimeFeeCap() == lifetime);
        address service = payer.service();
        uint256 before = service.balance;
        vm.prank(service);
        vm.expectRevert(ServiceFees.FeeTooLarge.selector);
        payer.pay(single + 1);
        require(service.balance == before && payer.remainingFeeBudget() == lifetime);
        charge(payer, single);
        require(service.balance == before + single && payer.remainingFeeBudget() == lifetime - single);
    }

    function testLifetimeCapsStopPaymentsAndNewWorkEvenAfterTopUp() public {
        exhaustBudget(router);
        exhaustBudget(sink);
        ReactiveAlert.LogRecord memory item = quote(9930, 2);
        vm.expectRevert(ServiceFees.FeeBudgetExceeded.selector);
        route(item);
        vm.expectRevert(ServiceFees.FeeBudgetExceeded.selector);
        deliver(2);
        require(!router.routed(eventId(2)) && !sink.recorded(eventId(2)));
    }

    function exhaustBudget(ServiceFees payer) private {
        uint256 single = payer.maxFeePerPayment();
        fund(payer, payer.lifetimeFeeCap() - address(payer).balance);
        while (payer.remainingFeeBudget() > single) charge(payer, single);
        charge(payer, 1);
        address service = payer.service();
        vm.prank(service);
        vm.expectRevert(ServiceFees.FeeBudgetExceeded.selector);
        payer.pay(single);
        charge(payer, single - 1);
        (bool topUp,) = payable(address(payer)).call{value: single}("");
        require(!topUp && address(payer).balance == 0 && payer.remainingFeeBudget() == 0);
        // Exercise the ceiling independently of the funding check, even with a surplus.
        vm.deal(address(payer), single);
        vm.prank(service);
        vm.expectRevert(ServiceFees.FeeBudgetExceeded.selector);
        payer.pay(1);
        FeeLedger(payable(service)).setDebt(address(payer), 1);
        vm.expectRevert(ServiceFees.FeeBudgetExceeded.selector);
        payer.coverDebt();
    }

    function testOnlyServiceCanCollectAndDebtSettlementUsesTheSameBudget() public {
        FeeLedger service = FeeLedger(payable(PROXY));
        vm.expectRevert(ServiceFees.WrongService.selector);
        sink.pay(1);
        uint256 single = sink.maxFeePerPayment();
        service.setDebt(address(sink), single + 1);
        vm.expectRevert(ServiceFees.FeeTooLarge.selector);
        sink.coverDebt();
        require(sink.remainingFeeBudget() == sink.lifetimeFeeCap() && address(service).balance == 0);
        service.setDebt(address(sink), single);
        charge(sink, single / 2);
        sink.coverDebt();
        require(service.debt(address(sink)) == 0 && address(service).balance == single);
        require(sink.remainingFeeBudget() == sink.lifetimeFeeCap() - single);
        sink.coverDebt();
        require(address(service).balance == single);
    }

    function testRejectedSettlementPreservesBalanceAndBudget() public {
        FeeLedger service = FeeLedger(payable(SYSTEM));
        service.rejectPayments();
        uint256 original = address(router).balance;
        vm.prank(SYSTEM);
        vm.expectRevert(ServiceFees.PaymentFailed.selector);
        router.pay(1);
        require(address(router).balance == original && address(service).balance == 0);
        require(router.remainingFeeBudget() == router.lifetimeFeeCap());
    }

    function testTopUpSettlesOutstandingDebtAndResumesRouting() public {
        for (uint256 i = 0; i < 3; ++i) charge(router, 0.05 ether);
        FeeLedger service = FeeLedger(payable(SYSTEM));
        service.setDebt(address(router), 0.02 ether);
        vm.expectRevert(ServiceFees.InsufficientFeeBalance.selector);
        router.coverDebt();
        require(service.debt(address(router)) == 0.02 ether);
        router.coverDebt{value: 0.03 ether}();
        require(service.debt(address(router)) == 0 && address(router).balance == 0.01 ether);
        require(router.remainingFeeBudget() == 0.13 ether);
        route(quote(9930, 2));
        require(router.routed(eventId(2)) && router.sent() == 1);
    }

    function testTopUpsAndPayableDebtSettlementRejectExcessFunds() public {
        uint256 room = sink.lifetimeFeeCap() - address(sink).balance;
        (bool ok,) = payable(address(sink)).call{value: room + 1}("");
        require(!ok);
        vm.expectRevert(ServiceFees.ExcessFunding.selector);
        sink.coverDebt{value: room + 1}();
        fund(sink, room);
        require(address(sink).balance == sink.lifetimeFeeCap());
        require(sink.remainingFeeBudget() == sink.lifetimeFeeCap());
    }
}
