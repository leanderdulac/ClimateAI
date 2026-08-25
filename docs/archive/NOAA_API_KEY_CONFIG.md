# ✅ NOAA API Key Adicionada ao Oracle

**Data**: 24 de Fevereiro de 2026  
**Status**: ✅ CONFIGURADO

---

## 📊 Resumo

API Key do NOAA adicionada ao serviço Oracle para busca de dados climáticos históricos.

```
NOAA API Key: WDjhFaVSxFFpLelfYoKaQjnaTorOMcfV
Status: ✅ Configurada
Local: blockchain/hathor/oracle_service.py
```

---

## 📁 Arquivos Atualizados

### 1. oracle_service.py

**Local**: `server/blockchain/hathor/oracle_service.py`

**Alteração**:
```python
# Antes:
self.noaa_token = ""  # Set from environment

# Depois:
self.noaa_token = "WDjhFaVSxFFpLelfYoKaQjnaTorOMcfV"  # NOAA API key
```

**Método Atualizado**: `_get_noaa_data()`

Agora busca dados reais da NOAA:
1. Encontra estações próximas
2. Busca dados históricos
3. Parseia temperatura e precipitação
4. Fallback para OpenMeteo se falhar

---

### 2. .env.example

**Local**: `.env.example`

**Adições**:

```bash
# NOAA Climate API
NOAA_API_KEY=WDjhFaVSxFFpLelfYoKaQjnaTorOMcfV

# HATHOR BLOCKCHAIN CONFIGURATION
HATHOR_NETWORK=testnet
HATHOR_WALLET_ADDRESS=
HATHOR_WALLET_SEED=
HATHOR_CLIMATE_TOKEN_SYMBOL=CLMT
HATHOR_CLIMATE_TOKEN_NAME=Climate Index Token
HATHOR_CLIMATE_TOKEN_INITIAL_SUPPLY=1000000
```

---

## 🌡️ Dados Disponíveis via NOAA

### Tipos de Dados

| datatype | Descrição | Unidade |
|----------|-----------|---------|
| **TMAX** | Temperatura máxima | °C |
| **TMIN** | Temperatura mínima | °C |
| **PRCP** | Precipitação | mm |
| **SNOW** | Neve | mm |
| **AWND** | Velocidade do vento | m/s |
| **RHAV** | Umidade relativa média | % |

### Cobertura

- **Global**: Estações em todo o mundo
- **Brasil**: Estações INMET integradas
- **Histórico**: Dados desde 1800s (varia por estação)
- **Atualização**: Diária

---

## 🚀 Como Usar

### 1. Via Oracle Service

```python
from blockchain.hathor.oracle_service import get_climate_oracle_service

oracle = get_climate_oracle_service()

# Buscar dados históricos da NOAA
data_points = oracle.get_historical_data(
    latitude=-23.5505,
    longitude=-46.6333,
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 12, 31),
    source="noaa",  # Usa NOAA com API key configurada
)

print(f"Dados obtidos: {len(data_points)} pontos")
print(f"Fonte: {data_points[0].source}")
```

### 2. Via API REST (quando integrada)

```bash
curl -X POST http://localhost:8000/api/v1/blockchain/hathor/oracle/index \
  -H "Content-Type: application/json" \
  -d '{
    "index_type": "precipitation",
    "latitude": -23.5505,
    "longitude": -46.6333,
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "trigger_value": 100.0,
    "trigger_condition": "below",
    "source": "noaa"
  }'
```

---

## 📊 Exemplo de Resposta NOAA

```json
{
  "results": [
    {
      "station": "USW00094728",
      "date": "2025-01-15T00:00:00",
      "datatype": "TMAX",
      "value": 32.5,
      "attributes": "0"
    },
    {
      "station": "USW00094728",
      "date": "2025-01-15T00:00:00",
      "datatype": "PRCP",
      "value": 15.2,
      "attributes": "0"
    }
  ]
}
```

---

