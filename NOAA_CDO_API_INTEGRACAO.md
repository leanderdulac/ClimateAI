# 📊 NOAA CDO API Integration Guide

**Data**: 24 de Fevereiro de 2026  
**Status**: ✅ IMPLEMENTADO

---

## 🎯 Resumo da Integração

API NOAA CDO (Climate Data Online) Web Services v2 integrada ao Oracle do ClimateWise.

**API Key Configurada**: `WDjhFaVSxFFpLelfYoKaQjnaTorOMcfV`

---

## 📋 Informações Técnicas da API NOAA

### Autenticação

| Item | Valor |
|------|-------|
| **Tipo** | Token |
| **Header** | `token: <seu_token>` |
| **Rate Limit** | 5 req/segundo |
| **Daily Limit** | 10,000 req/dia |
| **Obter Token** | https://www.ncdc.noaa.gov/cdo-web/apitoken |

### Base URL

```
https://www.ncei.noaa.gov/cdo-web/api/v2/{endpoint}
```

---

## 📍 Endpoints Implementados

### 1. `/stations` - Buscar Estações Próximas

**Propósito**: Encontrar estações meteorológicas próximas a uma coordenada.

**Parâmetros**:
| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `extent` | string | Não | Bounding box: `lat1,lon1,lat2,lon2` |
| `limit` | int | Não | Máximo de resultados (padrão: 25, máx: 1000) |
| `datasetid` | string | Não | Filtrar por dataset |
| `locationid` | string | Não | Filtrar por localização |
| `startdate` | date | Não | Dados após esta data |
| `enddate` | date | Não | Dados antes desta data |

**Exemplo de Request**:
```bash
curl -H "token:WDjhFaVSxFFpLelfYoKaQjnaTorOMcfV" \
  "https://www.ncei.noaa.gov/cdo-web/api/v2/stations?limit=10&extent=-24.05,-47.13,-23.05,-46.13"
```

**Exemplo de Response**:
```json
{
  "results": [
    {
      "id": "GHCND:BR001000",
      "name": "SAO PAULO",
      "latitude": -23.5,
      "longitude": -46.62,
      "elevation": 760,
      "mindate": "1934-01-01",
      "maxdate": "2025-12-31",
      "datacoverage": 0.95
    }
  ],
  "metadata": {
    "resultset": {
      "limit": 10,
      "count": 5,
      "offset": 0
    }
  }
}
```

---

### 2. `/data` - Buscar Dados Climáticos ⭐

**Propósito**: Obter dados climáticos históricos de uma estação.

**Parâmetros**:
| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `datasetid` | string | **SIM** | Dataset (ex: `GHCND`) |
| `stationid` | string | Não | ID da estação (ex: `GHCND:BR001000`) |
| `startdate` | date | **SIM** | Data inicial (YYYY-MM-DD) |
| `enddate` | date | **SIM** | Data final (YYYY-MM-DD) |
| `datatypeid` | string | Não | Tipo de dado (ex: `TMAX,PRCP`) |
| `units` | string | Não | `metric` ou `standard` |
| `limit` | int | Não | Máximo de resultados (máx: 1000) |
| `includemetadata` | bool | Não | Incluir metadados (padrão: true) |

**⚠️ Restrições de Período**:
- Dados diários: **máximo 1 ano** por request
- Dados mensais/anuais: **máximo 10 anos** por request

**Exemplo de Request**:
```bash
curl -H "token:WDjhFaVSxFFpLelfYoKaQjnaTorOMcfV" \
  "https://www.ncei.noaa.gov/cdo-web/api/v2/data?datasetid=GHCND&stationid=GHCND:BR001000&startdate=2025-01-01&enddate=2025-12-31&units=metric&limit=1000&includemetadata=false"
```

**Exemplo de Response**:
```json
{
  "results": [
    {
      "station": "GHCND:BR001000",
      "date": "2025-01-15T00:00:00",
      "datatype": "TMAX",
      "value": 325,
      "attributes": "0"
    },
    {
      "station": "GHCND:BR001000",
      "date": "2025-01-15T00:00:00",
      "datatype": "TMIN",
      "value": 220,
      "attributes": "0"
    },
    {
      "station": "GHCND:BR001000",
      "date": "2025-01-15T00:00:00",
      "datatype": "PRCP",
      "value": 152,
      "attributes": "0"
    }
  ],
  "metadata": {
    "resultset": {
      "limit": 1000,
      "count": 365,
      "offset": 0
    }
  }
}
```

---

## 📊 Tipos de Dados (Datatypes)

