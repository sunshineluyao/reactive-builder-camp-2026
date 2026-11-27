// SPDX-License-Identifier: MIT
pragma solidity 0.8.29;

/// Public ABI of Reactive Omni's subscription and versioned callback endpoint.
interface IOmni {
    struct Request { uint256 chainId; address recipient; uint64 gasLimit; bytes payload; }
    function subscribe(uint256, address, uint256, uint256, uint256, uint256) external;
    function unsubscribe(uint256, address, uint256, uint256, uint256, uint256) external;
    function requestCallbackV_1_0(Request calldata request) external;
}

interface IDebt { function debt(address payer) external view returns (uint256); }

/// Both the Lasna service and the destination proxy settle fees against the funded contract.
abstract contract ServiceFees {
    address payable public immutable service;
    uint256 public immutable maxFeePerPayment;
    uint256 public immutable lifetimeFeeCap;
    uint256 public remainingFeeBudget;
    error WrongService();
    error PaymentFailed();
    error BadAddress();
    error FeeTooLarge();
    error FeeBudgetExceeded();
    error InsufficientFeeBalance();
    error ExcessFunding();
    constructor(address provider, uint256 perPayment, uint256 lifetime) payable {
        if (provider == address(0)) revert BadAddress();
        if (msg.value > lifetime) revert ExcessFunding();
        service = payable(provider);
        maxFeePerPayment = perPayment;
        lifetimeFeeCap = lifetime;
        remainingFeeBudget = lifetime;
    }
    receive() external payable { checkFunding(); }
    function pay(uint256 amount) external {
        if (msg.sender != service) revert WrongService();
        sendFee(amount);
    }
    function coverDebt() external payable {
        if (msg.value != 0) checkFunding();
        sendFee(IDebt(service).debt(address(this)));
    }
    function checkFunding() private view {
        if (address(this).balance > remainingFeeBudget) revert ExcessFunding();
    }
    function sendFee(uint256 amount) private {
        if (amount == 0) return;
        if (amount > maxFeePerPayment) revert FeeTooLarge();
        if (amount > remainingFeeBudget) revert FeeBudgetExceeded();
        if (amount > address(this).balance) revert InsufficientFeeBalance();
        // Charge before settlement. A failed transfer also rolls back this debit.
        remainingFeeBudget -= amount;
        (bool sent,) = service.call{value: amount}("");
        if (!sent) revert PaymentFailed();
    }
    function requireFeeReserve() internal view {
        if (remainingFeeBudget == 0) revert FeeBudgetExceeded();
        if (address(this).balance == 0) revert InsufficientFeeBalance();
    }
}

/// Controlled source of deliberately simulated USDC/USDT quotes, denominated in 1/10000.
contract QuoteSource {
    address public immutable publisher = msg.sender;
    event PriceObserved(uint256 priceBps, uint256 observedAt);
    error NotPublisher();
    error BadQuote();
    function publish(uint256 priceBps) external {
        if (msg.sender != publisher) revert NotPublisher();
        if (priceBps == 0 || priceBps > 20_000) revert BadQuote();
        emit PriceObserved(priceBps, block.timestamp);
    }
}

