# Módulo Atlas Digital de Desastres

## Instalação Rápida

```bash
# 1. Instalar dependências
pip install -r server/requirements-atlas.txt

# 2. Iniciar o servidor
cd server
uvicorn main:app --reload --port 8000

# 3. Acessar documentação Swagger
# http://localhost:8000/docs
```

## Uso Básico

### 1. Carregar Dados

```python
import requests

# Fazer download dos dados (substitua pela URL real)
response = requests.post(
    "http://localhost:8000/api/v1/atlas/download",
    json={
        "url": "https://SEU_LINK_AQUI/atlas_desastres.csv",
        "filename": "atlas_dados.csv"
    }
)
print(response.json())
```

### 2. Consultar Dados

```python
# Filtrar por UF e tipo de desastre
response = requests.post(
    "http://localhost:8000/api/v1/atlas/filter",
    json={
        "anos": [2000, 2024],
        "uf": "RS",
        "tipo_desastre": "inundacao"
    }
)
dados = response.json()
print(f"Total: {dados['total']} ocorrências")
```

### 3. Gerar Visualizações

```python
# Gerar dashboard completo
response = requests.post(
    "http://localhost:8000/api/v1/atlas/visualizations/dashboard",
    json={"save_name": "dashboard.html"}
)
print(f"Dashboard: {response.json()['dashboard_path']}")
```

## Endpoints Principais

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/status` | GET | Status dos dados carregados |
| `/download` | POST | Download de arquivo CSV/Excel |
| `/records` | GET | Listar registros (paginado) |
| `/filter` | POST | Filtrar dados com múltiplos critérios |
| `/statistics` | GET | Estatísticas descritivas |
| `/aggregate/municipality` | POST | Agregar por município |
| `/aggregate/year` | GET | Agregar por ano |
| `/visualizations/timeseries` | GET | Gráfico de série temporal |
| `/visualizations/map` | GET | Mapa de calor por UF |
| `/visualizations/dashboard` | POST | Dashboard completo |

## Executar Testes

```bash
# Testes unitários
pytest server/tests/test_atlas_disaster_service.py -v

# Testes de API
pytest server/tests/test_atlas_api.py -v

# Com cobertura
pytest server/tests/test_atlas*.py --cov=services.atlas_disaster_service --cov=api.atlas_disasters -v
```

## Estrutura de Arquivos

```
server/
├── api/
│   └── atlas_disasters.py       # API endpoints
├── services/
│   ├── atlas_disaster_service.py       # Lógica principal
│   └── atlas_visualization_service.py  # Visualizações
├── models/
│   └── schemas.py              # Pydantic models
├── tests/
│   ├── test_atlas_disaster_service.py
│   └── test_atlas_api.py
└── data/
    └── atlas/                  # Dados e visualizações
```

## Documentação Completa

Veja [docs/ATLAS_DIGITAL_DESASTRES.md](../docs/ATLAS_DIGITAL_DESASTRES.md) para documentação detalhada.

## Exemplo de Script Python

```python
#!/usr/bin/env python3
"""
Script de exemplo para uso do módulo Atlas Digital de Desastres
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1/atlas"

def main():
    # 1. Verificar status
    print("=" * 50)
    print("1. Verificando status...")
    status = requests.get(f"{BASE_URL}/status")
    print(json.dumps(status.json(), indent=2))
    
    # 2. Filtrar dados do RS (2000-2024) - Inundações
    print("\n" + "=" * 50)
    print("2. Filtrando dados do RS (inundações)...")
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
    print("\n" + "=" * 50)
    print("3. Estatísticas gerais...")
    stats = requests.get(f"{BASE_URL}/statistics")
    stats_data = stats.json()
    print(f"Total de registros: {stats_data['total_registros']}")
    print(f"Período: {stats_data['periodo']['inicio']} - {stats_data['periodo']['fim']}")
    print(f"Tipo mais comum: {stats_data['tipos_desastre']['mais_comum']}")
    
    # 4. Top 10 municípios mais afetados
    print("\n" + "=" * 50)
    print("4. Top 10 municípios mais afetados (RS)...")
    top = requests.get(
        f"{BASE_URL}/analysis/top-affected",
        params={"limit": 10, "metric": "qtd_ocorrencias"}
    )
    for i, mun in enumerate(top.json()[:10], 1):
        print(f"{i}. {mun.get('municipio', 'N/A')} - {mun.get('qtd_ocorrencias', 0)} ocorrências")
    
    # 5. Gerar visualizações
    print("\n" + "=" * 50)
    print("5. Gerando visualizações...")
    
    # Série temporal
    ts = requests.get(f"{BASE_URL}/visualizations/timeseries")
    if ts.status_code == 200:
        print("✓ Série temporal gerada")
    
    # Mapa
    mapa = requests.get(f"{BASE_URL}/visualizations/map")
    if mapa.status_code == 200:
        print("✓ Mapa de calor gerado")
    
    # Dashboard
    dashboard = requests.post(
        f"{BASE_URL}/visualizations/dashboard",
        json={"save_name": "dashboard_completo.html"}
    )
    if dashboard.status_code == 200:
        print(f"✓ Dashboard: {dashboard.json()['dashboard_path']}")
    
    print("\n" + "=" * 50)
    print("Processo concluído!")

if __name__ == "__main__":
    main()
```

## Troubleshooting

### Erro: "Dados não encontrados"
Execute o download dos dados primeiro:
```bash
curl -X POST http://localhost:8000/api/v1/atlas/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://SEU_LINK_AQUI/dados.csv"}'
```

### Erro: "Matplotlib não disponível"
Instale as dependências de visualização:
```bash
pip install matplotlib plotly openpyxl
```

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AtlasFeature`)
3. Commit suas mudanças (`git commit -m 'Add nova feature do Atlas'`)
4. Push para a branch (`git push origin feature/AtlasFeature`)
5. Abra um Pull Request

## Licença

Mesma licença do projeto ClimateWise principal.