| Código | Descrição | Unidade | Fator de Conversão |
|--------|-----------|---------|-------------------|
| **TMAX** | Temperatura máxima | °C × 10 | dividir por 10 |
| **TMIN** | Temperatura mínima | °C × 10 | dividir por 10 |
| **TOBS** | Temperatura observada | °C × 10 | dividir por 10 |
| **PRCP** | Precipitação | mm × 10 | dividir por 10 |
| **SNOW** | Neve | mm × 10 | dividir por 10 |
| **AWND** | Velocidade do vento | m/s × 10 | dividir por 10 |
| **RHAV** | Umidade relativa média | % | nenhum |
| **EVAP** | Evaporação | mm × 10 | dividir por 10 |
| **WSF1** | Rajada de vento (1min) | m/s × 10 | dividir por 10 |
| **WSF2** | Rajada de vento (2min) | m/s × 10 | dividir por 10 |
| **WSF5** | Rajada de vento (5min) | m/s × 10 | dividir por 10 |
| **WT01** | Weather Type 1 (precip) | flag | boolean |
| **WT04** | Weather Type 4 (thunder) | flag | boolean |

---

## 🗂️ Datasets Disponíveis

| ID | Nome | Descrição | Período Máximo |
|----|------|-----------|----------------|
| **GHCND** | Global Historical Climatology Network Daily | Dados diários globais | 1 ano |
| **GSOM** | Global Summary of the Month | Resumo mensal global | 10 anos |
| **GSOY** | Global Summary of the Year | Resumo anual global | 10 anos |
| **PRECIP_15** | Precipitation 15 Minute | Precipitação em 15min | 1 ano |

---

## 🔄 Fluxo de Integração no ClimateWise

```
┌─────────────────────────────────────────────────────────────────┐
│              CLIMATEWISE → NOAA API INTEGRATION                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Solicitação de Dados Climáticos                            │
│     └─ latitude, longitude, start_date, end_date                │
│                                                                  │
│  2. Seleção da Fonte de Dados                                  │
│     ├─ noaa (usa API key) ✅                                    │
│     ├─ inmet (Brasil)                                           │
│     └─ openmeteo (fallback, free)                               │
│                                                                  │
│  3. Busca de Estações Próximas (NOAA /stations)                │
│     ├─ Bounding box: ±0.5° (~55km)                              │
│     ├─ Limit: 10 estações                                       │
│     └─ Seleciona primeira estação disponível                    │
│                                                                  │
│  4. Validação de Período                                       │
│     ├─ Se > 365 dias → trunca para 1 ano                        │
│     └─ Log warning para o usuário                               │
│                                                                  │
│  5. Fetch de Dados (NOAA /data)                                │
│     ├─ datasetid: GHCND                                         │
│     ├─ units: metric                                            │
│     ├─ limit: 1000                                              │
│     └─ includemetadata: false (performance)                     │
│                                                                  │
│  6. Parse e Normalização                                       │
│     ├─ Agrupa por data                                          │
│     ├─ Converte unidades (divide por 10)                        │
│     ├─ Calcula temperatura média (TMAX+TMIN)/2                  │
│     └─ Mapeia datatypes para formato ClimateWise                  │
│                                                                  │
│  7. Criação de ClimateDataPoint                                │
│     ├─ timestamp                                                │
│     ├─ temperature_c                                            │
│     ├─ precipitation_mm                                         │
│     ├─ humidity_pct                                             │
│     ├─ wind_speed_kmh                                           │
│     └─ source: "noaa"                                           │
│                                                                  │
│  8. Tratamento de Erros                                        │
│     ├─ 401: Authentication failed → Log error                   │
│     ├─ 429: Rate limit exceeded → Log error + fallback          │
│     ├─ Outros HTTP errors → Log + fallback                      │
│     └─ Fallback: OpenMeteo                                      │
│                                                                  │
│  9. Retorno dos Dados                                          │
│     └─ List[ClimateDataPoint]                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧪 Exemplo de Uso no ClimateWise

### Via Python

```python
from blockchain.hathor.oracle_service import get_climate_oracle_service
from datetime import datetime, timedelta

oracle = get_climate_oracle_service()

# Buscar dados históricos da NOAA
end_date = datetime.now()
start_date = end_date - timedelta(days=90)  # Últimos 90 dias

data_points = oracle.get_historical_data(
    latitude=-23.5505,  # São Paulo
    longitude=-46.6333,
    start_date=start_date,
    end_date=end_date,
    source="noaa",  # Usa NOAA com API key
)

print(f"Dados obtidos: {len(data_points)} pontos")
print(f"Fonte: {data_points[0].source if data_points else 'None'}")

# Calcular índices
total_precip = oracle.calculate_precipitation_index(data_points, "sum")
avg_temp = oracle.calculate_temperature_index(data_points, "avg")

