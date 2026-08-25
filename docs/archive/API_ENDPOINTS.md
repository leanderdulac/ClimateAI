# Endpoints da API do FIMCE

O Framework Integrado de Modelagem Climático-Econômica (FIMCE) disponibiliza os seguintes endpoints:

## 🌡️ Dados Climáticos
- `GET /api/v1/clima/historico` - Obter dados climáticos históricos
  - Parâmetros: latitude, longitude, data_inicio, data_fim, variavel (opcional)
- `GET /api/v1/clima/atual` - Obter condições climáticas atuais
  - Parâmetros: latitude, longitude
- `POST /api/v1/noaa/climate-data` - Obter dados climáticos históricos do NOAA
  - Parâmetros: location (string), start_date, end_date, data_type (opcional)
  - Fallback: Embrapa API se NOAA falhar
- `POST /api/v1/noaa/weather-forecast` - Obter previsão do tempo do NOAA
  - Parâmetros: latitude, longitude
  - Fallback: Embrapa API se NOAA falhar
- `GET /api/v1/noaa/status` - Status da integração NOAA
- `GET /api/v1/noaa/data-types` - Tipos de dados disponíveis no NOAA

## 📈 Previsões
- `GET /api/v1/previsao/clima` - Obter previsão climática
  - Parâmetros: latitude, longitude, dias (padrão: 7)
- `GET /api/v1/previsao/eventos` - Obter previsão de eventos climáticos extremos
  - Parâmetros: latitude, longitude, dias (padrão: 30)

## ⚠️ Eventos Climáticos
- `GET /api/v1/eventos` - Obter eventos climáticos detectados
  - Parâmetros: latitude (opcional), longitude (opcional), tipo (opcional), data_inicio (opcional), data_fim (opcional), raio (padrão: 50km)
- `GET /api/v1/eventos/severidade` - Obter eventos por severidade
  - Parâmetros: latitude, longitude, severidade_minima (padrão: 3), dias (padrão: 30)

## 💰 Modelagem Econômica
- `GET /api/v1/modelagem/previsao-precos` - Previsão de preços de commodities
  - Parâmetros: simbolos (lista), latitude (opcional), longitude (opcional), dias (padrão: 30)
- `GET /api/v1/modelagem/impacto-climatico` - Impacto climático sobre preços
  - Parâmetros: simbolo, latitude, longitude, periodo (padrão: 30)

## 🧮 Unified Pricing Orchestrator
- `POST /api/v1/unified-pricing/calculate` - Cálculo unificado de prêmio com 6 modelos + ajuste meteorológico NOAA
  - Corpo: coverage_amount, location_latitude, location_longitude, risk_factors, policy_duration_years, confidence_level, custom_model_weights (opcional), models_to_use (opcional)
  - Saída relevante em `explanation`:
    - `noaa_weather_adjustment`: risco meteorológico calculado e modificador aplicado
    - `noaa_blend_parameters`: parâmetros efetivos usados pelo orquestrador
- `GET /api/v1/unified-pricing/models` - Lista modelos disponíveis e pesos padrão
- `GET /api/v1/unified-pricing/health` - Status do orquestrador

### Parâmetros Operacionais NOAA (ambiente)
- `NOAA_RISK_BLEND_WEIGHT` (padrão: `0.15`, faixa: `0.0` a `1.0`)
  - Define o peso do risco meteorológico NOAA no `combined_risk_score`.
  - Peso base dos modelos internos = `1 - NOAA_RISK_BLEND_WEIGHT`.
- `NOAA_PREMIUM_MAX_IMPACT` (padrão: `0.12`, faixa: `0.0` a `0.5`)
  - Define o teto de aumento no prêmio recomendado vindo do NOAA.
  - Exemplo: `0.12` permite até `+12%`.

### Comportamento de Fallback NOAA
- Se NOAA estiver indisponível, o ajuste é neutro:
  - `combined_risk_score` permanece sem blend NOAA
  - `premium_modifier = 1.0`
  - `warnings` inclui aviso operacional

## 🌾 Agricultural Strategy (ENSO Adaptation)
- `POST /api/v1/agri-strategy/plan` - Plano de estratégia agrícola para risco extremo (El Niño/La Niña)
  - Corpo: `crop_type`, `phenological_stage`, `latitude`, `longitude`, `planning_horizon_days`, `risk_tolerance`, `farm_profile`
  - Saída:
    - `climate_outlook` (regime ENSO + fonte de forecast)
    - `exposure_scores` (heat, drought, excess_rain, flood, wind, disease)
    - `operational_actions` (ações por horizonte e prioridade)
    - `financial_actions` (seguro paramétrico, proteção de caixa/hedge)
    - `alert_triggers` (gatilhos operacionais)
