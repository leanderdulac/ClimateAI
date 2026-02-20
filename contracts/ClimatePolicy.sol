// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title ClimatePolicy
 * @dev Simplified ERC-3525 (Semi-Fungible Token) implementation for Climate Policies.
 * Each token represents a policy instance. 
 * Tokens in the same "Slot" represent the same risk type/region.
 * "Value" represents the coverage amount (Sum Insured) in Stablecoin.
 */
contract ClimatePolicy is ERC721, Ownable {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIds;

    // Mapping from token ID to its Slot
    mapping(uint256 => uint256) private _slots;
    // Mapping from token ID to its Value (Coverage Amount)
    mapping(uint256 => uint256) private _values;
    
    // Address of the Oracle allowed to trigger payouts
    address public oracle;
    
    // Counter for colateral (simulated Escrow)
    uint256 public totalCollateral;

    event PolicyMinted(address indexed to, uint256 indexed tokenId, uint256 slot, uint256 value);
    event PayoutTriggered(uint256 indexed tokenId, address indexed beneficiary, uint256 amount);
    event CollateralDeposited(uint256 amount);

    constructor(string memory name_, string memory symbol_) ERC721(name_, symbol_) {
        oracle = msg.sender;
    }

    function setOracle(address _oracle) external onlyOwner {
        oracle = _oracle;
    }

    /**
     * @dev Mint a new policy token. 
     * @param to Recipient address.
     * @param slot Categorization of the policy (e.g., Drought-Region-Hash).
     * @param value The coverage amount assigned to this policy.
     */
    function mintPolicy(address to, uint256 slot, uint256 value) external onlyOwner returns (uint256) {
        _tokenIds.increment();
        uint256 newTokenId = _tokenIds.current();

        _safeMint(to, newTokenId);
        _slots[newTokenId] = slot;
        _values[newTokenId] = value;
        totalCollateral += value;

        emit PolicyMinted(to, newTokenId, slot, value);
        return newTokenId;
    }

    /**
     * @dev Trigger payout for a specific policy. 
     * Only the designated Oracle can call this.
     */
    function triggerPayout(uint256 tokenId, uint256 payoutAmount) external {
        require(msg.sender == oracle || msg.sender == owner(), "Only Oracle or Owner can trigger payout");
        require(_exists(tokenId), "Policy does not exist");
        require(payoutAmount <= _values[tokenId], "Payout exceeds coverage value");

        address beneficiary = ownerOf(tokenId);
        
        // In a real implementation, we would transfer USDC/Stablecoin here
        // For Phase 3, we simulate the reduction of value and collateral
        _values[tokenId] -= payoutAmount;
        totalCollateral -= payoutAmount;

        emit PayoutTriggered(tokenId, beneficiary, payoutAmount);
    }

    // ERC-3525 like getters
    function slotOf(uint256 tokenId) external view returns (uint256) {
        require(_exists(tokenId), "Token does not exist");
        return _slots[tokenId];
    }

    function valueOf(uint256 tokenId) external view returns (uint256) {
        require(_exists(tokenId), "Token does not exist");
        return _values[tokenId];
    }
}
