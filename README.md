# ClimateWise - Framework Integrado de Modelagem Climático-Econômica (FIMCE)

APP Atuarial Climático que integra o Framework Integrado de Modelagem Climático-Econômica (FIMCE) para prever eventos climáticos extremos e seus impactos nos preços de commodities e mercados financeiros.

## 🌍 Visão Geral

O sistema combina:
- **Previsão Climática Avançada**: Ensemble de modelos ML + físicos para previsão meteorológica
- **Detecção de Eventos Extremos**: Identificação precoce de secas, enchentes, ondas de calor
- **Modelagem Econômica Integrada**: Impacto de eventos climáticos nos preços de commodities
- **Sistema de Alertas**: Monitoramento 24/7 com alertas automáticos
- **Tokenização de Eventos Climáticos**: Mecanismo para transformar eventos climáticos em ativos financeiros
- **Integração com APIs Climáticas**: NOAA, Embrapa, OpenMeteo com sistema de fallback inteligente

## 🚀 **Recursos Principais**

### ✅ **Plataforma Completa**
- **Backend API** (FastAPI) - Port 8000
- **Frontend React** (Vite) - Port 3000
- **Landing Page** (HTML/CSS/JS) - Port 8080

### ✅ **Scripts de Gerenciamento**
- `start_platform.sh` - Inicia todos os serviços
- `stop_platform.sh` - Para todos os serviços
- `status_platform.sh` - Verifica status da plataforma
- `start_landing_page.sh` - Inicia apenas a landing page
- `generate_pdf.sh` - Gera PDF da landing page

### ✅ **Integrações Climáticas**
- **NOAA (National Oceanic and Atmospheric Administration)**: Dados climáticos oficiais dos EUA
- **Embrapa**: Dados climáticos brasileiros especializados em agricultura
- **OpenMeteo**: API gratuita de dados meteorológicos globais
- **Sistema de Fallback**: APIs secundárias ativadas automaticamente em caso de falha

### ✅ **Landing Page Aprimorada**
- Design moderno inspirado no i4sea.com
- Elementos visuais ricos com gradientes e animações
- Demonstração interativa conectada ao backend
- Design responsivo para todos os dispositivos
- PDF profissional gerado automaticamente

## 🏗️ Arquitetura

O sistema é composto por três partes principais:

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

### Landing Page (HTML/CSS/JS)
- Arquivo `landing-page.html` autônomo
- Design profissional com elementos visuais ricos
- Demonstração interativa conectada ao backend
- Otimizado para conversão e apresentação

## 🚀 **Como Usar**

### **1. Iniciar Toda a Plataforma**
```bash
./start_platform.sh
```

### **2. Verificar Status**
```bash
./status_platform.sh
```

### **3. Acessar os Serviços**

### **4. Gerar PDF da Landing Page**
```bash
./generate_pdf.sh
```

### **5. Parar a Plataforma**
```bash
./stop_platform.sh
```
## Dependências e Ambiente

1. Instale as dependências:
  ```bash
  pip install -r requirements.txt
  ```

2. Configure as variáveis de ambiente:
  - Crie um arquivo `.env` baseado em `.env.example` (client) e adicione as chaves necessárias.
  - Para Supabase, configure `SUPABASE_URL` e `SUPABASE_ANON_KEY`.
  - Para NOAA, configure `NOAA_API_KEY` se disponível.

3. Execute scripts de verificação e testes:
  ```bash
  ./run_tests_venv.sh
  ```

## Recomendações

- Use ambientes virtuais para isolar dependências.
- Consulte os scripts de health check e verificação de conexão para garantir a estabilidade.
- Para mais detalhes, veja os arquivos de teste e scripts na pasta `server/`.

## 🔗 **Integração Landing Page ↔ Dashboard**

### **Fluxo de Conversão Otimizado**
A landing page está totalmente integrada ao dashboard para maximizar conversões:

#### **Botões de CTA Conectados**
- **"Acessar Dashboard"**: Redireciona diretamente para `http://localhost:3000/welcome`
- **Verificação Automática**: JavaScript verifica se o dashboard está rodando
- **Fallback Inteligente**: Se dashboard offline, mostra alerta para iniciar plataforma

#### **Página de Boas-Vindas**
- **Rota `/welcome`**: Página dedicada para usuários vindos da landing page
- **Onboarding Guiado**: Explica funcionalidades principais do ClimateWise
- **Navegação Fluida**: Botões para explorar dashboard completo
- **Design Consistente**: Mantém identidade visual da landing page

