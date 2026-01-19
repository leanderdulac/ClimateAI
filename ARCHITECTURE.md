# Documentação Técnica do ClimateAI

## Visão Geral

ClimateAI é uma plataforma full-stack para análise e previsão de dados climáticos, utilizando inteligência artificial e machine learning para fornecer insights e modelos preditivos avançados.

## Arquitetura

### Frontend (Client)
- **Framework**: React 18 com TypeScript
- **Estilização**: Tailwind CSS com Radix UI para componentes acessíveis
- **Roteamento**: React Router DOM
- **Visualizações**: Recharts para gráficos, Leaflet para mapas interativos
- **HTTP Client**: Axios para requisições à API
- **Build Tool**: Vite

### Backend (Server)
- **Framework Web**: FastAPI
- **Modelagem de Dados**: Pydantic para validação
- **Banco de Dados**: PostgreSQL com SQLAlchemy ORM
- **Cache**: Redis
- **Machine Learning**: PyTorch para modelos LSTM com atenção
- **Autenticação**: JWT tokens com python-jose
- **Logging**: python-json-logger para logs estruturados

## Estrutura de Diretórios

```
climateAI/
├── client/                 # Código-fonte do frontend
│   ├── src/
│   │   ├── components/     # Componentes React reutilizáveis
│   │   ├── pages/          # Páginas da aplicação
│   │   ├── hooks/          # Hooks customizados
│   │   ├── services/       # Serviços de API
│   │   └── utils/          # Funções utilitárias
│   ├── public/
│   └── package.json
├── server/                 # Código-fonte do backend
│   ├── main.py            # Ponto de entrada da aplicação FastAPI
│   ├── api/               # Definições de endpoints
│   ├── models/            # Modelos de dados do SQLAlchemy
│   ├── schemas/           # Esquemas Pydantic
│   ├── database/          # Configuração do banco de dados
│   ├── ml/                # Modelos e funções de machine learning
│   ├── auth/              # Funcionalidades de autenticação
│   └── requirements*.txt  # Dependências
├── docker-compose*.yml    # Configurações Docker
└── .github/workflows/     # Workflows CI/CD
```

## Componentes Principais

### Backend

#### API Endpoints
- `/api/v1/users/` - Gerenciamento de usuários
- `/api/v1/climate/` - Dados e previsões climáticas
- `/api/v1/ml/` - Modelos e inferências de ML
- `/api/v1/auth/` - Autenticação e autorização

#### Machine Learning
- **Modelos LSTM com Mecanismo de Atenção** para previsão temporal
- **PyTorch** como framework principal
- **Scikit-learn** para pré-processamento e validação
- **OpenMeteo** para obtenção de dados meteorológicos

#### Banco de Dados
- **PostgreSQL** como banco de dados principal
- **SQLAlchemy** como ORM
- **Alembic** para migrações de banco de dados
- **AsyncPG** para operações assíncronas

### Frontend

#### Componentes de UI
- **Radix UI Primitives** para componentes acessíveis
- **Recharts** para visualização de dados
- **Leaflet + React-Leaflet** para mapas interativos
- **Lucide React** para ícones

#### Gerenciamento de Estado
- **React Router DOM** para navegação
- **Axios** para comunicação com a API
- **React Query** (ou SWR) para gerenciamento de dados remotos

## Segurança

### Autenticação
- JWT tokens com expiração configurável
- Hash de senhas com bcrypt
- Middleware de autenticação para proteger endpoints

### Proteção contra Ataques
- Validação rigorosa de entrada com Pydantic
- CORS configurado para domínios específicos
- Rate limiting para proteção contra DDoS

## Configuração de Ambientes

### Variáveis de Ambiente
- `DATABASE_URL` - String de conexão com o banco de dados
- `REDIS_URL` - URL de conexão com o Redis
- `SECRET_KEY` - Chave secreta para JWT
- `OPENMETEO_API_KEY` - Chave de API para OpenMeteo
- `GOOGLE_GEMINI_API_KEY` - Chave de API para Google Gemini

## Deployment

### Docker
- Imagens otimizadas com multi-stage build
- Separação de frontend e backend em containers distintos
- Configuração para produção e desenvolvimento

### CI/CD
- Testes automatizados em cada push
- Varredura de segurança
- Deployment automático para staging e produção

## Monitoramento e Logging

### Logs
- Logs estruturados em formato JSON
- Níveis de log configuráveis
- Integração com sistemas de log externos

### Health Checks
- Endpoints de health check para monitoramento
- Verificação de conectividade com serviços dependentes

## Melhores Práticas

### Código
- Tipagem estática com TypeScript e Pydantic
- Cobertura de testes >80%
- Linting e formatação automática
- Documentação inline e JSDoc/Docstrings

### Segurança
- Varreduras de dependências regulares
- Atualizações de segurança automáticas
- Princípio do menor privilégio para permissões

## Escalabilidade

### Backend
- Design assíncrono com FastAPI
- Cache com Redis para operações frequentes
- Filas de tarefas para processos demorados

### Frontend
- Code splitting para carregamento otimizado
- Lazy loading de componentes
- Caching de requisições HTTP
