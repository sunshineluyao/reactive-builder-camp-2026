// SPDX-License-Identifier: MIT
pragma solidity 0.8.29;

/// Test-only deterministic transport. Install these two harnesses on private Anvil nodes.
interface IQuoteObserver {
    struct Record {
        uint256 chainId;
        address contractAddress;
        uint256 topic0;
        uint256 topic1;
        uint256 topic2;
        uint256 topic3;
        bytes data;
        uint256 blockNumber;
        uint256 opCode;
        uint256 blockHash;
        uint256 txHash;
        uint256 logIndex;
    }
    function react(Record calldata logRecord) external;
}

contract LocalOmni {
    struct Request { uint256 chainId; address recipient; uint64 gasLimit; bytes payload; }
    struct Subscription { uint256 chainId; address origin; uint256 topic0; }
    mapping(address => Subscription) public subscribers;
    event LocalCallbackQueued(address indexed sender, uint256 indexed chain, address indexed recipient, bytes payload);

    function subscribe(uint256 chainId, address origin, uint256 topic0, uint256, uint256, uint256) external {
        subscribers[msg.sender] = Subscription(chainId, origin, topic0);
    }

    function unsubscribe(uint256, address, uint256, uint256, uint256, uint256) external {
        delete subscribers[msg.sender];
    }

    function deliver(address observer, IQuoteObserver.Record calldata record) external {
        Subscription memory sub = subscribers[observer];
        require(sub.chainId == record.chainId && sub.origin == record.contractAddress && sub.topic0 == record.topic0);
        IQuoteObserver(observer).react(record);
    }

    function requestCallbackV_1_0(Request calldata req) external {
        require(subscribers[msg.sender].chainId != 0);
        emit LocalCallbackQueued(msg.sender, req.chainId, req.recipient, req.payload);
    }
}

/// Emulates address injection by the destination proxy. The caller relays bytes emitted by LocalOmni.
contract LocalProxy {
    function forward(address sender, address recipient, bytes calldata payload) external {
        bytes memory data = payload;
        require(data.length >= 36);
        assembly ("memory-safe") { mstore(add(data, 36), sender) }
        (bool ok, bytes memory result) = recipient.call(data);
        if (!ok) assembly ("memory-safe") { revert(add(result, 32), mload(result)) }
    }
}
