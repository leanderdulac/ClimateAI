# 📚 Hathor Blockchain Integration Guide

## 🎯 Overview

This guide provides complete documentation for integrating ClimateWise with Hathor Network for climate index tokenization.

---

## 📁 Project Structure

```
server/
├── blockchain/
│   └── hathor/
│       ├── __init__.py
│       ├── config.py                    # Configuration settings
│       ├── hathor_service.py            # Core blockchain service
│       ├── climate_token_service.py     # Climate token management
│       ├── oracle_service.py            # Climate data oracle
│       └── tests/
│           └── test_hathor_integration.py
│
├── api/
│   └── hathor_blockchain.py             # REST API endpoints
│
└── requirements-blockchain.txt          # Python dependencies
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd server
pip install -r requirements-blockchain.txt
```

### 2. Configure Environment

Create `.env` file:

```bash
# Hathor Network Configuration
HATHOR_NETWORK=testnet
HATHOR_WALLET_SEED="your 24 word mnemonic seed here"
HATHOR_WALLET_ADDRESS=""

# Token Configuration
HATHOR_CLIMATE_TOKEN_SYMBOL=CLMT
HATHOR_CLIMATE_TOKEN_NAME="Climate Index Token"
HATHOR_CLIMATE_TOKEN_INITIAL_SUPPLY=1000000
```

### 3. Initialize Wallet

```python
from blockchain.hathor.hathor_service import get_hathor_service

hathor = get_hathor_service()

# Generate new wallet
address = hathor.initialize()
print(f"Wallet address: {address}")

# Or use existing seed
address = hathor.initialize(seed="your 24 word seed")
```

### 4. Create First Climate Token

```python
from blockchain.hathor.climate_token_service import get_climate_token_service
from blockchain.hathor.climate_token_service import ClimateTokenMetadata, ClimateIndexType

token_service = get_climate_token_service()

# Create metadata
metadata = ClimateTokenMetadata(
    index_type=ClimateIndexType.DROUGHT,
    region="São Paulo",
    latitude=-23.5505,
    longitude=-46.6333,
    start_date="2026-01-01",
    end_date="2026-03-31",
    trigger_value=100.0,  # 100mm precipitation
    trigger_condition="below",  # Payout if precipitation < 100mm
    payout_amount=10000,  # R$ 10,000 in smallest unit
    currency="BRL",
    oracle_source="INMET",
)

# Create token
token = token_service.create_climate_token(
    name="ClimateWise Drought Index SP 2026",
    symbol="CLMT-DROUGHT-SP-2026",
    total_supply=10000,
    metadata=metadata,
)

print(f"Token created: {token.token_uid}")
```

---

## 📖 API Reference

### Create Climate Token

**Endpoint**: `POST /api/v1/blockchain/hathor/tokens/create`

**Request**:
```json
{
  "name": "ClimateWise Drought Index SP 2026",
  "symbol": "CLMT-DROUGHT-SP-2026",
  "total_supply": 10000,
  "index_type": "drought",
  "region": "São Paulo",
  "latitude": -23.5505,
  "longitude": -46.6333,
  "start_date": "2026-01-01",
  "end_date": "2026-03-31",
  "trigger_value": 100.0,
  "trigger_condition": "below",
  "payout_amount": 10000,
  "currency": "BRL",
  "oracle_source": "INMET"
}
```

**Response**:
```json
{
  "success": true,
  "token_uid": "00a1b2c3d4e5f6...",
  "name": "ClimateWise Drought Index SP 2026",
  "symbol": "CLMT-DROUGHT-SP-2026",
  "total_supply": 10000,
  "tx_hash": "tx_hash_here",
  "explorer_url": "https://explorer.testnet.hathor.network/token/...",
  "message": "Climate token created successfully"
}
```

### Transfer Tokens

**Endpoint**: `POST /api/v1/blockchain/hathor/tokens/transfer`

**Request**:
```json
{
  "token_uid": "00a1b2c3d4e5f6...",
  "amount": 100,
  "destination_address": "wallet_address_here",
  "message": "Token transfer"
}
```

### Execute Payout

**Endpoint**: `POST /api/v1/blockchain/hathor/tokens/{token_uid}/payout`

**Request**:
```json
{
  "beneficiary_address": "wallet_address_here",
  "oracle_value": 85.5
}
```

**Process**:
1. Fetch oracle data (if not provided)
2. Check trigger condition (85.5 < 100.0 = TRUE)
3. Execute payout automatically
4. Update token status to PAID_OUT

### Get Climate Index

**Endpoint**: `POST /api/v1/blockchain/hathor/oracle/index`

**Request**:
```json
{
  "index_type": "precipitation",
  "latitude": -23.5505,
  "longitude": -46.6333,
  "start_date": "2026-01-01",
  "end_date": "2026-03-31",
  "trigger_value": 100.0,
  "trigger_condition": "below",
  "source": "openmeteo"
}
```

