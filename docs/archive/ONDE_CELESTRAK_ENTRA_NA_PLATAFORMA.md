# 🛰️ ONDE O CELESTRAK ENTRA NA PLATAFORMA CLIMATEWISE

## Visão Geral da Integração

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIMATEWISE PLATFORM                           │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌───────────────┐
│  CELESTRAK    │   │   OPENMETEO     │   │  ATLAS DIGITAL│
│  SPACE LAYER  │   │ ATMOSPHERE LAYER│   │ SURFACE LAYER │
└───────────────┘   └─────────────────┘   └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │    UNIFIED PLATFORM           │
              │  (Orquestra todos os dados)   │
              └───────────────────────────────┘
```

---

## 📍 5 PONTOS DE INTEGRAÇÃO DO CELESTRAK

### 1. **CAMADA SPACE (Dados de Satélites)**

**Onde:** `services/celestrak_service.py`

**O que entra:**
```python
# TLE (Two-Line Elements) - Posição orbital de satélites
tle_data = celestrak_service.get_tle_data(category='stations')

# Resultado:
[
  TLEData(
    norad_id='25544',
    satellite_name='ISS (ZARYA)',
    line1='1 25544U 98067A   24056.50000000 ...',
    line2='2 25544 51.6400 200.0000 0007000 ...',
    orbit_type=OrbitType.LEO,
    ...
  ),
  ...
]
```

**Uso na plataforma:**
- Rastrear posição de satélites segurados
- Validar localização em caso de sinistro
- Calcular órbitas para determinação de cobertura

---

### 2. **ALERTAS DE CONJUNÇÃO (SOCRATES)**

**Onde:** `services/celestrak_service.py` → `get_conjunction_alerts()`

**O que entra:**
```python
# Alertas de risco de colisão orbital
alerts = celestrak_service.get_conjunction_alerts(
    satellite_norad='25544',  # ISS
    min_probability=1e-6,
    max_distance_km=5.0
)

# Resultado:
[
  ConjunctionAlert(
    conjunction_id='CONJ-20260226-0001',
    object1_norad='25544',
    object1_name='ISS (ZARYA)',
    object2_norad='39574',
    object2_name='DEBRIS 2009-001A',
    tca=datetime(2026, 2, 27, 14, 30),
    miss_distance_km=0.5,
    collision_probability=6.59e-06,
    risk_level=RiskLevel.LOW,
    ...
  ),
  ...
]
```

**Uso na plataforma:**
- **Trigger de seguro:** Probabilidade > 10⁻⁴ → Payout automático
- **Alerta em tempo real:** Dashboard mostra riscos ativos
- **Validação de sinistro:** Confirma se conjunção foi catalogada

**Endpoint da API:**
```http
GET /api/v1/atlas-simulation/live-events

Resposta:
{
  "event_id": "evt_abc123",
  "municipio": "Órbita LEO",
  "disaster_type": "conjunction",
  "severity_score": 2.5,
  "payout_triggered": false,
  ...
}
```

---

### 3. **CLIMA ESPACIAL (Space Weather)**

**Onde:** `services/celestrak_service.py` → `get_space_weather()`

**O que entra:**
```python
# Dados de clima espacial
space_weather = celestrak_service.get_space_weather()

# Resultado:
SpaceWeatherData(
  timestamp=datetime.now(),
  kp_index=4.3,              # 0-9 (geomagnetic activity)
  ap_index=12,
  solar_flux=150.5,
  geomagnetic_storm=False,
  storm_level="None",
  solar_radiation_storm=False,
  radio_blackout=False,
  ...
)
```

**Uso na plataforma:**
- **Trigger de seguro:** Kp index >= 7 → Tempestade geomagnética severa
- **Payout automático:** Baseado no índice Kp
- **Correlação cruzada:** Space weather → afeta clima terrestre

**Exemplo de Trigger:**
```python
# Produto: Satellite Operator Bundle
if space_weather.kp_index >= 7:
    payout_percentage = min(1.0, (space_weather.kp_index - 6) / 3)
    # Kp=7 → 33% payout
    # Kp=8 → 66% payout
    # Kp=9 → 100% payout
```

---

### 4. **CATÁLOGO SATCAT (Informações de Satélites)**

**Onde:** `services/celestrak_service.py` → `get_satellite_info()`

**O que entra:**
```python
# Informações do catálogo de satélites
sat_info = celestrak_service.get_satellite_info(norad_id='25544')

