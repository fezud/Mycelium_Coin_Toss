// SPDX-License-Identifier: MIT
pragma solidity 0.8.0;

import "@chainlink/contracts/src/v0.8/VRFConsumerBase.sol";
import "./Pool.sol";

contract CoinToss is VRFConsumerBase {
    uint256 internal fee;
    uint8 public result;
    address payable current_player;
    bytes32 keyhash;
    Pool pool;
    address owner;
    uint8 guess_value;
    uint256 bid;
    uint256 prize;
    bool pool_is_set = false;

    enum STATE {
        DEPLOYED,
        OPEN,
        CLOSED
    }

    STATE public state;

    event RequestedRandomness(bytes32 requestId);
    event CalculatedResult(uint8 result);
    event Won(address winner, uint256 prize);
    event Result(uint8 guess_value, uint8 result, uint256 bid, address player, uint256 timestamp);

    constructor(
        address _vrfCoordinator,
        address _link,
        uint256 _fee,
        bytes32 _keyhash
    ) VRFConsumerBase(_vrfCoordinator, _link) {
        fee = _fee;
        keyhash = _keyhash;
        owner = msg.sender;

        state = STATE.DEPLOYED;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    function setPool(address payable _pool) public onlyOwner {
        pool = Pool(_pool);
        state = STATE.OPEN;
    }

    function maximumBid() internal view returns (uint256) {
        return address(pool).balance / 50;
    }

    function flip(uint8 _guess_value) external payable {
        require(state == STATE.OPEN);
        require(current_player == address(0));

        require(
            _guess_value == 0 || _guess_value == 1,
            "Wrong format of guess value"
        );
        guess_value = _guess_value;

        require(msg.value <= maximumBid(), "Your bid is too big");
        bid = msg.value;
        prize = bid * 2;

        state = STATE.CLOSED;
        current_player = payable(msg.sender);

        payable(address(pool)).transfer(bid);
        
        bytes32 requestId = requestRandomness(keyhash, fee);
        emit RequestedRandomness(requestId);
    }

    function fulfillRandomness(bytes32 _requestId, uint256 _randomness)
        internal
        override
    {
        require(state == STATE.CLOSED);
        require(current_player != address(0));
        require(_randomness > 0);

        result = uint8(_randomness % 2);
        emit Result(result, guess_value, bid, current_player, block.timestamp);
    }

    function receivePrize() external {

        require(state == STATE.CLOSED);
        require(current_player == msg.sender, "You haven't played");
        require(result == guess_value, "You've lost");

        address payable _current_player = current_player;
        uint256 _prize = prize;

        bid = 0;
        prize = 0;
        current_player = payable(address(0));
        state = STATE.OPEN;


        emit Won(_current_player, _prize);
        pool.payWinner(_current_player, _prize);
    }
}
