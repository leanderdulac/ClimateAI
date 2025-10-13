"""
Router para endpoints de dados climáticos da Embrapa
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta
from models.schemas import ClimaData
from services.embrapa_service import EmbrapaAPIService
from services.openmeteo_service import OpenMeteoService
from services.advanced_actuarial_service import AdvancedActuarialService

router = APIRouter()
embrapa_service = EmbrapaAPIService()
openmeteo_service = OpenMeteoService()
advanced_actuarial_service = AdvancedActuarialService()

@router.get("/historico")
async def get_historico_clima(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    data_inicio: datetime = Query(...),
    data_fim: datetime = Query(...),
    variavel: Optional[str] = Query(None)
):
    """
    Obter dados climáticos históricos para uma localização específica usando Embrapa

    - **latitude**: Latitude do local (-90 a 90)
    - **longitude**: Longitude do local (-180 a 180)
    - **data_inicio**: Data inicial para busca dos dados
    - **data_fim**: Data final para busca dos dados
    - **variavel**: Filtrar por variável específica (opcional)
    """
    try:
        # Usar Embrapa com fallback para OpenMeteo
        dados = await embrapa_service.get_climate_data(
            latitude=latitude,
            longitude=longitude,
            start_date=data_inicio.strftime("%Y-%m-%d"),
            end_date=data_fim.strftime("%Y-%m-%d")
        )

        return {
            "dados": dados,
            "fonte": "Embrapa",
            "periodo": {
                "inicio": data_inicio.strftime("%Y-%m-%d"),
                "fim": data_fim.strftime("%Y-%m-%d")
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "erro": str(e),
                "mensagem": "Falha ao obter dados históricos",
                "sugestao": "Tente reduzir o período de busca ou usar outra fonte de dados"
            }
        )

@router.get("/atual", response_model=ClimaData)
async def get_clima_atual(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
):
    """
    Obter condições climáticas atuais para uma localização específica
    """
    try:
        # Busca dados de hoje usando OpenMeteo
        now = datetime.now()
        dados = await embrapa_service.get_climate_data(
            latitude=latitude,
            longitude=longitude,
            start_date=now.strftime("%Y-%m-%d"),
            end_date=now.strftime("%Y-%m-%d")
        )
        if not dados:
            raise HTTPException(status_code=404, detail="Dados não encontrados")
        
        # Retorna o primeiro (e único) registro
        return dados[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/previsao")
async def get_previsao_clima(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    dias: int = Query(7, ge=1, le=15)
):
    """
    Obter previsão do tempo para os próximos dias usando OpenMeteo
    """
    try:
        # Usar OpenMeteo para previsões
        dados_openmeteo = openmeteo_service.obter_previsao(
            latitude=latitude,
            longitude=longitude,
            dias=dias
        )

        # Converter para formato compatível
        previsao = []
        for dado in dados_openmeteo:
            previsao.append({
                "data": dado.data.strftime("%Y-%m-%d"),
                "temperatura_max": dado.temperatura + 5,  # Aproximação baseada na média
                "temperatura_min": dado.temperatura - 5,  # Aproximação baseada na média
                "precipitacao": dado.precipitacao,
                "probabilidade_precipitacao": dado.probabilidade_precipitacao,
                "vento_velocidade": dado.vento_velocidade,
                "vento_rajada": dado.vento_rajada,
                "vento_direcao": dado.vento_direcao,
                "fonte": "OpenMeteo"
            })

        return {
            "previsao": previsao,
            "localizacao": {
                "latitude": latitude,
                "longitude": longitude
            },
            "periodo_dias": dias,
            "fonte": "OpenMeteo"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter previsão do tempo: {str(e)}"
        )

@router.get("/zarc")
async def get_zoneamento_agricola(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    cultura: str = Query(...)
):
    """
    Obter zoneamento agrícola de risco climático
    """
    try:
        return await embrapa_service.get_agricultural_zoning(
            latitude=latitude,
            longitude=longitude,
            crop=cultura
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risco")
async def get_analise_risco(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    data_inicio: Optional[datetime] = Query(None),
    data_fim: Optional[datetime] = Query(None)
):
    """
    Obter análise de risco climático
    """
    try:
        start_date = data_inicio.strftime("%Y-%m-%d") if data_inicio else None
        end_date = data_fim.strftime("%Y-%m-%d") if data_fim else None
        
        return await embrapa_service.get_risk_analysis(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculo-avancado-premio")
async def calcular_premio_avancado(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    frequency: float = Query(..., ge=0, le=100),
    severity: float = Query(..., gt=0),
    asset_value: float = Query(..., gt=0),
    confidence_level: float = Query(95, ge=50, le=99.9),
    data_inicio: Optional[datetime] = Query(None),
    data_fim: Optional[datetime] = Query(None)
):
    """
    Cálculo avançado de prêmio usando técnicas matemáticas sofisticadas:

    - **Cálculo fratal**: Análise de padrões climáticos complexos
    - **Simulação Monte Carlo**: 50.000 iterações com distribuições adaptativas
    - **Lógica fuzzy**: Avaliação de risco com graus de pertinência
    - **Física estatística**: Modelagem de sistemas complexos
    - **Cálculos atuariais**: Prêmio puro, carregamentos e margem de risco

    - **latitude**: Latitude do local (-90 a 90)
    - **longitude**: Longitude do local (-180 a 180)
    - **frequency**: Frequência do evento (%) (0-100)
    - **severity**: Severidade máxima do evento ($)
    - **asset_value**: Valor do bem segurado ($)
    - **confidence_level**: Nível de confiança (%) (50-99.9)
    - **data_inicio**: Data inicial para dados climáticos (opcional)
    - **data_fim**: Data final para dados climáticos (opcional)
    """
    try:
        # Obter dados climáticos históricos para análise fractal
        if data_inicio and data_fim:
            start_date = data_inicio.strftime("%Y-%m-%d")
            end_date = data_fim.strftime("%Y-%m-%d")
        else:
            # Padrão: últimos 1 ano (limitação da API OpenMeteo)
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        # Buscar dados climáticos usando Embrapa
        if not embrapa_service.is_configured:
            raise HTTPException(
                status_code=503,
                detail="Serviço Embrapa não configurado para análise atuarial. Configure EMBRAPA_API_KEY no arquivo .env"
            )
        
        climate_data = await embrapa_service.get_climate_data(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date
        )

        # Calcular prêmio usando técnicas avançadas
        premium_result = advanced_actuarial_service.calculate_comprehensive_premium(
            frequency=frequency,
            severity=severity,
            asset_value=asset_value,
            confidence_level=confidence_level,
            climate_data=climate_data
        )

        return {
            "premio_puro": round(premium_result.pure_premium, 2),
            "carregamentos": round(premium_result.loading_premium, 2),
            "margem_risco": round(premium_result.risk_margin, 2),
            "premio_total": round(premium_result.total_premium, 2),
            "intervalo_confianca": {
                "inferior": round(premium_result.confidence_interval[0], 2),
                "superior": round(premium_result.confidence_interval[1], 2)
            },
            "analise_fractal": {
                "dimensao_fractal": round(premium_result.fractal_dimension.dimension, 3),
                "lacunaaridade": round(premium_result.fractal_dimension.lacunarity, 3),
                "persistencia": round(premium_result.fractal_dimension.persistence, 3)
            },
            "risco_fuzzy": {
                "muito_baixo": round(premium_result.fuzzy_risk.very_low, 3),
                "baixo": round(premium_result.fuzzy_risk.low, 3),
                "medio": round(premium_result.fuzzy_risk.medium, 3),
                "alto": round(premium_result.fuzzy_risk.high, 3),
                "muito_alto": round(premium_result.fuzzy_risk.very_high, 3)
            },
            "parametros_entrada": {
                "latitude": latitude,
                "longitude": longitude,
                "frequencia": frequency,
                "severidade": severity,
                "valor_bem": asset_value,
                "nivel_confianca": confidence_level,
                "periodo_analise": {
                    "inicio": start_date,
                    "fim": end_date
                }
            },
            "metodologia": {
                "iteracoes_monte_carlo": advanced_actuarial_service.monte_carlo_iterations,
                "tecnicas_utilizadas": [
                    "Cálculo Fratal (Box-counting)",
                    "Simulação Monte Carlo Avançada",
                    "Lógica Fuzzy",
                    "Física Estatística",
                    "Cálculos Atuariais do Setor de Seguros"
                ]
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "erro": str(e),
                "mensagem": "Falha no cálculo avançado de prêmio",
                "sugestao": "Verifique os parâmetros de entrada e tente novamente"
            }
        )
