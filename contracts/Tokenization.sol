// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract ClimateToken is ERC20 {
    address public admin;
    constructor(string memory name_, string memory symbol_) ERC20(name_, symbol_) {
        admin = msg.sender;
    }
    function mint(address to, uint256 amount) external {
        require(msg.sender == admin, "only admin can mint");
        require(to != address(0), "recipient cannot be zero");
        require(amount > 0, "amount must be positive");
        _mint(to, amount);
    }
}
