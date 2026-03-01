# Atlas Digital de Desastres - Documentação

## Visão Geral

O módulo **Atlas Digital de Desastres** integra dados do Atlas Digital de Desastres Naturais do Brasil ao sistema ClimateWise, proporcionando análises históricas, estatísticas e visualizações sobre desastres naturais ocorridos no território nacional.

## Fontes de Dados

- **Atlas Digital de Desastres Naturais (1991-2024)** - MDR (Ministério do Desenvolvimento Regional)
- Dados abertos do governo federal sobre desastres naturais
- Integrado com múltiplas fontes de alertas (CEMADEN, INMET, CPTEC)

## Arquitetura

```
server/
├── api/
│   └── atlas_disasters.py       # Router da API FastAPI
├── services/
│   ├── atlas_disaster_service.py       # Lógica de negócio
│   └── atlas_visualization_service.py  # Visualizações e gráficos
├── models/
│   └── schemas.py              # Schemas Pydantic (Atlas*)
├── tests/
│   ├── test_atlas_disaster_service.py  # Testes unitários
│   └── test_atlas_api.py               # Testes de API
└── data/
    └── atlas/                  # Dados baixados e visualizações
```

## Instalação

### Dependências Adicionais

Para funcionalidades completas de visualização:

```bash
pip install matplotlib plotly pandas numpy requests
```

### Configuração

1. Configure a URL dos dados no serviço ou via API:

```python
# URL do arquivo CSV/Excel do Atlas Digital
DATA_URL = "https://atlasdigital.mdr.gov.br/downloads/atlas_desastres_1991_2024.csv"
```

2. O diretório padrão para dados é `server/data/atlas/`

## API Endpoints

### Base URL
```
/api/v1/atlas
```

### Gestão de Dados

#### Download de Dados
```http
POST /api/v1/atlas/download
Content-Type: application/json

{
    "url": "https://exemplo.com/dados.csv",
    "filename": "atlas_2024.csv",
    "force": false
}
```

**Resposta:**
```json
{
    "status": "success",
    "filepath": "/path/to/data/atlas/atlas_2024.csv",
    "message": "Download realizado com sucesso"
}
```

#### Status dos Dados
```http
GET /api/v1/atlas/status
```

**Resposta:**
```json
{
    "arquivo_carregado": "/path/to/atlas_desastres.csv",
    "total_registros": 50000,
    "cache_timestamp": "2024-01-15T10:30:00",
    "data_dir": "/path/to/data/atlas"
}
```

#### Recarregar Dados
```http
GET /api/v1/atlas/reload
```

### Consulta de Dados

#### Listar Registros (Paginado)
```http
GET /api/v1/atlas/records?limit=100&offset=0
```

#### Filtrar Desastres (POST)
```http
POST /api/v1/atlas/filter
Content-Type: application/json

{
    "anos": [2000, 2024],
    "uf": "RS",
    "municipio": "Porto Alegre",
    "tipo_desastre": "inundacao",
    "intensidade": "alta",
    "min_afetados": 100,
    "min_mortes": 5
}
```

**Resposta:**
```json
{
    "total": 150,
    "filters_applied": {...},
    "data": [...]
}
```

#### Filtrar Desastres (GET Simplificado)
```http
GET /api/v1/atlas/filter/simple?ano_inicio=2000&ano_fim=2024&uf=RS&tipo_desastre=inundacao&min_afetados=100
```

### Agregações e Estatísticas

#### Agregar por Município
```http
POST /api/v1/atlas/aggregate/municipality
Content-Type: application/json

{
    "group_cols": ["uf", "municipio", "tipo_desastre"]
}
```

#### Agregar por Ano
```http
GET /api/v1/atlas/aggregate/year?group_by_uf=false
```

#### Estatísticas Descritivas
```http
GET /api/v1/atlas/statistics
```

**Resposta:**
```json
{
    "total_registros": 50000,
    "periodo": {
        "inicio": 1991,
        "fim": 2024,
        "anos_unicos": 34
    },
    "uf": {
        "total_estados": 27,
        "mais_afetado": "RS"
    },
    "tipos_desastre": {
        "total_tipos": 8,
        "mais_comum": "Inundação",
        "top_5": {"Inundação": 15000, "Seca": 12000, ...}
    },
    "impacto": {
        "mortes_diretas": {"total": 5000, "media": 0.1, "max": 500},
        "afetados": {"total": 5000000, "media": 100, "max": 50000}
    }
}
```

### Análise

