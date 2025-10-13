"""
Router para endpoints de modelagem econômica
"""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional, Dict
from datetime import datetime
from models.schemas import PrevisaoPreco
from services.modelagem_service import ModelagemService

router = APIRouter()
modelagem_service = ModelagemService()


@router.get("/previsao-precos", response_model=List[PrevisaoPreco])
async def get_previsao_precos(
    simbolos: List[str] = Query(..., description="Símbolos de commodities"),
    latitude: Optional[float] = Query(None, ge=-90, le=90),
    longitude: Optional[float] = Query(None, ge=-180, le=180),
    dias: int = Query(30, ge=1, le=90)
):
    """
    Obter previsões de preços de commodities considerando fatores climáticos
    """
    try:
        # Gera chave de cache baseada nos parâmetros
        cache_key = smart_cache._generate_key({
            'simbolos': sorted(simbolos),
            'latitude': latitude,
            'longitude': longitude,
            'dias': dias
        })

        # Verifica cache
        cached_result = smart_cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Executa cálculo se não estiver em cache
        result = modelagem_service.obter_previsao_precos(
            simbolos=simbolos,
            latitude=latitude,
            longitude=longitude,
            dias=dias
        )

        # Armazena no cache (TTL: 30 minutos para dados de commodities)
        smart_cache.set(cache_key, result, 1800)
        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/impacto-climatico", response_model=List[Dict])
async def get_impacto_climatico(
    simbolo: str = Query(...),
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    periodo: int = Query(30, ge=1, le=365)
):
    """
    Obter análise de impacto climático sobre o preço de uma commodity
    """
    try:
        # Gera chave de cache baseada nos parâmetros
        cache_key = smart_cache._generate_key({
            'simbolo': simbolo,
            'latitude': latitude,
            'longitude': longitude,
            'periodo': periodo
        })

        # Verifica cache
        cached_result = smart_cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Executa cálculo se não estiver em cache
        result = modelagem_service.obter_impacto_climatico(
            simbolo=simbolo,
            latitude=latitude,
            longitude=longitude,
            periodo=periodo
        )

        # Armazena no cache (TTL: 15 minutos para análises de impacto)
        smart_cache.set(cache_key, result, 900)
        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ml-sinistrality-prediction")
async def predict_sinistrality_ml(
    features: Dict,
    use_cache: bool = Query(True, description="Usar cache para resultados")
):
    """
    Prediz sinistralidade usando machine learning

    Args:
        features: Características para predição ML
        use_cache: Se deve usar cache (padrão: True)

    Returns:
        Predições de frequência e severidade
    """
    try:
        from services.ml_service import predict_sinistrality

        # Gera chave de cache
        cache_key = smart_cache._generate_key(features) if use_cache else None

        # Verifica cache se habilitado
        if use_cache and cache_key:
            cached_result = smart_cache.get(cache_key)
            if cached_result is not None:
                return cached_result

        # Executa predição ML
        result = predict_sinistrality(features)

        # Armazena no cache se habilitado (TTL: 1 hora para predições ML)
        if use_cache and cache_key:
            smart_cache.set(cache_key, result, 3600)

        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro na predição ML: {str(e)}")


@router.post("/derivativos-climaticos/preco")
async def price_climate_derivative(
    target_year: int = Query(2025, ge=2020, le=2050, description="Ano alvo para precificação"),
    iam_adjustment: float = Query(0.5, ge=0, le=5, description="Ajuste IAM em °F"),
    months_to_expiry: float = Query(3, ge=0.1, le=12, description="Meses até expiração"),
    scenario_name: str = Query("Base", description="Nome do cenário"),
    base_temp: float = Query(65.0, ge=50, le=80, description="Temperatura base em °F"),
    contract_period_days: int = Query(92, ge=30, le=365, description="Período do contrato em dias"),
    payout_per_cdd: float = Query(10000, ge=1000, le=100000, description="Pagamento por CDD em $")
):
    """
    Precifica derivativos climáticos baseados em CDD (Cooling Degree Days)

    Usa Gaussian Process + Monte Carlo para modelagem de risco climático
    """
    try:
        from services.climate_derivative_pricer import ClimateDerivativePricer

        # Inicializar pricer com parâmetros customizados
        pricer = ClimateDerivativePricer(
            base_temp=base_temp,
            contract_period_days=contract_period_days,
            payout_per_cdd=payout_per_cdd
        )

        # Executar precificação
        result = pricer.price_climate_derivative(
            target_year=target_year,
            iam_adjustment=iam_adjustment,
            months_to_expiry=months_to_expiry,
            scenario_name=scenario_name
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro na precificação: {str(e)}")


@router.post("/derivativos-climaticos/comparar-cenarios")
async def compare_climate_derivative_scenarios(
    scenarios: List[Dict] = Body(..., description="Lista de cenários para comparação")
):
    """
    Compara múltiplos cenários de precificação de derivativos climáticos

    Cada cenário deve conter: target_year, iam_adjustment, months_to_expiry, scenario_name
    """
    try:
        from services.climate_derivative_pricer import ClimateDerivativePricer

        pricer = ClimateDerivativePricer()

        # Validar cenários
        for scenario in scenarios:
            required_fields = ['target_year', 'iam_adjustment', 'months_to_expiry', 'scenario_name']
            for field in required_fields:
                if field not in scenario:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Campo obrigatório '{field}' ausente no cenário"
                    )

        result = pricer.compare_scenarios(scenarios)
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro na comparação de cenários: {str(e)}")