- `GET /api/v1/agri-strategy/catalog` - Catálogo de culturas e estágios suportados
- `GET /api/v1/agri-strategy/health` - Status do módulo

### Exemplo de requisição
```bash
curl -X POST http://localhost:8000/api/v1/agri-strategy/plan \
  -H "Content-Type: application/json" \
  -d '{
    "crop_type": "soybean",
    "phenological_stage": "flowering",
    "latitude": -23.55,
    "longitude": -46.63,
    "planning_horizon_days": 120,
    "risk_tolerance": "medium",
    "farm_profile": {
      "irrigation_available": false,
      "drainage_level": "medium",
      "soil_cover_level": "high",
      "farm_size_hectares": 180
    }
  }'
```

### Exemplo de resposta (resumido)
```json
{
  "crop_type": "soybean",
  "phenological_stage": "flowering",
  "planning_horizon_days": 120,
  "climate_outlook": {
    "enso": {
      "regime_label": "la_nina",
      "regime_confidence": "high",
      "impact_risk_modifier": 1.08
    },
    "forecast_source": "NOAA/NWS"
  },
  "exposure_scores": {
    "heat": 0.42,
    "drought": 0.38,
    "excess_rain": 0.74,
    "flood": 0.69,
    "wind": 0.41,
    "disease": 0.63
  },
  "operational_actions": [...],
  "financial_actions": [...],
  "alert_triggers": [...]
}
```

## 🔔 Sistema de Alertas
- `GET /api/v1/alertas` - Obter alertas ativos
  - Parâmetros: latitude (opcional), longitude (opcional), nivel_minimo (padrão: 1), ativo (padrão: true), limite (padrão: 50)
- `GET /api/v1/alertas/usuario` - Obter alertas de um usuário
  - Parâmetros: usuario_id, lido (opcional)
- `PUT /api/v1/alertas/{alerta_id}/marcar-lido` - Marcar alerta como lido

## 🏠 Gerais
- `GET /` - Página inicial do FIMCE
- `GET /health` - Verificação de saúde do sistema
- `GET /docs` - Documentação interativa da API (Swagger UI)
- `GET /redoc` - Documentação da API (ReDoc)

## 📊 Exemplos de Uso

### Obter previsão climática para São Paulo
```
GET /api/v1/previsao/clima?latitude=-23.5505&longitude=-46.6333&dias=7
```

### Obter previsão de preços de soja com impacto climático
```
GET /api/v1/modelagem/previsao-precos?simbolos=SOF&latitude=-23.5505&longitude=-46.6333
```

### Obter alertas de alta severidade em uma região
```
GET /api/v1/alertas?latitude=-23.5505&longitude=-46.6333&nivel_minimo=3
```

## 📋 Modelos de Dados

### ClimaData
- latitude: float
- longitude: float
- data: datetime
- temperatura: float (opcional)
- precipitacao: float (opcional)
- umidade: float (opcional)
- vento_velocidade: float (opcional)
- vento_direcao: float (opcional)
- pressao: float (opcional)
- indice_spi: float (opcional)
- fonte: str (opcional)

### PrevisaoClima
- latitude: float
- longitude: float
- data_inicio: datetime
- data_fim: datetime
- variaveis: List[ClimaData]
- metodo: str
- confianca: float

### EventoClimatico
- tipo: Enum (SECA, ENCHENTE, ONDA_CALOR, GEADA, SECA_FLASH)
- latitude: float
- longitude: float
- data_inicio: datetime
- data_fim: datetime (opcional)
- intensidade: float
- probabilidade: float
- descricao: str
- nivel_alerta: int

### PrevisaoPreco
- simbolo: str
- descricao: str
- data_referencia: datetime
- preco_atual: float
- preco_previsto: float
- variacao_prevista: float
- confianca: float
- fatores_climaticos: List[Dict]

### Alerta
- id: str
- tipo: str
- titulo: str
- descricao: str
- nivel: int (1-5)
- localizacao: Dict (opcional)
- data_criacao: datetime
- data_validade: datetime (opcional)
- lido: bool