print(f"Precipitação total: {total_precip:.1f}mm")
print(f"Temperatura média: {avg_temp:.1f}°C")
```

### Via API REST (quando integrada)

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

## ⚠️ Tratamento de Erros

### Códigos de Erro HTTP

| Código | Significado | Ação |
|--------|-------------|------|
| **200** | Success | Processar dados |
| **400** | Bad Request | Verificar parâmetros |
| **401** | Unauthorized | Verificar API token |
| **404** | Not Found | Estação não encontrada |
| **429** | Too Many Requests | Aguardar e retry |
| **500** | Server Error | Retry com backoff |

### Implementação de Retry

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def fetch_noaa_data(...):
    # Implementação com retry automático
    pass
```

---

## 📈 Limites e Cotas

| Limite | Valor | Estratégia |
|--------|-------|------------|
| **Requests/segundo** | 5 | Throttling no código |
| **Requests/dia** | 10,000 | Monitorar uso diário |
| **Resultados/request** | 1000 | Paginação com offset |
| **Período (diário)** | 1 ano | Truncar automaticamente |
| **Período (anual)** | 10 anos | Truncar automaticamente |

---

## 🌍 Estações no Brasil

### Exemplos de Estações

| ID | Nome | Latitude | Longitude | Estado |
|----|------|----------|-----------|--------|
| `GHCND:BR001000` | SAO PAULO | -23.50 | -46.62 | SP |
| `GHCND:BR001001` | RIO DE JANEIRO | -22.90 | -43.17 | RJ |
| `GHCND:BR001002` | BRASILIA | -15.78 | -47.92 | DF |
| `GHCND:BR001003` | SALVADOR | -12.97 | -38.50 | BA |
| `GHCND:BR001004` | FORTALEZA | -3.73 | -38.53 | CE |
| `GHCND:BR001005` | MANAUS | -3.10 | -60.02 | AM |

---

## 📊 Comparação: NOAA vs OpenMeteo

| Característica | NOAA | OpenMeteo |
|----------------|------|-----------|
| **API Key** | ✅ Requer | ❌ Free |
| **Cobertura** | Global (estações) | Global (grade) |
| **Histórico** | Desde 1800s | Desde 1940 |
| **Atualização** | Diária | Diária |
| **Latência** | 1-2 dias | 1-2 dias |
| **Resolução** | Por estação | ~11km grade |
| **Dados** | Observados | Reanálise + obs |
| **Rate Limit** | 5 req/s, 10k/dia | Sem limite rígido |
| **Qualidade** | ✅ Verificada | ✅ Boa |

**Recomendação**: Usar NOAA como fonte primária, OpenMeteo como fallback.

---

## ✅ Checklist de Implementação

- [x] ✅ API key configurada
- [x] ✅ Método `_get_noaa_data()` implementado
- [x] ✅ Busca de estações por bounding box
- [x] ✅ Parse de datatypes (TMAX, TMIN, PRCP, etc.)
- [x] ✅ Conversão de unidades (divide por 10)
- [x] ✅ Cálculo de temperatura média
- [x] ✅ Validação de período (max 1 ano)
- [x] ✅ Tratamento de erros HTTP
- [x] ✅ Fallback para OpenMeteo
- [x] ✅ Logging de operações
- [ ] Testes com dados reais
- [ ] Cache de respostas
- [ ] Rate limiting automático

---

## 📞 Recursos e Links

### Documentação Oficial

- **API Docs**: https://www.ncei.noaa.gov/cdo-web/webservices/v2
- **Get Token**: https://www.ncdc.noaa.gov/cdo-web/apitoken
- **Stations API**: https://www.ncei.noaa.gov/cdo-web/webservices/v2/stations
- **Data API**: https://www.ncei.noaa.gov/cdo-web/webservices/v2/data
- **Datatypes**: https://www.ncei.noaa.gov/cdo-web/webservices/v2/datatypes

### ClimateWise

- **Oracle Service**: `blockchain/hathor/oracle_service.py`
- **Demo Script**: `scripts/demo_hathor_blockchain.py`
- **Docs**: `blockchain/hathor/README.md`

---

## 🎯 Próximos Passos

### Imediato (1-2 semanas)

1. [ ] Testar com estações reais no Brasil
2. [ ] Implementar cache de respostas (Redis)
3. [ ] Adicionar rate limiting automático
4. [ ] Testar fallback NOAA → OpenMeteo

### Curto Prazo (2-4 semanas)

1. [ ] Integrar múltiplas estações para redundância
2. [ ] Calcular médias ponderadas por distância
3. [ ] Adicionar validação de qualidade de dados
4. [ ] Implementar retry com backoff exponencial

### Médio Prazo (1-3 meses)

1. [ ] Dashboard de monitoramento de estações
2. [ ] Alertas de qualidade de dados
3. [ ] Integração com INMET (Brasil)
4. [ ] Publicação de dados na blockchain

---

**Status**: ✅ **NOAA API INTEGRADA E PRONTA PARA TESTES**

**Próximo**: Testar com dados históricos reais de estações brasileiras

---

*Documento gerado em: 24 de Fevereiro de 2026*
