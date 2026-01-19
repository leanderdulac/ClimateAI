# ClimateAI - Framework Integrado de Modelagem Climático-Econômica (FIMCE)

APP Atuarial Climático que integra o Framework Integrado de Modelagem Climático-Econômica (FIMCE) para prever eventos climáticos extremos e seus impactos nos preços de commodities e mercados financeiros.

## 🌍 Visão Geral

O sistema combina:
- **Previsão Climática Avançada**: Ensemble de modelos ML + físicos para previsão meteorológica
- **Detecção de Eventos Extremos**: Identificação precoce de secas, enchentes, ondas de calor
- **Modelagem Econômica Integrada**: Impacto de eventos climáticos nos preços de commodities
- **Sistema de Alertas**: Monitoramento 24/7 com alertas automáticos
- **Tokenização de Eventos Climáticos**: Mecanismo para transformar eventos climáticos em ativos financeiros

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
- **API Backend**: http://localhost:8000/docs
- **Aplicação Frontend**: http://localhost:3000
- **Landing Page**: http://localhost:8080/landing-page.html

### **4. Gerar PDF da Landing Page**
```bash
./generate_pdf.sh
```

### **5. Parar a Plataforma**
```bash
./stop_platform.sh
```

## 🔗 **Integração Landing Page ↔ Dashboard**

### **Fluxo de Conversão Otimizado**
A landing page está totalmente integrada ao dashboard para maximizar conversões:

#### **Botões de CTA Conectados**
- **"Acessar Dashboard"**: Redireciona diretamente para `http://localhost:3000/welcome`
- **Verificação Automática**: JavaScript verifica se o dashboard está rodando
- **Fallback Inteligente**: Se dashboard offline, mostra alerta para iniciar plataforma

#### **Página de Boas-Vindas**
- **Rota `/welcome`**: Página dedicada para usuários vindos da landing page
- **Onboarding Guiado**: Explica funcionalidades principais do ClimateAI
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
- Conecta com APIs reais do ClimateAI
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
- `GET /api/v1/localizacao/cidades` - Busca de cidades brasileiras
- `GET /api/v1/localizacao/coordenadas` - Geocodificação reversa

## 🛠️ **Tecnologias Utilizadas**

### Backend
- **FastAPI**: Framework web assíncrono
- **Pandas/NumPy**: Processamento de dados
- **Scikit-learn**: Machine Learning
- **SQLAlchemy**: ORM para banco de dados
- **OpenMeteo/Embrapa**: APIs climáticas

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

## 📁 **Estrutura do Projeto**

```
ClimateAI/
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
git clone https://github.com/leanderdulac/ClimateAI.git
cd ClimateAI

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

**ClimateAI Team**
- GitHub: [@leanderdulac](https://github.com/leanderdulac)
- Projeto: [ClimateAI](https://github.com/leanderdulac/ClimateAI)

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