# Resultado:
SatelliteInfo(
  norad_id='25544',
  satcat_code='CAT-25544',
  satellite_name='ISS (ZARYA)',
  country='ISS',
  launch_date=datetime(1998, 11, 20),
  orbit_type='LEO',
  status='Active',
  operator='NASA/Roscosmos',
  purpose='Space Station',
  ...
)
```

**Uso na plataforma:**
- **Subscrição de riscos:** Valida se satélite existe e está ativo
- **Cálculo de prêmio:** Baseado em órbita, operador, propósito
- **Validação de apólice:** Confirma dados do satélite segurado

---

### 5. **PLATAFORMA UNIFICADA (Integração Final)**

**Onde:** `services/unified_earth_space_platform.py`

**Como o CelesTrak se integra:**

```python
class UnifiedEarthSpacePlatform:
    def __init__(self):
        # CelesTrak é um dos 3 serviços principais
        self.celestrak_service = CelesTrakService()
        self.atlas_service = AtlasDisasterService()
        self.realtime_climate = AtlasRealTimeClimateService()
    
    def get_unified_risk_assessment(self, latitude, longitude, altitude_km):
        # Se altitude > 100km → usa dados do CelesTrak
        if altitude_km > 100:
            assessment.space_risk = self._get_space_risk(
                latitude, longitude, altitude_km
            )
            # _get_space_risk chama:
            # - celestrak_service.get_conjunction_alerts()
            # - celestrak_service.get_space_weather()
```

**Fluxo completo:**
```
1. Cliente solicita seguro de satélite
   ↓
2. Plataforma consulta CelesTrak
   - TLE data (posição orbital)
   - SOCRATES (riscos de conjunção)
   - Space Weather (tempestades)
   ↓
3. Calcula risco composto
   - Space risk (CelesTrak): 60%
   - Atmospheric risk (OpenMeteo): 30%
   - Surface risk (Atlas): 10%
   ↓
4. Define prêmio e triggers
   ↓
5. Monitora em tempo real
   ↓
6. Trigger detectado → Payout automático via Oracle
```

---

## 🎯 EXEMPLOS PRÁTICOS DE USO

### Exemplo 1: **Seguro de Colisão de Satélite**

```python
# 1. Dados do CelesTrak entram no trigger
alerts = celestrak_service.get_conjunction_alerts(
    satellite_norad='43013',  # Tiangong-1
    min_probability=1e-6
)

# 2. Verifica se trigger foi atingido
for alert in alerts:
    if alert.collision_probability > 1e-4:  # Threshold da apólice
        # 3. Trigger ativado!
        payout_amount = insured_value * 0.5  # 50% payout
        trigger_oracle_payout(alert, payout_amount)
```

**Endpoint correspondente:**
```http
POST /api/v1/unified-platform/risk-assessment
{
  "latitude": 0,
  "longitude": 0,
  "altitude_km": 400,  # Órbita LEO
  "include_space": true
}

Resposta:
{
  "space_risk": {
    "conjunction_risk": {
      "active_alerts": 2,
      "max_probability": 6.59e-06,
      "risk_level": "LOW"
    }
  },
  "composite_risk_score": 3.5,
  "composite_risk_level": "MEDIUM"
}
```

---

### Exemplo 2: **Seguro de Tempestade Geomagnética**

```python
# 1. Dados de Space Weather do CelesTrak
space_weather = celestrak_service.get_space_weather()

# 2. Verifica trigger
if space_weather.kp_index >= 7:
    # Tempestade geomagnética severa!
    # Kp=7, 8, ou 9 (escala 0-9)
    
    # 3. Calcula payout baseado no índice
    payout_percentage = (space_weather.kp_index - 6) / 3
    # Kp=7 → 33%
    # Kp=8 → 66%
    # Kp=9 → 100%
    
    trigger_payout(payout_percentage)
```

**Produto correspondente:**
```yaml
# Satellite Operator Bundle
triggers:
  - type: geomagnetic_storm
    source: CelesTrak
    conditions:
      kp_index_min: 6  # Tempestade G2 ou maior
```

---

### Exemplo 3: **Correlação Cruzada (Space → Atmosphere)**

```python
# 1. CelesTrak detecta tempestade geomagnética
space_weather = celestrak_service.get_space_weather()
if space_weather.kp_index >= 6:
    # 2. Plataforma unificada correlaciona com clima terrestre
    assessment = unified_platform.get_unified_risk_assessment(
        latitude=-23.55,
        longitude=-46.63,
        altitude_km=0  # Superfície
    )
    
    # 3. Identifica correlação
    assessment.cross_domain_correlations.append({
        'type': 'space_weather_to_atmosphere',
        'description': 'Tempestade geomagnética pode afetar padrões climáticos',
        'confidence': 0.6,
        'impact': 'Moderate impact on atmospheric circulation'
    })
    
    # 4. Gera recomendação
    assessment.recommendations.append(
        '🌞 Tempestade geomagnética detectada - monitorar clima terrestre'
    )
