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