contract ReactiveAlert is ServiceFees {
    struct LogRecord {
        uint256 chainId; address contractAddress;
        uint256 topic0; uint256 topic1; uint256 topic2; uint256 topic3;
        bytes data; uint256 blockNumber; uint256 opCode; uint256 blockHash;
        uint256 txHash; uint256 logIndex;
    }
    address public constant SYSTEM = 0x8888888888888888888888888888888888888888;
    uint256 public constant ORIGIN_CHAIN = 11155111;
    uint256 public constant DEST_CHAIN = 84532;
    uint256 private constant WILDCARD = 0xa65f96fc951c35ead38878e0f0b7a3c744a6f5ccc1476b313353ce31712313ad;
    uint256 private constant QUOTE_TOPIC = uint256(keccak256("PriceObserved(uint256,uint256)"));
    uint256 public constant MAX_REQUESTS = 20;
    address public immutable owner = msg.sender;
    address public immutable origin;
    address public destination;
    uint256 public sent;
    mapping(bytes32 => bool) public routed;
    event DestinationBound(address indexed destination);
    event QuoteRouted(bytes32 indexed evidenceId, bytes32 indexed originTx, uint256 logIndex, uint256 priceBps, uint256 observedAt);
    error NotOwner();
    error AlreadyBound();
    // Native units on Lasna are lREACT (18 decimals).
    constructor(address source) payable ServiceFees(SYSTEM, 0.05 ether, 0.30 ether) {
        if (source == address(0)) revert BadAddress();
        origin = source;
        IOmni(SYSTEM).subscribe(ORIGIN_CHAIN, source, QUOTE_TOPIC, WILDCARD, WILDCARD, WILDCARD);
    }
    function bindDestination(address receiver) external {
        if (msg.sender != owner) revert NotOwner();
        if (destination != address(0)) revert AlreadyBound();
        if (receiver == address(0)) revert BadAddress();
        destination = receiver;
        emit DestinationBound(receiver);
    }
    function react(LogRecord calldata item) external {
        if (msg.sender != SYSTEM) revert WrongService();
        if (item.chainId != ORIGIN_CHAIN || item.contractAddress != origin || item.topic0 != QUOTE_TOPIC) return;
        if (destination == address(0) || sent >= MAX_REQUESTS || item.data.length != 64 || item.txHash == 0) return;
        (uint256 price, uint256 observedAt) = abi.decode(item.data, (uint256, uint256));
        if (price == 0 || price > 20_000 || observedAt == 0 || (price >= 9950 && price <= 10050)) return;
        bytes32 sourceHash = bytes32(item.txHash);
        bytes32 id = keccak256(abi.encode(ORIGIN_CHAIN, sourceHash, item.logIndex));
        if (routed[id]) return;
        requireFeeReserve();
        routed[id] = true;
        ++sent;
        bytes memory payload = abi.encodeCall(AlertSink.record, (address(0), ORIGIN_CHAIN, sourceHash, item.logIndex, price, observedAt));
        IOmni(SYSTEM).requestCallbackV_1_0(IOmni.Request(DEST_CHAIN, destination, 400_000, payload));
        emit QuoteRouted(id, sourceHash, item.logIndex, price, observedAt);
        if (sent == MAX_REQUESTS) {
            IOmni(SYSTEM).unsubscribe(ORIGIN_CHAIN, origin, QUOTE_TOPIC, WILDCARD, WILDCARD, WILDCARD);
        }
    }
}

contract AlertSink is ServiceFees {
    address public immutable reactive;
    uint256 public alertCount;
    mapping(bytes32 => bool) public recorded;
    event PriceDeviation(bytes32 indexed evidenceId, bytes32 indexed originTx, uint256 logIndex, uint256 priceBps, uint256 observedAt);
    error WrongSender();
    error WrongOrigin();
    constructor(address proxy, address authorizedReactive) payable ServiceFees(proxy, 0.00025 ether, 0.002 ether) {
        if (authorizedReactive == address(0)) revert BadAddress();
        reactive = authorizedReactive;
    }
    function record(address sender, uint256 sourceChain, bytes32 originTx, uint256 logIndex, uint256 price, uint256 observedAt) external {
        if (msg.sender != service) revert WrongService();
        if (sender != reactive) revert WrongSender();
        if (sourceChain != 11155111 || originTx == bytes32(0) || observedAt == 0 || price == 0 ||
            price > 20_000 || (price >= 9950 && price <= 10050)) revert WrongOrigin();
        bytes32 id = keccak256(abi.encode(sourceChain, originTx, logIndex));
        if (recorded[id]) return;
        requireFeeReserve();
        recorded[id] = true;
        ++alertCount;
        emit PriceDeviation(id, originTx, logIndex, price, observedAt);
    }
}