#### **Experiência Seamless**
1. **Usuário visita landing page** (`http://localhost:8080/landing-page.html`)
2. **Clica em "Acessar Dashboard"** → Redirecionado para `/welcome`
3. **Página de boas-vindas** explica funcionalidades e guia usuário
4. **Transição suave** para dashboard principal (`/`)

### **Como Testar a Integração**
```bash
# Script automatizado de teste
./test_integration.sh

# Ou testar manualmente:
# 1. Iniciar landing page: ./start_landing_page.sh
# 2. Iniciar plataforma: ./start_platform.sh
# 3. Acessar landing page e clicar nos botões CTA
# 4. Verificar redirecionamento para dashboard
```

## 🌐 **Landing Page Detalhada**

### Design e Funcionalidades
- **Hero Section**: Apresentação com gradientes dinâmicos e animações
- **Seção de Demonstração**: Interface interativa conectada ao backend
- **Recursos**: Cards com ícones Font Awesome e hover effects
- **Depoimentos**: Design glassmorphism com avatares personalizados
- **Call-to-Action**: Seção de conversão com elementos visuais ricos

### Demonstração Interativa
- Conecta com APIs reais do ClimateWise
- Mostra previsões climáticas em tempo real
- Simula análises de risco e precificação
- Interface responsiva e moderna

### PDF Profissional
- Gerado automaticamente com Chrome headless
- Formato A4 otimizado
- Inclui todas as animações e estilos
- Pronto para compartilhamento e apresentação

## 📊 **APIs Disponíveis**

### Clima
- `GET /api/v1/clima/previsao` - Previsão meteorológica
- `GET /api/v1/clima/eventos` - Detecção de eventos extremos
- `GET /api/v1/clima/alertas` - Sistema de alertas

### Modelagem
- `POST /api/v1/modelagem/derivativos-climaticos/analise-capital` - Análise de capital
- `POST /api/v1/modelagem/precos` - Precificação de derivativos
- `GET /api/v1/modelagem/simulacao` - Simulações Monte Carlo

### Localização
- `GET /api/v1/localizacao/cidade/busca?termo={termo}&estado={estado}` - Busca de cidades brasileiras
- `GET /api/v1/localizacao/cep/{cep}` - Busca de localização por CEP
- `GET /api/v1/localizacao/coordenadas` - Geocodificação reversa

### IA e Análise
- `POST /api/v1/grok/analyze` - Análise de dados climáticos com Grok especialista
- `POST /api/v1/grok/insights` - Geração de insights climáticos especializados
- `POST /api/v1/grok/parametric-insurance` - Análise de seguros paramétricos
- `POST /api/v1/grok/actuarial-calculation` - Cálculos atuariais para seguros
- `GET /api/v1/grok/status` - Status da integração com Grok
- `GET /api/v1/grok/models` - Informações sobre modelos especializados
- `POST /api/v1/noaa/climate-data` - Dados climáticos históricos do NOAA
- `POST /api/v1/noaa/weather-forecast` - Previsão do tempo do National Weather Service
- `GET /api/v1/noaa/status` - Status da integração com NOAA
- `GET /api/v1/noaa/data-types` - Tipos de dados climáticos disponíveis

## 🛠️ **Tecnologias Utilizadas**

### Backend
- **FastAPI**: Framework web assíncrono
- **Pandas/NumPy**: Processamento de dados
- **Scikit-learn**: Machine Learning
- **SQLAlchemy**: ORM para banco de dados
- **OpenMeteo/Embrapa**: APIs climáticas

### Integração com IA
- **Google Gemini**: Análise avançada de dados climáticos
- **xAI Grok**: Especialista em seguros paramétricos, normas SUSEP, cálculos atuariais e histórico climático brasileiro (1994-2024)
- **NOAA (National Oceanic and Atmospheric Administration)**: Dados climáticos históricos e previsões meteorológicas

### Frontend
- **React**: Biblioteca UI
- **TypeScript**: Tipagem estática
- **Vite**: Build tool e dev server
- **Tailwind CSS**: Framework CSS
- **Chart.js**: Visualização de dados

### Landing Page
- **HTML5/CSS3**: Estrutura e estilos
- **JavaScript**: Interatividade
- **Font Awesome**: Ícones
- **Google Fonts**: Tipografia
- **Chrome Headless**: Geração de PDF