#### Top Municípios Mais Afetados
```http
GET /api/v1/atlas/analysis/top-affected?limit=20&metric=qtd_ocorrencias
```

**Métricas disponíveis:**
- `qtd_ocorrencias` - Número de ocorrências
- `total_afetados` - Total de pessoas afetadas
- `total_mortes` - Total de mortes

#### Tendências Temporais
```http
GET /api/v1/atlas/analysis/trends
```

**Resposta:**
```json
{
    "evolucao_anual": [
        {"ano": 2000, "qtd_ocorrencias": 1200, "crescimento": 5.2, ...},
        ...
    ],
    "estatisticas": {
        "media_anual": 1500,
        "desvio_padrao": 200,
        "ano_max": 2024,
        "ano_min": 1991
    }
}
```

#### Análise por Tipo de Desastre
```http
GET /api/v1/atlas/analysis/by-disaster-type
```

### Exportação

#### Exportar para CSV
```http
POST /api/v1/atlas/export/csv
Content-Type: application/json

{
    "filename": "atlas_rs_inundacoes.csv"
}
```

#### Baixar CSV Exportado
```http
GET /api/v1/atlas/export/csv/atlas_rs_inundacoes.csv
```

### Visualizações

#### Gráfico de Série Temporal
```http
GET /api/v1/atlas/visualizations/timeseries?chart_type=line&group_by=uf&return_base64=true
```

**Parâmetros:**
- `chart_type`: `line`, `bar`, `area`
- `group_by`: Coluna para agrupamento (ex: `uf`, `tipo_desastre`)
- `return_base64`: `true` para retornar imagem codificada

#### Mapa de Calor por UF
```http
GET /api/v1/atlas/visualizations/map?return_base64=true
```

#### Gráfico de Pizza por Tipo
```http
GET /api/v1/atlas/visualizations/pie-chart?return_base64=true
```

#### Análise de Impacto
```http
GET /api/v1/atlas/visualizations/impact-analysis?return_base64=true
```

#### Dashboard Completo
```http
POST /api/v1/atlas/visualizations/dashboard
Content-Type: application/json

{
    "save_name": "dashboard_completo.html"
}
```

#### Gerar Todas as Visualizações
```http
POST /api/v1/atlas/visualizations/generate-all
Content-Type: application/json

{
    "prefix": "atlas"
}
```

## Tipos de Desastres Suportados

O sistema reconhece e mapeia automaticamente os seguintes tipos:

| Tipo | Sinônimos |
|------|-----------|
| `inundacao` | inundação, enchente, alagamento |
| `seca` | estiagem, secas |
| `deslizamento` | movimento de massa, rolagem de barro |
| `granizo` | queda de granizo |
| `vendaval` | vento forte, ciclone, tornado |
| `incendio` | incêndio, queimada |
| `geada` | geada, granizo |
| `aluviao` | aluviação, enxurrada |

## Exemplos de Uso

### Python (Cliente)

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/atlas"

# 1. Verificar status
status = requests.get(f"{BASE_URL}/status")
print(status.json())

# 2. Filtrar dados do RS (2000-2024)
response = requests.post(
    f"{BASE_URL}/filter",
    json={
        "anos": [2000, 2024],
        "uf": "RS",
        "tipo_desastre": "inundacao"
    }
)
dados = response.json()
print(f"Total de ocorrências: {dados['total']}")

# 3. Obter estatísticas
stats = requests.get(f"{BASE_URL}/statistics")
print(stats.json())

# 4. Gerar gráfico de série temporal
chart = requests.get(
    f"{BASE_URL}/visualizations/timeseries",
    params={"chart_type": "line", "group_by": "uf"}
)
# chart.json()['data'] contém a imagem em base64

# 5. Exportar dados filtrados
export = requests.post(
    f"{BASE_URL}/export/csv",
    json={"filename": "rs_inundacoes.csv"}
)
print(f"Arquivo exportado: {export.json()['filepath']}")
```

### cURL

```bash
# Status
curl http://localhost:8000/api/v1/atlas/status

# Filtrar dados
curl -X POST http://localhost:8000/api/v1/atlas/filter \
  -H "Content-Type: application/json" \
  -d '{"anos": [2000, 2024], "uf": "RS", "tipo_desastre": "inundacao"}'

# Estatísticas
curl http://localhost:8000/api/v1/atlas/statistics

# Gerar dashboard
curl -X POST http://localhost:8000/api/v1/atlas/visualizations/dashboard \
  -H "Content-Type: application/json" \
  -d '{"save_name": "dashboard.html"}'
