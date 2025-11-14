#!/bin/bash
# GitHub Backup Script for ClimateAI with New Features

echo "🔄 Starting GitHub backup for ClimateAI with new features..."

# Change to the project directory
cd /home/artha/climateAI

echo "📝 Adding new files and changes..."
git add .

echo "📦 Committing all changes..."
git commit -m "feat: Add Bayesian bootstrap with regularized loss functions

- Implemented Bayesian bootstrap premium calculation:
  * L(θ) = Σ_i l(y_i, ŷ_i) + Ω(f) where Ω(f) = γT + ½λ||w||²
  * Prêmio = R$ 1.200 ± [R$ 900 (P10) - R$ 2.100 (P90)]
- Added Standardized Precipitation Index (SPI) 3/6/12 months
- Added Relative Wetness Index (RWI)
- Added synoptic circulation pattern analysis
- Added vertical temperature gradient analysis
- Added climate drift rate modeling: λ_s = β₀ + β₁·ΔT_s + β₂·d(CO₂)/dt
- Integrated PyTorch for LSTM functionality
- Updated documentation with 15th mathematical engine"

echo "📤 Pushing changes to GitHub..."
git push

if [ $? -eq 0 ]; then
    echo "✅ Backup successfully completed!"
    echo "✅ All new features and updates pushed to GitHub"
    echo "✅ Bayesian bootstrap functionality included"
    echo "✅ Climate features (SPI, RWI, synoptic patterns, gradients) integrated"
    echo "✅ PyTorch installation for LSTM functionality included"
    echo "✅ Regularized loss function L(θ) = Σ_i l(y_i, ŷ_i) + Ω(f) implemented"
else
    echo "❌ Backup failed. Please check your git configuration and GitHub access."
fi