## 🎯 **Especializações do xAI Grok**

O ClimateWise integra o xAI Grok configurado como **especialista em seguros paramétricos e atuária brasileira**, com conhecimento profundo das normas da SUSEP e do histórico climático nacional dos últimos 30 anos.

### 🛡️ Seguros Paramétricos
- Análise de viabilidade de produtos paramétricos
- Definição de triggers automáticos baseados em índices climáticos
- Cálculo de pay-outs automáticos
- Redução de custos administrativos (até 70%)

### ⚖️ Normas da SUSEP
- **Circular 562/2015**: Seguros paramétricos
- **Circular 591/2016**: Seguros agrícolas
- **Circular 269/2004**: Contratos de seguro
- **Circular 302/2005**: Resseguro
- **Circular 347/2007**: Responsabilidade civil

### 🧮 Cálculos Atuariais
- Princípios atuariais: Equivalência, Suficiência, Adequação
- Cálculo de prêmios baseado em probabilidade de sinistros
- Reserva matemática e provisões técnicas
- Taxa de juros técnica (i) e taxa de desconto
- Valor presente dos fluxos de caixa

### 🌡️ Histórico Climático Brasileiro (1994-2024)
- **Região Norte**: Acre (+15% precipitação), Amazonas (+1.2°C), Pará (+20% dias >50mm)
- **Região Nordeste**: Ceará (+25% secas extremas), Bahia (+1.5°C), Pernambuco (+30% chuvas intensas)
- **Região Centro-Oeste**: Mato Grosso (+18% safra), Mato Grosso do Sul (+1.3°C), Goiás (+22% granizo)
- **Região Sudeste**: São Paulo (+15% chuvas extremas), Rio de Janeiro (+1.4°C), Minas Gerais (+20% variabilidade)
- **Região Sul**: Rio Grande do Sul (+25% granizo), Santa Catarina (+1.1°C), Paraná (+18% precipitação invernal)

### 📊 Endpoints Especializados
```bash
# Análise paramétrica
POST /api/v1/grok/parametric-insurance

# Cálculos atuariais
POST /api/v1/grok/actuarial-calculation

# Insights especializados
POST /api/v1/grok/insights
```

## 🌊 **Integração com NOAA (National Oceanic and Atmospheric Administration)**

O ClimateWise integra dados oficiais do NOAA para fornecer informações climáticas precisas e históricas.

### 📊 **Dados Climáticos Disponíveis**
- **Temperatura**: Máxima, mínima e média diária
- **Precipitação**: Quantidade de chuva e neve
- **Ventos**: Velocidade e direção dos ventos
- **Umidade**: Dados de umidade relativa

### 🌤️ **Previsão do Tempo**
- Previsões do National Weather Service (NWS)
- Alertas meteorológicos e avisos
- Dados em tempo real para qualquer localização

### 📈 **Datasets NOAA Integrados**
- **GHCND**: Global Historical Climatology Network Daily
- **NEXRAD**: Next Generation Weather Radar
- **GOES**: Geostationary Operational Environmental Satellite

### 🔧 **Endpoints NOAA**
```bash
# Dados climáticos históricos
POST /api/v1/noaa/climate-data

# Previsão do tempo
POST /api/v1/noaa/weather-forecast

# Status da integração
GET /api/v1/noaa/status

# Tipos de dados disponíveis
GET /api/v1/noaa/data-types
```

## 📁 **Estrutura do Projeto**

```
ClimateWise/
├── client/                 # Frontend React/Vite
│   ├── src/
│   ├── public/
│   └── package.json
├── server/                 # Backend FastAPI
│   ├── api/
│   ├── services/
│   ├── models/
│   └── main.py
├── landing-page.html       # Landing page autônoma
├── landing-page.pdf        # PDF gerado automaticamente
├── start_platform.sh       # Script para iniciar tudo
├── stop_platform.sh        # Script para parar tudo
├── status_platform.sh      # Verificar status
├── generate_pdf.sh         # Gerar PDF da landing page
└── README.md              # Esta documentação
```

## 🔧 **Instalação e Configuração**

### Pré-requisitos
- Python 3.8+
- Node.js 18+
- Google Chrome (para geração de PDF)

