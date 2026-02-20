// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./ClimatePolicy.sol";

/**
 * @title RiskVault
 * @dev Implementation of a Tokenized Strategy Vault (ERC-4626) for Climate Risk.
 * Investors deposit assets (e.g., USDC) to provide collateral for Climate Policies.
 * In return, they receive vault shares representing their stake in the risk pool.
 */
contract RiskVault is ERC4626, Ownable {
    
    // Reference to the ClimatePolicy contract
    ClimatePolicy public climatePolicy;
    
    // Mapping of active collateral locked for policies
    uint256 public lockedCollateral;

    event PolicyCollateralized(uint256 indexed tokenId, uint256 amount);
    event PremiumReceived(uint256 amount);

    constructor(
        IERC20 asset_, 
        string memory name_, 
        string memory symbol_, 
        address climatePolicy_
    ) ERC4626(asset_) ERC20(name_, symbol_) {
        climatePolicy = ClimatePolicy(climatePolicy_);
    }

    /**
     * @dev Allows the owner (or the system) to allocate vault funds to a policy.
     * This increases the "totalAssets" from the perspective of the policy, 
     * but locks it from immediate withdrawal until the policy expires or is claimed.
     */
    function allocateCollateral(uint256 tokenId, uint256 amount) external onlyOwner {
        require(totalAssets() - lockedCollateral >= amount, "Insufficient unlocked liquidity");
        lockedCollateral += amount;
        emit PolicyCollateralized(tokenId, amount);
    }

    /**
     * @dev Releases locked collateral back to the pool.
     * Called when a policy expires without a claim.
     */
    function releaseCollateral(uint256 amount) external onlyOwner {
        require(lockedCollateral >= amount, "Amount exceeds locked collateral");
        lockedCollateral -= amount;
    }

    /**
     * @dev Deposits premiums into the vault, which increases the value of shares.
     */
    function depositPremium(uint256 amount) external {
        // In a real scenario, this would transfer tokens from a fee collector
        // For Phase 4, we assume tokens are already in the contract or sent herewith
        emit PremiumReceived(amount);
    }

    /**
     * @dev Override maxWithdraw to account for locked collateral.
     */
    function maxWithdraw(address owner) public view override returns (uint256) {
        uint256 ownerAssets = convertToAssets(balanceOf(owner));
        uint256 freeAssets = totalAssets() > lockedCollateral ? totalAssets() - lockedCollateral : 0;
        return ownerAssets < freeAssets ? ownerAssets : freeAssets;
    }

    /**
     * @dev Override maxRedeem to account for locked collateral.
     */
    function maxRedeem(address owner) public view override returns (uint256) {
        uint256 freeAssets = totalAssets() > lockedCollateral ? totalAssets() - lockedCollateral : 0;
        uint256 maxRedeemableShares = convertToShares(freeAssets);
        return balanceOf(owner) < maxRedeemableShares ? balanceOf(owner) : maxRedeemableShares;
    }
}
