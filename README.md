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
- Node.js 16+
- Google Chrome (para geração de PDF)

### Instalação
```bash
# Clonar repositório
git clone https://github.com/leanderdulac/ClimateAI.git
cd ClimateAI

# Instalar dependências do backend
cd server
pip install -r requirements.txt

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

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

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