**Response**:
```json
{
  "index_type": "precipitation",
  "region": "-23.5505,-46.6333",
  "latitude": -23.5505,
  "longitude": -46.6333,
  "start_date": "2026-01-01",
  "end_date": "2026-03-31",
  "index_value": 85.5,
  "trigger_value": 100.0,
  "trigger_condition": "below",
  "trigger_met": true,
  "data_points_count": 90,
  "calculation_method": "precipitation_sum"
}
```

---

## 🔧 Services

### HathorService

Core blockchain operations:

```python
from blockchain.hathor.hathor_service import get_hathor_service

hathor = get_hathor_service()

# Initialize wallet
address = hathor.initialize(seed="your seed")

# Get balance
balance = hathor.get_balance(token_uid="00")  # HTR balance

# Create token
result = hathor.create_climate_token(
    name="My Token",
    symbol="MYTK",
    amount=10000,
)

# Transfer tokens
result = hathor.transfer_tokens(
    token_uid="token_uid",
    amount=100,
    destination_address="address",
)

# Mint new tokens
result = hathor.mint_tokens(
    token_uid="token_uid",
    amount=1000,
    mint_authority="address",
)

# Melt (burn) tokens
result = hathor.melt_tokens(
    token_uid="token_uid",
    amount=100,
    melt_authority="address",
)

# Create Nano Contract
result = hathor.create_nano_contract(
    contract_type="payout",
    conditions={...},
    oracle_address="address",
)
```

### ClimateTokenService

Climate-specific token operations:

```python
from blockchain.hathor.climate_token_service import get_climate_token_service

token_service = get_climate_token_service()

# Create drought token
token = token_service.create_drought_token(
    region="São Paulo",
    latitude=-23.5505,
    longitude=-46.6333,
    start_date="2026-01-01",
    end_date="2026-03-31",
    trigger_precipitation_mm=100.0,
    payout_amount=10000,
    total_supply=10000,
)

# Create flood token
token = token_service.create_flood_token(
    region="Rio de Janeiro",
    latitude=-22.9068,
    longitude=-43.1729,
    start_date="2026-01-01",
    end_date="2026-03-31",
    trigger_precipitation_mm=300.0,
    payout_amount=10000,
)

# Create temperature token
token = token_service.create_temperature_token(
    region="Brasília",
    latitude=-15.7801,
    longitude=-47.9292,
    start_date="2026-01-01",
    end_date="2026-12-31",
    trigger_temperature_c=35.0,
    trigger_condition="above",  # Heatwave
    payout_amount=10000,
)

# Get token
token = token_service.get_token("token_uid")

# List tokens
tokens = token_service.list_tokens(
    status=TokenStatus.ACTIVE,
    index_type=ClimateIndexType.DROUGHT,
)

# Execute payout
result = token_service.execute_payout(
    token_uid="token_uid",
    oracle_value=85.5,
    beneficiary_address="address",
)
```

### ClimateOracleService

Climate data and index calculation:

```python
from blockchain.hathor.oracle_service import get_climate_oracle_service

oracle = get_climate_oracle_service()

# Get historical data
data_points = oracle.get_historical_data(
    latitude=-23.5505,
    longitude=-46.6333,
    start_date=datetime(2026, 1, 1),
    end_date=datetime(2026, 3, 31),
    source="openmeteo",
)

# Calculate precipitation index
index_value = oracle.calculate_precipitation_index(
    data_points,
    aggregation="sum",
)

# Calculate temperature index
index_value = oracle.calculate_temperature_index(
    data_points,
    aggregation="avg",
)

# Get complete climate index
index = oracle.get_climate_index(
    index_type="precipitation",
    latitude=-23.5505,
    longitude=-46.6333,
    start_date=datetime(2026, 1, 1),
    end_date=datetime(2026, 3, 31),
    trigger_value=100.0,
    trigger_condition="below",
)

# Check trigger
trigger_met = oracle.check_trigger(
    index_value=85.5,
    trigger_value=100.0,
    condition="below",
)

# Publish to blockchain
tx_hash = oracle.publish_to_blockchain(index)

# Generate oracle report
report = oracle.get_oracle_report(
    token_uid="token_uid",
    index=index,
)
```

---

## 🧪 Testing

### Run Unit Tests

```bash
cd server
pytest tests/unit/test_hathor_integration.py -v
```

### Test Token Creation

```python
def test_create_drought_token():
    token_service = get_climate_token_service()
    
    token = token_service.create_drought_token(
        region="Test Region",
        latitude=-23.5505,
        longitude=-46.6333,
        start_date="2026-01-01",
        end_date="2026-03-31",
        trigger_precipitation_mm=100.0,
        payout_amount=10000,
    )
    
    assert token.token_uid is not None
    assert token.symbol == "CLMT-DROUGHT-TEST-20260101"
    assert token.metadata.index_type == ClimateIndexType.DROUGHT
```

### Test Oracle Data