```

---

## 📊 ARQUIVOS ONDE CELESTRAK ESTÁ PRESENTE

| Arquivo | Função do CelesTrak | Linhas |
|---------|---------------------|--------|
| `services/celestrak_service.py` | **Serviço principal** - Toda integração com API CelesTrak | 500 |
| `services/unified_earth_space_platform.py` | **Orquestração** - Integra CelesTrak com Atlas e OpenMeteo | 650 |
| `api/atlas_oracle_simulation.py` | **Simulação** - Gera eventos mock baseados em CelesTrak | 200 |
| `api/unified_platform.py` | **Endpoints** - API expõe dados do CelesTrak | 200 |
| `components/AtlasDashboardPanel.tsx` | **Frontend** - Mostra dados espaciais no dashboard | 600 |

**Total:** ~2,150 linhas de código integrando CelesTrak

---

## 🔗 FLUXO DE DADOS COMPLETO

```
┌─────────────────┐
│   CelesTrak.org │
│  (API pública)  │
└────────┬────────┘
         │ HTTPS
         │ GET /NORAD/elements/
         │ GET /SOCRATES/
         ▼
┌─────────────────────────────────┐
│  services/celestrak_service.py  │
│  - get_tle_data()               │
│  - get_conjunction_alerts()     │
│  - get_space_weather()          │
│  - get_satellite_info()         │
└────────┬────────────────────────┘
         │
         │ Dados processados
         │ (TLEData, ConjunctionAlert, SpaceWeatherData)
         ▼
┌─────────────────────────────────────┐
│  services/unified_earth_space_      │
│           platform.py               │
│  - get_unified_risk_assessment()    │
│  - _get_space_risk()                │
│  - _calculate_composite_risk()      │
└────────┬────────────────────────────┘
         │
         │ Risco composto calculado
         │ (score 0-10, level HIGH/MEDIUM/LOW)
         ▼
┌─────────────────────────────────┐
│  api/unified_platform.py        │
│  POST /risk-assessment          │
│  GET /insurance-products        │
│  GET /dashboard-summary         │
└────────┬────────────────────────┘
         │
         │ JSON via HTTP
         ▼
┌─────────────────────────────────┐
│  Frontend (React)               │
│  components/AtlasDashboardPanel │
│  - Space Layer tab              │
│  - KPI cards                    │
│  - Conjunction alerts           │
└─────────────────────────────────┘
```

---

## 💡 RESUMO: ONDE CELESTRAK ENTRA

| Camada | Entrada do CelesTrak | Finalidade |
|--------|---------------------|------------|
| **Dados** | TLE, SOCRATES, Space Weather, SATCAT | Fornecer dados espaciais brutos |
| **Serviço** | `celestrak_service.py` | Processar e formatar dados |
| **Orquestração** | `unified_earth_space_platform.py` | Integrar com Atlas + OpenMeteo |
| **API** | `/api/v1/unified-platform/*` | Expor dados via endpoints |
| **Oracle** | `atlas_oracle_simulation.py` | Triggers de payout baseados em espaço |
| **Frontend** | `AtlasDashboardPanel.tsx` | Visualizar dados espaciais |
| **Produtos** | 3 seguros paramétricos | Triggers espaciais (colisão, space weather) |

---

## 🎯 CONCLUSÃO

**O CelesTrak entra em 6 níveis na plataforma:**

1. ✅ **Fonte de dados espaciais** (TLE, SOCRATES, Space Weather)
2. ✅ **Serviço de processamento** (`celestrak_service.py`)
3. ✅ **Camada SPACE** da arquitetura unificada
4. ✅ **Triggers de seguros** paramétricos espaciais
5. ✅ **Correlações cruzadas** (espaço → terra)
6. ✅ **Dashboard** de monitoramento orbital

**Sem CelesTrak:** A plataforma perderia a camada espacial e não poderia oferecer seguros de satélites ou proteção contra clima espacial.

**Com CelesTrak:** ClimateWise é a **primeira plataforma Terra-Espaço** integrada do mercado!