### Instalação
```bash
# Clonar repositório
git clone https://github.com/leanderdulac/ClimateWise.git
cd ClimateWise

# Instalar dependências do backend (perfil padrão: produção com PyTorch, sem TensorFlow)
cd server
pip install -r requirements-prod-ml.txt
# Opções:
#   - Leve, sem ML pesado: pip install -r requirements-base.txt
#   - Desenvolvimento com TensorFlow: pip install -r requirements-base.txt -r requirements-ml.txt

# Instalar dependências do frontend
cd ../client
npm install

# Voltar para raiz
cd ..
```

### Configuração
1. Verificar configurações em `server/config/config.py`
2. Configurar APIs externas (Embrapa, OpenMeteo)
3. Ajustar portas se necessário

## 🤝 **Contribuição**

### CI/CD Pipeline
O projeto utiliza GitHub Actions para CI/CD automatizado:

- **Build**: Compilação e testes automatizados
- **Security**: Varredura de vulnerabilidades com Trivy
- **Quality**: Análise de código com flake8, black, isort
- **Docker**: Build e push de imagens
- **Deploy**: Implantação automatizada

### Testes
```bash
# Executar todos os testes
cd server
pytest

# Com cobertura
pytest --cov=.

# Testes de performance
./run_performance_tests.sh
```

### Monitoramento
```bash
# Iniciar stack de monitoramento
./start_monitoring.sh

# Acessar dashboards
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# Kibana: http://localhost:5601
```

## 📄 **Licença**

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 **Contato**

**ClimateWise Team**
- GitHub: [@leanderdulac](https://github.com/leanderdulac)
- Projeto: [ClimateWise](https://github.com/leanderdulac/ClimateWise)

---

**🌟 Framework Integrado de Modelagem Climático-Econômica - Transformando riscos climáticos em oportunidades de negócio**
- **Animações Suaves**: Transições e efeitos visuais modernos
- **SEO Otimizado**: Meta tags e estrutura semântica

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
cp server/.env.example server/.env
# Edite server/.env com suas chaves de API
```

#### Configuração das APIs

**Embrapa Climate API** (Dados históricos e previsões):
- URL da API: `https://api.cnptia.embrapa.br/climapi/v1`
- Para obter acesso, visite: https://www.embrapa.br/
- Configure as seguintes variáveis no arquivo `.env`:
  - `EMBRAPA_API_URL=https://api.cnptia.embrapa.br`
  - `EMBRAPA_API_VERSION=climapi/v1`
  - `EMBRAPA_API_KEY=sua_chave_aqui`
- **Fallback automático**: Se a API Embrapa estiver indisponível, o sistema automaticamente usa OpenMeteo como alternativa

**OpenMeteo API** (Previsões alternativas):
- Gratuita, não requer chave de API
- Usada automaticamente como fallback para previsões climáticas

**Outras configurações**:
- `HOST`: Endereço do servidor (padrão: 0.0.0.0)
- `PORT`: Porta do servidor (padrão: 8000)
- `DEBUG`: Modo de desenvolvimento (padrão: true)

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

### Endpoints Principais

#### Dados Climáticos
- `GET /api/v1/clima/historico` - **Embrapa**: Dados climáticos históricos (30+ anos)
- `GET /api/v1/clima/previsao` - **OpenMeteo**: Previsão climática (7-15 dias)
- `GET /api/v1/clima/atual` - Condições climáticas atuais

#### Cálculos Atuariais
- `POST /api/v1/clima/calculo-avancado-premio` - Cálculo atuarial com técnicas avançadas:
  - Análise fractal de padrões climáticos
  - Simulação Monte Carlo (50k iterações)
  - Lógica fuzzy para avaliação de risco
  - Física estatística para sistemas complexos

#### Outros
- `GET /api/v1/eventos` - Eventos climáticos detectados
- `GET /api/v1/modelagem/previsao-precos` - Previsão de preços de commodities
- `GET /api/v1/alertas` - Sistema de alertas
- `GET /api/v1/localizacao` - Serviços de geocodificação

## 📊 Funcionalidades

1. **Seleção de Localização**: Escolha de coordenadas para análise climática
2. **Visualização de Dados Climáticos**: Séries históricas e previsões
3. **Simulador de Preços**: Modelagem do impacto climático nos preços
4. **Tokenização de Eventos**: Mecanismo para criar tokens representando eventos climáticos
5. **Monitoramento de Contratos Inteligentes**: Rastreamento de contratos baseados em eventos climáticos
