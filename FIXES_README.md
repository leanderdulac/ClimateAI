# CI/CD Pipeline Fix Documentation

## Issue Summary
The CI/CD pipeline was failing on the main branch (commit cb9532ae) due to missing dependencies required by new functionality added to the ClimateAI system.

## Root Cause Analysis
1. Recent commit added Bayesian Bootstrap functionality with regularized loss functions
2. New LSTM Attention service requires PyTorch for climate time series prediction
3. Production Docker image was using minimal requirements without PyTorch
4. Missing python-json-logger dependency for structured logging system

## Changes Made

### 1. Created Production ML Requirements File
- Added `requirements-prod-ml.txt` with essential ML libraries (PyTorch) but excluding heavy TensorFlow
- PyTorch required for LSTM attention mechanisms in climate prediction
- Size: ~700MB (vs ~200MB base, ~1200MB with TensorFlow)

### 2. Updated Dockerfile
- Modified production stage to use `requirements-prod-ml.txt` instead of `requirements-base.txt`
- Now includes PyTorch and other essential ML dependencies for production

### 3. Updated GitHub Actions Workflow
- Changed dependency installation step to use `requirements-prod-ml.txt`
- Ensures CI/CD tests match production build requirements

### 4. Updated Main Requirements
- Added PyTorch and python-json-logger to `requirements.txt`
- Updated documentation to reflect new production requirements

### 5. Added Missing Logging Dependency
- Added `python-json-logger==2.0.7` for structured JSON logging system
- Required by `api/logging.py` module

## Files Modified
- `/server/Dockerfile` - Updated to use production ML requirements
- `/server/requirements-prod-ml.txt` - New file with production ML dependencies  
- `/server/requirements.txt` - Added PyTorch and python-json-logger
- `/.github/workflows/ci-cd.yml` - Updated dependency installation
- Added import for `sinistrality_predictor` in main.py (from recent commit)

## Impact
- ✅ CI/CD pipeline should now pass
- ✅ Production Docker image includes all required dependencies
- ✅ Bayesian Bootstrap and LSTM Attention functionality operational
- 📈 Image size increased from ~200MB to ~700MB (reasonable for ML functionality)

## Verification Steps
To verify the fix:
1. Run: `docker build -t climateai-backend:test .` in /server directory
2. Check that all imports work: `python -c "from main import app"`
3. Verify Bayesian Bootstrap endpoints: `curl http://localhost:8000/api/v1/bayesian-bootstrap/health`

## Future Considerations
- Consider multi-stage builds to further optimize image size
- Monitor build times with additional ML dependencies
- Evaluate if specific PyTorch CPU-only version can reduce image size