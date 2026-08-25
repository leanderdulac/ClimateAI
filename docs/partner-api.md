# ClimateWise Partner API

API machine-to-machine para outras plataformas integrarem clima, analytics, atlas, geo, pricing atuarial e estratégias agroclimáticas.

## URL-base

| Ambiente | Base |
|---|---|
| Local | `http://127.0.0.1:8000/api/v1/partner` |
| Produção | `https://<seu-dominio>/api/v1/partner` |

Catálogo dinâmico (sem autenticação):

```
GET /api/v1/partner/catalog
```

OpenAPI (não produção): `GET /openapi.json` — tag **Partner API**.

## Autenticação

| Item | Valor |
|---|---|
| Tipo | API Key |
| Header | `X-API-Key` |
| Desenvolvimento | `cw_dev_partner_key` (ou `PARTNER_API_KEY`) |
| Produção | chave `sk_live_*` emitida por um admin ClimateWise |

```http
GET /api/v1/partner/climate/current?lat=-23.55&lon=-46.63
X-API-Key: cw_dev_partner_key
```

JWT Bearer **não** é o método desta superfície. A API interna (`/api/v1/auth`) continua para o produto web.

## Envelope JSON

Toda resposta autenticada segue:

```json
{
  "data": {},
  "meta": {
    "updated_at": "2026-08-25T18:00:00Z",
    "observed_at": "2026-08-25T18:00:00Z",
    "generated_at": "2026-08-25T18:00:01Z",
    "source": "Open-Meteo",
    "status": "fresh",
    "stale": false,
    "unavailable": false,
    "cache_ttl_seconds": 900,
    "refresh_frequency": "15 minutes",
    "license": {
      "license": "CC BY 4.0 (via Open-Meteo)",
      "attribution": "Weather data by Open-Meteo.com",
      "url": "https://open-meteo.com/en/license"
    }
  }
}
```

`meta.status`: `fresh` | `stale` | `unavailable`.  
Quando o upstream falha, HTTP continua 200 com `status=unavailable` e `stale=true` — não inventamos número atuarial.

## Endpoints

| Método | Caminho | Descrição |
|---|---|---|
| GET | `/catalog` | Descoberta pública |
| GET | `/climate/current` | Condição atual |
| GET | `/climate/forecast` | Previsão 1–16 dias |
| GET | `/climate/history` | Histórico recente |
| GET | `/analytics/indicators` | Índices de calor, seca, inundação, vento |
| GET | `/analytics/extremes` | Eventos extremos / alertas |
| GET | `/atlas/events` | Eventos ao vivo em **GeoJSON** |
| GET | `/atlas/risk-summary` | Resumo nacional de risco |
| GET | `/geo/layers` | Catálogo XYZ / WMTS / GeoJSON |
| GET | `/geo/feature` | Ponto GeoJSON |
| GET | `/geo/satellite` | URL estática + tiles de satélite |
| POST | `/pricing/quote` | Prêmio a partir dos indicadores |
| GET | `/agri/catalog` | Culturas e estágios |
| POST | `/agri/plan` | Estratégia agroclimática |

### Exemplo — clima atual

```json
{
  "data": {
    "latitude": -23.55,
    "longitude": -46.63,
    "temperature": 27.4,
    "humidity": 61,
    "rain": 0.2,
    "wind_speed": 12.1,
    "weather_description": "Parcialmente nublado",
    "source": "Open-Meteo"
  },
  "meta": {
    "status": "fresh",
    "stale": false,
    "source": "Open-Meteo",
    "refresh_frequency": "15 minutes"
  }
}
```

### Exemplo — quote

```http
POST /api/v1/partner/pricing/quote
X-API-Key: cw_dev_partner_key
Content-Type: application/json

{
  "asset_value": 250000,
  "severity_amount": 40000,
  "frequency_pct": 12,
  "coverage_period_years": 1,
  "latitude": -23.55,
  "longitude": -46.63
}
```

## Limites e frequência

| Limite | Valor |
|---|---|
| Requisições / minuto / chave | 60 |
| Burst | 20 |
| Cota diária de referência | 10 000 |
| Clima atual | atualização ~15 min (cache) |
| Previsão | ~1 hora |
| Histórico | 24 horas |
| Atlas ao vivo | ~15 min |
| Atlas histórico MDR | diário |
| Quote / agri plan | sob demanda, sem cache de prêmio |

HTTP 429 quando o limite por minuto é excedido (`Retry-After: 60`).

## Dados geográficos

| Formato | Uso |
|---|---|
| **GeoJSON** (RFC 7946) | `/atlas/events` (FeatureCollection), `/geo/feature` (Point) |
| **XYZ** | OSM Standard `https://tile.openstreetmap.org/{z}/{x}/{y}.png` |
| **XYZ satélite** | Esri World Imagery `.../World_Imagery/MapServer/tile/{z}/{y}/{x}` |
| **WMTS** | NASA GIBS MODIS Terra True Color |
| **WMS** | não exposto nesta versão |
| **URL estática** | `/geo/satellite?lat=&lon=&zoom=` devolve `preview_url` do tile |

Polígonos: o `bbox` em `/geo/feature` é um envelope; eventos vêm como pontos. Camadas raster entram via XYZ/WMTS no cliente de mapas.

## Licença e atribuição

| Fonte | Licença | Atribuição obrigatória |
|---|---|---|
| Open-Meteo | CC BY 4.0 | Weather data by Open-Meteo.com |
| OpenStreetMap | ODbL 1.0 | © OpenStreetMap contributors |
| NASA GIBS | público NASA EOSDIS | Imagery courtesy NASA EOSDIS GIBS |
| Esri World Imagery | termos Esri | Esri, Maxar, Earthstar Geographics |
| Atlas MDR | dados abertos | Ministério da Integração e do Desenvolvimento Regional |
| Indicadores / prêmio / agro | contrato de parceria | ClimateWise / FIMCE |

Cada payload já traz `meta.license`. A plataforma consumidora **deve** exibir a atribuição das imagens e dos dados climáticos.

## Cache e indisponibilidade

- Cache interno (serviço climático ~15 min; previsão 1 h).
- `meta.stale=true` quando o valor é cache/fallback.
- `meta.status=unavailable` quando o provedor falhou — o corpo em `data.message` explica. **Não** devolvemos prêmio simulado aprovado.
- `meta.updated_at` / `observed_at` / `generated_at` separam observação da geração da resposta.

## Coleção Postman

Importe `docs/partner-api.postman.json`. Variáveis: `baseUrl`, `apiKey`.