```python
def test_get_climate_index():
    oracle = get_climate_oracle_service()
    
    index = oracle.get_climate_index(
        index_type="precipitation",
        latitude=-23.5505,
        longitude=-46.6333,
        start_date=datetime(2026, 1, 1),
        end_date=datetime(2026, 1, 31),
        trigger_value=100.0,
        trigger_condition="below",
    )
    
    assert index.index_type == "precipitation"
    assert index.value >= 0
    assert isinstance(index.trigger_met, bool)
```

---

## 📊 Use Cases

### 1. Drought Insurance

```python
# Create drought index token
token = token_service.create_drought_token(
    region="Sertão PE",
    latitude=-8.0,
    longitude=-37.0,
    start_date="2026-01-01",
    end_date="2026-06-30",
    trigger_precipitation_mm=200.0,  # 200mm in 6 months
    payout_amount=50000,  # R$ 50,000
)

# Farmer buys token
hathor.transfer_tokens(
    token_uid=token.token_uid,
    amount=1000,
    destination_address="farmer_wallet",
)

# Oracle fetches data at end of period
index = oracle.get_climate_index(...)

# If precipitation < 200mm, payout executed automatically
if index.trigger_met:
    result = token_service.execute_payout(
        token_uid=token.token_uid,
        oracle_value=index.value,
        beneficiary_address="farmer_wallet",
    )
```

### 2. Flood Insurance

```python
# Create flood index token
token = token_service.create_flood_token(
    region="Petrópolis RJ",
    latitude=-22.5051,
    longitude=-43.1783,
    start_date="2026-01-01",
    end_date="2026-03-31",
    trigger_precipitation_mm=300.0,  # 300mm in 3 months
    payout_amount=100000,  # R$ 100,000
)
```

### 3. Temperature Insurance (Heatwave)

```python
# Create heatwave index token
token = token_service.create_temperature_token(
    region="Mato Grosso",
    latitude=-12.6819,
    longitude=-56.9211,
    start_date="2026-01-01",
    end_date="2026-02-28",
    trigger_temperature_c=35.0,  # Average temp > 35°C
    trigger_condition="above",
    payout_amount=75000,
)
```

---

## 🔐 Security Best Practices

### Wallet Management

```python
# ✅ DO: Store seed in environment variable
import os
seed = os.getenv("HATHOR_WALLET_SEED")

# ❌ DON'T: Hardcode seed in code
seed = "my secret seed here"

# ✅ DO: Use hardware wallet for production
# (Integration with Ledger/Trezor recommended)

# ✅ DO: Implement multi-sig for large payouts
contract = hathor.create_nano_contract(
    contract_type="multisig",
    conditions={
        "required_signatures": 2,
        "signers": ["address1", "address2", "address3"],
    },
)
```

### Oracle Security

```python
# ✅ DO: Use multiple data sources
sources = ["openmeteo", "inmet", "noaa"]
indices = [oracle.get_climate_index(source=s) for s in sources]
average_value = sum(i.value for i in indices) / len(indices)

# ✅ DO: Verify data integrity
is_valid = oracle.verify_data_integrity(index, expected_hash)

# ✅ DO: Implement data quality checks
if len(index.data_points) < expected_days * 0.9:
    raise ValueError("Insufficient data points")
```

---

## 📈 Monitoring

### Transaction Status

```python
# Check transaction confirmation
status = hathor.get_transaction_status(tx_hash)

if status["confirmed"] and status["confirmations"] >= 10:
    print("Transaction confirmed!")
elif status["confirmed"]:
    print(f"Transaction confirmed with {status['confirmations']} confirmations")
else:
    print("Transaction pending...")
```

### Token Status

```python
# Monitor token lifecycle
token = token_service.get_token("token_uid")

print(f"Token Status: {token.status.value}")
print(f"Payout Executed: {token.payout_executed}")
print(f"Payout Amount: {token.payout_amount}")
```

---

## 🌐 Network Information

### Testnet

- **RPC URL**: https://node.testnet.hathor.network
- **Explorer**: https://explorer.testnet.hathor.network
- **Faucet**: (Request test HTR from Hathor team)

### Mainnet

- **RPC URL**: https://node.hathor.network
- **Explorer**: https://explorer.hathor.network
- **Exchanges**: Mercado Bitcoin, Foxbit

---

## 🆘 Troubleshooting

### "Wallet not initialized"

```python
# Solution: Initialize wallet first
hathor = get_hathor_service()
hathor.initialize(seed=os.getenv("HATHOR_WALLET_SEED"))
```

### "Insufficient balance"

```python
# Check balance
balance = hathor.get_balance(token_uid="00")
print(f"HTR Balance: {balance['total']}")

# Request testnet HTR from faucet or transfer from exchange
```

### "Token not found"

```python
# Verify token UID
token = token_service.get_token("token_uid")
if not token:
    print("Token doesn't exist in local registry")
    
# Check blockchain
token_info = hathor.get_token_info("token_uid")
```

---

## 📞 Support

- **Hathor Documentation**: https://docs.hathor.network
- **Hathor Discord**: https://discord.gg/hathor
- **ClimateWise Team**: (Add contact info)

---

**Document Version**: 1.0.0  
**Last Updated**: 24 de Fevereiro de 2026