## 🔄 Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIMATE ORACLE FLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Solicitação de Dados                                        │
│     └─ latitude, longitude, start_date, end_date                │
│                                                                  │
│  2. Seleção da Fonte                                            │
│     ├─ noaa (usa API key configurada) ✅                        │
│     ├─ inmet (Brasil)                                           │
│     └─ openmeteo (fallback, free)                               │
│                                                                  │
│  3. Busca de Estações Próximas                                  │
│     └─ NOAA API: /stations?lat=X&lon=Y&limit=5                  │
│                                                                  │
│  4. Busca de Dados Históricos                                   │
│     └─ NOAA API: /data?stationid=XXX&start=YYYY-MM-DD           │
│                                                                  │
│  5. Parse e Normalização                                        │
│     ├─ temperature_c                                            │
│     ├─ precipitation_mm                                         │
│     ├─ humidity_pct                                             │
│     └─ wind_speed_kmh                                           │
│                                                                  │
│  6. Cálculo de Índices                                          │
│     ├─ precipitation_sum                                        │
│     ├─ temperature_avg                                          │
│     └─ trigger verification                                     │
│                                                                  │
│  7. Publicação na Blockchain (opcional)                         │
│     └─ Hathor Nano Contract                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ Limites da API NOAA

| Limite | Valor |
|--------|-------|
| **Requests/dia** | Ilimitado (com API key) |
| **Requests/segundo** | 5 por segundo |
| **Dados históricos** | Desde 1800s (varia) |
| **Estações** | ~150,000 globalmente |
| **Dados por request** | Máximo 1000 registros |

---

## 🔍 Testes

### Testar Integração NOAA

```bash
cd /home/exp/Downloads/ClimateAI/server
source venv-hathor/bin/activate

# Executar script de teste
python -c "
from blockchain.hathor.oracle_service import get_climate_oracle_service
from datetime import datetime, timedelta

oracle = get_climate_oracle_service()

# Testar busca NOAA
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

data = oracle.get_historical_data(
    latitude=-23.5505,
    longitude=-46.6333,
    start_date=start_date,
    end_date=end_date,
    source='noaa',
)

print(f'NOAA data points: {len(data)}')
print(f'Source: {data[0].source if data else \"None\"}')
"
```

---

## 📈 Próximos Passos

### Imediato

1. [x] ✅ Adicionar NOAA API key
2. [x] ✅ Implementar método _get_noaa_data()
3. [x] ✅ Atualizar .env.example
4. [ ] Testar com dados reais
5. [ ] Adicionar cache de respostas

### Curto Prazo

1. [ ] Implementar retry logic para rate limits
2. [ ] Adicionar múltiplas estações para redundância
3. [ ] Calcular médias de múltiplas estações
4. [ ] Adicionar validação de qualidade de dados

---

## 📞 Recursos

### NOAA API Documentation

- **API Docs**: https://www.ncdc.noaa.gov/cdo-web/webservices
- **Token**: https://www.ncdc.noaa.gov/cdo-web/token
- **Stations**: https://www.ncdc.noaa.gov/cdo-web/webservices/v2/stations
- **Data**: https://www.ncdc.noaa.gov/cdo-web/webservices/v2/data

### ClimateWise Oracle

- **Service**: `blockchain/hathor/oracle_service.py`
- **Demo**: `scripts/demo_hathor_blockchain.py`
- **Docs**: `blockchain/hathor/README.md`

---

## ✅ Checklist

- [x] NOAA API key adicionada
- [x] Método _get_noaa_data() implementado
- [x] .env.example atualizado
- [x] Fallback para OpenMeteo configurado
- [ ] Testes com dados reais
- [ ] Cache implementado
- [ ] Rate limiting tratado

---

**Status**: ✅ **NOAA API KEY CONFIGURADA E PRONTA PARA USO**

**Próximo**: Testar integração com dados históricos reais

---

*Documento gerado em: 24 de Fevereiro de 2026*