@router.get("/derivativos-climaticos/analise-risco")
async def get_risk_analysis(
    target_year: int = Query(2025, ge=2020, le=2050),
    iam_adjustment: float = Query(0.5, ge=0, le=5),
    confidence_levels: List[float] = Query([0.95, 0.99], description="Níveis de confiança para VaR/CVaR")
):
    """
    Análise de risco detalhada para derivativos climáticos
    """
    try:
        from services.climate_derivative_pricer import ClimateDerivativePricer

        pricer = ClimateDerivativePricer()

        # Executar precificação completa
        result = pricer.price_climate_derivative(
            target_year=target_year,
            iam_adjustment=iam_adjustment
        )

        # Extrair métricas de risco específicas
        risk_analysis = {
            'scenario': result['scenario'],
            'expected_payout': result['risk_metrics']['expected_payout'],
            'volatility': result['risk_metrics']['std_payout'],
            'var_cvar': {}
        }

        # Calcular VaR e CVaR para diferentes níveis de confiança
        payouts = np.random.normal(
            result['risk_metrics']['expected_payout'],
            result['risk_metrics']['std_payout'],
            pricer.n_simulations
        )

        for conf_level in confidence_levels:
            var = np.percentile(payouts, (1 - conf_level) * 100)
            cvar = payouts[payouts >= var].mean()

            risk_analysis['var_cvar'][f'{int(conf_level*100)}%'] = {
                'var': var,
                'cvar': cvar
            }

        return risk_analysis

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro na análise de risco: {str(e)}")


@router.post("/derivativos-climaticos/analise-capital")
async def analyze_capital_requirements(
    ask_price: float = Body(..., ge=0, description="Preço de venda do contrato"),
    initial_capital: float = Body(1000000, ge=0, description="Capital inicial disponível"),
    risk_tolerance: float = Body(0.05, ge=0, le=1, description="Tolerância ao risco (0-1)")
):
    """
    Analisa requisitos de capital e estratégias de investimento para derivativos climáticos

    Fornece insights sobre quantos contratos podem ser adquiridos e retorno esperado
    """
    try:
        from services.climate_derivative_pricer import ClimateDerivativePricer

        pricer = ClimateDerivativePricer()

        # Análise de capital
        capital_analysis = pricer.analyze_capital_requirements(ask_price, initial_capital)

        # Estratégias baseadas na tolerância ao risco
        strategies = {
            'conservative': {
                'max_contracts': min(capital_analysis['contracts_affordable'] * 0.3, 0.5),
                'description': 'Estratégia conservadora: máximo 30% do capital disponível'
            },
            'moderate': {
                'max_contracts': min(capital_analysis['contracts_affordable'] * 0.6, 1.0),
                'description': 'Estratégia moderada: até 60% do capital disponível'
            },
            'aggressive': {
                'max_contracts': min(capital_analysis['contracts_affordable'] * risk_tolerance, 2.0),
                'description': f'Estratégia agressiva: baseada na tolerância ao risco ({risk_tolerance})'
            }
        }

        # Recomendação baseada na análise
        if capital_analysis['contracts_affordable'] < 0.1:
            recommendation = "capital_insufficient"
            message = "Capital insuficiente para investimento significativo. Considere pooling de recursos."
        elif capital_analysis['contracts_affordable'] < 1.0:
            recommendation = "fractional_contract"
            message = "Capital permite investimento fracionário. Considere contratos parciais."
        else:
            recommendation = "full_contract"
            message = "Capital suficiente para contrato completo. Diversifique em múltiplos contratos."

        return {
            'capital_analysis': capital_analysis,
            'investment_strategies': strategies,
            'recommendation': {
                'type': recommendation,
                'message': message,
                'risk_assessment': 'high' if ask_price > initial_capital * 0.1 else 'moderate'
            },
            'market_context': {
                'contract_price_percentile': 'high' if ask_price > 200000000 else 'moderate',
                'volatility_adjustment': risk_tolerance,
                'liquidity_note': 'Mercado de derivativos climáticos ainda em desenvolvimento'
            }
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro na análise de capital: {str(e)}")


@router.get("/derivativos-climaticos/validacao-inmet")
async def validate_with_inmet(
    station_code: str = Query(..., description="Código da estação INMET"),
    start_date: str = Query(..., description="Data inicial (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Data final (YYYY-MM-DD)"),
    threshold_temp: float = Query(28.0, description="Temperatura limiar em °C")
):
    """
    Valida projeções climáticas com dados reais do INMET
    """
    try:
        from services.climate_derivative_pricer import ClimateDerivativePricer

        pricer = ClimateDerivativePricer()

        # Buscar dados reais do INMET
        temp_real = pricer.get_inmet_data(station_code, start_date, end_date)

        if temp_real is None:
            raise HTTPException(
                status_code=404,
                detail=f"Dados INMET não disponíveis para estação {station_code}"
            )

        # Calcular payout baseado na temperatura real
        payout = 10000 if temp_real > threshold_temp else 0

        return {
            'station_code': station_code,
            'period': {'start': start_date, 'end': end_date},
            'temperature_real': temp_real,
            'threshold_temp': threshold_temp,
            'payout': payout,
            'triggered': temp_real > threshold_temp,
            'data_source': 'INMET'
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro na validação INMET: {str(e)}")
