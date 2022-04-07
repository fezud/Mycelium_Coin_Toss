// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Pool {
    address coin_toss;
    event Received(address, uint256);

    constructor(address _coin_toss) {
        coin_toss = _coin_toss;
    }

    modifier onlyCoinTossContract() {
        require(msg.sender == coin_toss);
        _;
    }

    function payWinner(address payable _winner, uint256 _prize)
        public
        onlyCoinTossContract
    {
        require(_prize <= address(this).balance);
        (bool sent, bytes memory data) = _winner.call{value: _prize}("");
        require(sent, "Transaction was not successfull");
    }

    fallback() external payable {}

    function getBalance() public view returns (uint256) {
        return address(this).balance;
    }
}
