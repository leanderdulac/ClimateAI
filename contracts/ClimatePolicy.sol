// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title ClimatePolicy
 * @dev Simplified ERC-3525-like policy token. Coverage amount is stored as `value`.
 * Payouts can only be triggered by the designated oracle.
 */
contract ClimatePolicy is ERC721, Ownable {
    uint256 private _nextTokenId;

    mapping(uint256 => uint256) private _slots;
    mapping(uint256 => uint256) private _values;

    address public oracle;
    uint256 public totalCollateral;

    event PolicyMinted(address indexed to, uint256 indexed tokenId, uint256 slot, uint256 value);
    event PayoutTriggered(uint256 indexed tokenId, address indexed beneficiary, uint256 amount);
    event OracleUpdated(address indexed previousOracle, address indexed newOracle);
    event CollateralDeposited(uint256 amount);

    constructor(string memory name_, string memory symbol_) ERC721(name_, symbol_) {
        oracle = msg.sender;
    }

    function setOracle(address newOracle) external onlyOwner {
        require(newOracle != address(0), "Oracle cannot be zero");
        address previous = oracle;
        oracle = newOracle;
        emit OracleUpdated(previous, newOracle);
    }

    function mintPolicy(address to, uint256 slot, uint256 value) external onlyOwner returns (uint256) {
        require(to != address(0), "Recipient cannot be zero");
        require(value > 0, "Coverage must be positive");

        _nextTokenId += 1;
        uint256 newTokenId = _nextTokenId;

        _safeMint(to, newTokenId);
        _slots[newTokenId] = slot;
        _values[newTokenId] = value;
        totalCollateral += value;

        emit PolicyMinted(to, newTokenId, slot, value);
        return newTokenId;
    }

    function triggerPayout(uint256 tokenId, uint256 payoutAmount) external {
        require(msg.sender == oracle, "Only oracle can trigger payout");
        require(_policyExists(tokenId), "Policy does not exist");
        require(payoutAmount > 0, "Payout must be positive");
        require(payoutAmount <= _values[tokenId], "Payout exceeds coverage value");

        address beneficiary = ownerOf(tokenId);
        _values[tokenId] -= payoutAmount;
        totalCollateral -= payoutAmount;

        emit PayoutTriggered(tokenId, beneficiary, payoutAmount);
    }

    function slotOf(uint256 tokenId) external view returns (uint256) {
        require(_policyExists(tokenId), "Token does not exist");
        return _slots[tokenId];
    }

    function valueOf(uint256 tokenId) external view returns (uint256) {
        require(_policyExists(tokenId), "Token does not exist");
        return _values[tokenId];
    }

    function _policyExists(uint256 tokenId) internal view returns (bool) {
        return _ownerOf(tokenId) != address(0);
    }
}
