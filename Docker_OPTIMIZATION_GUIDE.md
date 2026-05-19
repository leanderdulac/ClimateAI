# Guia de Otimização do Docker para ClimateWise

## Visão Geral

Este guia descreve as otimizações realizadas nas imagens Docker do ClimateWise para melhorar desempenho, segurança e eficiência de recursos.

## Otimizações Realizadas

### 1. Multi-stage Builds

- **Antes**: Imagem única com todas as dependências
- **Depois**: Estágios distintos para desenvolvimento e produção
- **Benefício**: Imagens menores para produção, mantendo flexibilidade para desenvolvimento

### 2. Camadas de Cache Eficientes

- Cópia de `requirements.txt` e `package.json` antes do código fonte
- Isolamento de dependências que mudam com menos frequência
- **Benefício**: Melhor aproveitamento do cache do Docker, builds mais rápidos

### 3. Segurança

- Uso de usuário não-root (`appuser`)
- Imagens base mais leves (`slim`, `alpine`)
- Remoção de pacotes desnecessários após instalação
- **Benefício**: Superfície de ataque reduzida

### 4. Tamanho da Imagem

- Uso de `--no-cache-dir` para pip
- Limpeza de caches e listas de pacotes
- Uso de imagens Alpine para frontend
- **Benefício**: Imagens menores, menor tempo de pull

### 5. Recursos e Performance

- Configuração de health checks adequados
- Limites de memória para Redis
- Workers configuráveis para uvicorn
- **Benefício**: Monitoramento melhorado, uso eficiente de recursos

## Arquivos Criados

### Server
- `Dockerfile.optimized` - Nova imagem otimizada com estágios de produção e desenvolvimento

### Client
- `Dockerfile.client.optimized` - Imagem otimizada para o frontend

### Orquestração
- `docker-compose.optimized.yml` - Configuração otimizada para produção

## Como Usar

### Para Produção
```bash
# Backend
docker build -f Dockerfile.optimized --target production -t climatewise/backend:prod .

# Frontend
docker build -f Dockerfile.client.optimized -t climatewise/frontend:prod .

# Compose
docker compose -f docker-compose.optimized.yml up -d
```

### Para Desenvolvimento
```bash
# Backend
docker build -f Dockerfile.optimized --target development -t climatewise/backend:dev .

# Compose com modo dev
docker compose -f docker-compose.optimized.yml --profile dev up
```

## Melhorias de Segurança

1. **Não-root User**: Todas as aplicações rodam como usuário não-root
2. **Imagens Leves**: Uso de imagens slim/alpine para reduzir superfície de ataque
3. **Health Checks**: Verificação de integridade da aplicação
4. **Resource Limits**: Configuração de limites de memória e CPU

## Melhorias de Performance

1. **Multi-stage Builds**: Separação de dependências de build e runtime
2. **Cache Eficiente**: Estratégia de cache otimizada para builds rápidos
3. **Configuração de Workers**: Ajuste de workers do uvicorn para melhor throughput
4. **Otimização de Pip**: Uso de opções de pip para builds mais rápidos

## Boas Práticas Implementadas

- `.dockerignore` para excluir arquivos desnecessários
- Labels descritivas para identificação da imagem
- Configuração de logging estruturado
- Volumes nomeados para persistência de dados
- Networks isoladas para segurança

## Monitoramento

- Health checks configurados para todos os serviços
- Configuração de logging estruturado
- Métricas de desempenho configuradas

## Próximos Passos

1. Implementar scanning de vulnerabilidades nas imagens
2. Configurar CI/CD para builds automatizados
3. Implementar políticas de retenção de imagens
4. Configurar orquestração com Kubernetes para ambientes de produção
