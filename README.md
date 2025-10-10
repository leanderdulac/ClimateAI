# ClimateAI - Framework Integrado de Modelagem Climático-Econômica (FIMCE)

APP Atuarial Climático que integra o Framework Integrado de Modelagem Climático-Econômica (FIMCE) para prever eventos climáticos extremos e seus impactos nos preços de commodities e mercados financeiros.

## 🌍 Visão Geral

O sistema combina:
- **Previsão Climática Avançada**: Ensemble de modelos ML + físicos para previsão meteorológica
- **Detecção de Eventos Extremos**: Identificação precoce de secas, enchentes, ondas de calor
- **Modelagem Econômica Integrada**: Impacto de eventos climáticos nos preços de commodities
- **Sistema de Alertas**: Monitoramento 24/7 com alertas automáticos
- **Tokenização de Eventos Climáticos**: Mecanismo para transformar eventos climáticos em ativos financeiros

## 🏗️ Arquitetura

O sistema é composto por duas partes principais:

### Frontend (React/Vite)
- Localizado em `client/`
- Interface web moderna com React e TypeScript
- Componentes para visualização de dados climáticos
- Simulador de preços e tokenização de eventos
- Design responsivo com Tailwind CSS

### Backend (FastAPI)
- Localizado em `server/`
- API REST com endpoints para dados climáticos e econômicos
- Serviços de previsão e detecção de eventos climáticos
- Modelagem de impactos econômicos
- Sistema de alertas inteligente

## 🚀 Execução

### Requisitos
- Python 3.9+
- Node.js 18+
- Docker e Docker Compose (opcional)

### Execução Local

1. Instale as dependências do backend:
```bash
cd server
pip install -r requirements.txt
```

2. Configure as variáveis de ambiente:
```bash
cp .env.template .env
# Edite .env com suas chaves de API
```

3. Execute o backend:
```bash
cd server
python main.py
# ou
uvicorn main:app --reload
```

4. Em outro terminal, instale as dependências do frontend:
```bash
cd client
npm install
```

5. Execute o frontend:
```bash
cd client
npm run dev
```

### Execução com Docker Compose

1. Execute todos os serviços:
```bash
docker-compose up --build
```

## 🔌 APIs Disponíveis

- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:5173
- **Documentação da API**: http://localhost:8000/docs

Endpoints principais:
- `GET /api/v1/clima/historico` - Dados climáticos históricos
- `GET /api/v1/previsao/clima` - Previsão climática
- `GET /api/v1/eventos` - Eventos climáticos detectados
- `GET /api/v1/modelagem/previsao-precos` - Previsão de preços de commodities
- `GET /api/v1/alertas` - Sistema de alertas

## 📊 Funcionalidades

1. **Seleção de Localização**: Escolha de coordenadas para análise climática
2. **Visualização de Dados Climáticos**: Séries históricas e previsões
3. **Simulador de Preços**: Modelagem do impacto climático nos preços
4. **Tokenização de Eventos**: Mecanismo para criar tokens representando eventos climáticos
5. **Monitoramento de Contratos Inteligentes**: Rastreamento de contratos baseados em eventos climáticos