```

## Testes

### Executar Testes Unitários

```bash
# Testes do serviço
pytest server/tests/test_atlas_disaster_service.py -v

# Testes da API
pytest server/tests/test_atlas_api.py -v

# Todos os testes do módulo
pytest server/tests/test_atlas*.py -v
```

### Cobertura de Testes

Os testes cobrem:
- Download e carregamento de dados
- Filtragem por múltiplos critérios
- Agregações (município, ano, tipo)
- Cálculo de estatísticas
- Exportação para CSV
- Validação de schemas
- Tratamento de erros
- Casos extremos (dataframes vazios, colunas faltantes)

## Estrutura de Dados

### Schema de Entrada (AtlasFilterRequest)

```python
{
    "anos": [2000, 2024],      # Tupla (ano_inicial, ano_final)
    "uf": "RS",                 # Sigla da UF
    "municipio": "Porto Alegre", # Nome do município
    "tipo_desastre": "inundacao", # Tipo de desastre
    "intensidade": "alta",       # Nível de intensidade
    "min_afetados": 100,         # Mínimo de afetados
    "min_mortes": 5              # Mínimo de mortes
}
```

### Schema de Saída (AtlasDisasterRecord)

```python
{
    "record_id": "12345",
    "ano": 2024,
    "uf": "RS",
    "municipio": "Porto Alegre",
    "codigo_municipio": "4314902",
    "tipo_desastre": "Inundação",
    "subtipo_desastre": "Cheia",
    "data_inicio": "2024-01-15",
    "data_fim": "2024-01-20",
    "intensidade": "Alta",
    "mortes_diretas": 5,
    "mortes_indiretas": 2,
    "feridos": 15,
    "desabrigados": 500,
    "desalojados": 2000,
    "afetados": 10000,
    "prejuizo_estimado": 5000000.0,
    "latitude": -30.0346,
    "longitude": -51.2177
}
```

## Integração com Outros Módulos

### Brazil Disaster Alerts

O módulo Atlas complementa o sistema de alertas:

```python
# Alertas em tempo real (brazil-alerts)
GET /api/v1/brazil-alerts/fetch

# Dados históricos (atlas)
GET /api/v1/atlas/filter?uf=RS&tipo_desastre=inundacao
```

### Climate Data

Integração com dados climáticos:

```python
# Dados climáticos históricos
GET /api/v1/climate/historico?latitude=-30&longitude=-51

# Cruzar com dados do Atlas
POST /api/v1/atlas/filter
```

## Performance e Cache

- **Cache em memória**: Dados carregados são cacheados por 60 minutos
- **Paginação**: Endpoints de listagem suportam paginação (limit/offset)
- **Lazy loading**: Visualizações são geradas sob demanda

## Segurança

- Rate limiting aplicado via middleware global
- Validação de entrada com Pydantic
- Sanitização de paths de arquivo
- Logs estruturados de operações

## Troubleshooting

### Erro: "Dados não encontrados"

**Solução:** Faça upload/download dos dados primeiro:
```bash
POST /api/v1/atlas/download
{"url": "https://seu-link.com/dados.csv"}
```

### Erro: "Serviço de visualização não disponível"

**Solução:** Instale as dependências:
```bash
pip install matplotlib plotly
```

### Erro: "Coluna 'ano' não encontrada"

**Solução:** Verifique o formato do arquivo CSV. Colunas esperadas:
- `ano`, `year`, `data_ano`
- `uf`, `estado`, `sigla_uf`
- `municipio`, `municip`, `nome_municipio`
- `tipo_desastre`, `tipo`, `desastre_tipo`

## Próximos Passos

1. **Integração com Banco de Dados**: Persistência em PostgreSQL
2. **Georreferenciamento**: Mapas interativos com coordenadas
3. **Machine Learning**: Modelos preditivos baseados em dados históricos
4. **Relatórios PDF**: Geração automática de relatórios técnicos
5. **Webhooks**: Notificações em tempo real para novos dados

## Referências

- [Atlas Digital de Desastres Naturais - MDR](http://atlasdigital.mdr.gov.br/)
- [CEMADEN - Centro Nacional de Monitoramento](http://www.cemaden.gov.br/)
- [INMET - Instituto Nacional de Meteorologia](https://portal.inmet.gov.br/)
- [ClimateWise Documentation](../README.md)

## Licença

Este módulo segue a licença do projeto ClimateWise principal.
