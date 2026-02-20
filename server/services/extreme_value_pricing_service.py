
"""
Extreme Value Pricing Service
ClimateAI v2.0 - Financial Survival Architecture

Este módulo implementa a lógica de precificação baseada em Teoria de Valores Extremos (EVT),
focando na sobrevivência financeira da seguradora frente a riscos catastróficos (Cisnes Negros).

Componentes:
1. ClimateDataCleaner: Higienização de dados para evitar ruídos mas preservar extremos reais.
2. ExtremeValueTheoryModel: Modelagem GEV/GPD para caudas longas.
3. DefensivePricingOrchestrator: Arbitragem de preços com minimização de arrependimento.
4. StressTester: Simulação de cenários de ruptura climática.
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from scipy.stats import genextreme, genpareto, norm

try:
    import nolds
    NOLDS_AVAILABLE = True
except (ImportError, TypeError):
    nolds = None  # type: ignore
    NOLDS_AVAILABLE = False

# Configuração de logging
logger = logging.getLogger(__name__)

# ==============================================================================
# DATA MODELS (Schemas)
# ==============================================================================

class PricingStrategy(str, Enum):
    MARKET_COMPETITIVE = "Market Competitive (Gaussian)"
    SAFETY_FIRST = "Safety First (GEV Dominance)"
    WEIGHTED_ENSEMBLE = "Weighted Ensemble"

class RiskMetrics(BaseModel):
    return_level_100: float = Field(..., description="Nível de retorno de 100 anos")
    return_level_1000: float = Field(..., description="Nível de retorno de 1000 anos")
    max_probable_loss: float = Field(..., description="Perda máxima provável (MPL)")
    shape_parameter_xi: float = Field(..., description="Parâmetro de forma (Xi) da distribuição GEV")
    tail_volatility: float = Field(..., description="Volatilidade da cauda da distribuição")

class PricingOutput(BaseModel):
    final_premium: float
    strategy: PricingStrategy
    risk_metrics: RiskMetrics
    warnings: List[str] = []
    calculation_timestamp: datetime = Field(default_factory=datetime.now)
    divergence_factor: float = Field(..., description="Divergência percentual entre modelos")
    fractal_metrics: Optional['FractalAnalysisResult'] = Field(None, description="Métricas de análise fractal e caos")

class FractalAnalysisResult(BaseModel):
    hurst_exponent: float
    fractal_dimension: float
    regime: str
    risk_multiplier: float

class StressTestResult(BaseModel):
    scenario_name: str
    temperature_shift: float
    old_model_loss: float
    new_model_profit_or_loss: float
    solvency_maintained: bool
    details: Dict[str, float]

# ==============================================================================
# 1. ROBUST DATA CLEANER
# ==============================================================================

class ClimateDataCleaner:
    """
    Higieniza dados climáticos, removendo erros de medição impossíveis
    mas PRESERVANDO extremos genuínos.
    """
    
    MIN_POSSIBLE_TEMP = -90.0  # Antártida recorde ~ -89.2C
    MAX_POSSIBLE_TEMP = 60.0   # Vale da Morte ~ 56.7C (Margem seguranca)
    
    @staticmethod
    def clean_temperature_data(series: pd.Series) -> pd.Series:
        """
        Remove outliers físicos impossíveis (erros de sensor).
        Mantém outliers estatísticos (eventos extremos reais).
        """
        # 1. Filtro Físico Absoluto
        mask_valid = (series >= ClimateDataCleaner.MIN_POSSIBLE_TEMP) & \
                     (series <= ClimateDataCleaner.MAX_POSSIBLE_TEMP)
        
        clean_series = series[mask_valid]
        
        removed_count = len(series) - len(clean_series)
        if removed_count > 0:
            logger.warning(f"Removidos {removed_count} pontos de dados fisicamente impossíveis.")
            
        return clean_series

class ClimateDataGenerator:
    """
    Gera dados sintéticos que imitam a realidade climática (Tendência + Sazonalidade + Cisnes Negros).
    Útil para demos e fallbacks quando a API externa falha.
    """
    def __init__(self, start_date='2000-01-01', years=20):
        self.start_date = start_date
        self.years = years
        self.days = years * 365

    def generate(self) -> pd.DataFrame:
        dates = pd.date_range(self.start_date, periods=self.days)
        t = np.arange(self.days)

        # Componentes
        trend = 0.0005 * t  # Aquecimento gradual
        seasonality = 10 * np.sin(2 * np.pi * t / 365) # Variação anual
        noise = np.random.normal(0, 2, self.days) # Variação diária comum
        base_temp = 25 + trend + seasonality + noise

        # Injeção de "Cisnes Negros" (Eventos Extremos Imprevistos)
        black_swans = np.random.choice([0, 1], size=self.days, p=[0.999, 0.001])
        impact = np.random.exponential(scale=8, size=self.days) * black_swans # Cauda longa
        
        final_temp = base_temp + impact

        return pd.DataFrame({'date': dates, 'temperature': final_temp})

# ==============================================================================
# 2. EXTREME VALUE THEORY MODEL (CORE)
# ==============================================================================

class ExtremeValueTheoryModel:
    """
    Implementação robusta de GEV (Generalized Extreme Value) para
    modelagem de máximos anuais e definição de preço de sobrevivência.
    """
    
    def __init__(self, confidence_level: float = 0.999):
        self.confidence_level = confidence_level # 1 em 1000 anos por padrão
        self.params: Optional[Tuple[float, float, float]] = None # c, loc, scale
        self.fitted = False

    def fit(self, data: pd.DataFrame, value_col: str = 'temperature', date_col: str = 'date') -> 'ExtremeValueTheoryModel':
        """
        Ajusta a distribuição GEV aos Block Maxima (Máximos Anuais).
        Suporta análise Não-Estacionária (Tendência Linear na Localização).
        """
        # Garantir datetime
        if not np.issubdtype(data[date_col].dtype, np.datetime64):
            data[date_col] = pd.to_datetime(data[date_col])
            
        # Limpeza prévia
        clean_values = ClimateDataCleaner.clean_temperature_data(data[value_col])
        df_clean = data.loc[clean_values.index].copy()
        
        # Block Maxima
        df_clean['year'] = df_clean[date_col].dt.year
        # Agrupamento por ano para obter maximos
        files_ann_max = df_clean.groupby('year')[value_col].agg(['max', 'count'])
        # Filtrar anos incompletos (opcional, aqui assumimos dados suficientes)
        annual_maxima = files_ann_max['max']
        years = annual_maxima.index.values
        
        if len(annual_maxima) < 10:
            logger.warning("Dados insuficientes para ajuste GEV confiável (< 10 anos). Resultados instáveis.")
            
        # 1. Detectar Tendência (Non-Stationarity Test)
        # Ajuste linear simples nos máximos anuais: Max(t) = a + b*t
        slope, intercept = np.polyfit(years, annual_maxima, 1)
        
        # Se slope positivo e significativo (heurística simples aqui, ideal seria Mann-Kendall)
        # Vamos assumir "Non-Stationary" se o aumento for > 0.02 grau/ano
        is_non_stationary = slope > 0.02 
        
        self.non_stationary_params = None
        
        if is_non_stationary:
            logger.info(f"Tendência Não-Estacionária Detectada: {slope:.4f}°C/ano. Usando GEV Não-Estacionária.")
            # Modelo: mu(t) = mu_0 + mu_1 * t
            # Approach: Detrend -> Fit GEV -> Retrend for projections
            current_year = years.max()
            # Trazemos todos os passados para o presente
            detrended_maxima = annual_maxima + (slope * (current_year - years))
            
            try:
                # Ajusta GEV aos dados "trazidos a valor presente"
                params = genextreme.fit(detrended_maxima)
                self.params = params
                self.fitted = True
                self.non_stationary_params = {'slope': slope, 'intercept': intercept, 'ref_year': current_year}
                
                c, loc, scale = self.params
                logger.info(f"Non-Stationary GEV Fit (Ref Year {current_year}): c={c:.4f}, loc={loc:.2f}, scale={scale:.2f}")

            except Exception as e:
                logger.error(f"Falha no ajuste GEV Não-Estacionário: {e}")
                self.params = (0.0, annual_maxima.mean(), annual_maxima.std())
                self.fitted = True
        else:
            # Stationary Fit padrão
            try:
                self.params = genextreme.fit(annual_maxima)
                self.fitted = True
                c, loc, scale = self.params
                logger.info(f"Stationary GEV Fit: c={c:.4f}, loc={loc:.2f}, scale={scale:.2f}")
            except Exception as e:
                logger.error(f"Falha no ajuste GEV: {e}")
                self.params = (0.0, annual_maxima.mean(), annual_maxima.std())
                self.fitted = True
            
        return self

    def calculate_risk_metrics(self, projection_years: int = 0) -> RiskMetrics:
        """
        Calcula métricas de risco baseadas no ajuste GEV.
        Se non-stationary, projeta para o futuro (projection_years).
        """
        if not self.fitted or not self.params:
            raise ValueError("Modelo não ajustado. Chame .fit() primeiro.")
            
        c, loc, scale = self.params
        
        # Se não-estacionário, ajusta 'loc' para o futuro
        if self.non_stationary_params and projection_years > 0:
            slope = self.non_stationary_params['slope']
            # Projetar 'loc' para o meio do período do contrato
            loc_future = loc + (slope * projection_years)
            logger.info(f"Projetando parâmetros GEV para +{projection_years} anos: loc {loc:.2f} -> {loc_future:.2f}")
            loc = loc_future
        
        # Return Level para 100 e 1000 anos
        rl_100 = genextreme.ppf(1 - (1/100), c, loc, scale)
        rl_1000 = genextreme.ppf(1 - (1/1000), c, loc, scale)
        
        tail_vol = max(0.1, abs(c)) * scale
        mpl = rl_1000 + (tail_vol * 3)
        
        return RiskMetrics(
            return_level_100=float(rl_100),
            return_level_1000=float(rl_1000),
            max_probable_loss=float(mpl),
            shape_parameter_xi=float(c),
            tail_volatility=float(tail_vol)
        )

    def calculate_eal(self, threshold: float, projection_years: int = 0) -> float:
        """
        Calcula a Perda Anual Esperada (Expected Annual Loss) integrando a cauda da distribuição.
        Suporta projeção futura dos parâmetros.
        """
        if not self.fitted or not self.params:
            return 0.0
            
        c, loc, scale = self.params
        
        if self.non_stationary_params and projection_years > 0:
            slope = self.non_stationary_params['slope']
            loc = loc + (slope * projection_years)
        
        try:
            p_exceed = 1 - genextreme.cdf(threshold, c, loc, scale)
            
            if p_exceed < 1e-6:
                return 0.0
                
            # Monte Carlo integration for Tail Expectation
            tail_samples = genextreme.rvs(c, loc, scale, size=10000)
            tail_losses = tail_samples[tail_samples > threshold]
            
            if len(tail_losses) == 0:
                expected_severity = threshold
            else:
                expected_severity = np.mean(tail_losses)
                
            eal = (expected_severity - threshold) * p_exceed
            return float(eal)
            
        except Exception as e:
            logger.error(f"Erro ao calcular EAL: {e}")
            return 0.0

# ==============================================================================
# 2.5 FRACTAL RISK ENGINE
# ==============================================================================

class FractalRiskEngine:
    """
    Analisa a estrutura temporal da série climática para detectar
    persistência (memória de longo prazo) e caos.
    """
    
    def calculate_hurst(self, series: pd.Series) -> float:
        """
        Calcula o Expoente de Hurst via Rescaled Range (R/S) Analysis usando a biblioteca nolds.
        H ~ 0.5: Passeio Aleatório (Browniano) -> Mercado Eficiente/Normal
        H > 0.5: Persistente (Tendência reforça tendência) -> Risco Alto de Extremes
        H < 0.5: Anti-persistente (Retorno à média) -> Estável
        """
        # Limpeza básica de NaNs
        clean_series = series.dropna().values
        
        if len(clean_series) < 10:
             return 0.5
            
        try:
            if NOLDS_AVAILABLE and nolds is not None:
                # nolds.hurst_rs implementa o método clássico R/S
                hurst = nolds.hurst_rs(clean_series)
            else:
                # Manual R/S Hurst exponent fallback
                n = len(clean_series)
                max_k = min(n // 2, 512)
                if max_k < 8:
                    return 0.5
                rs_values = []
                ns = []
                for k in [8, 16, 32, 64, 128, 256, 512]:
                    if k > max_k:
                        break
                    num_blocks = n // k
                    rs_block = []
                    for i in range(num_blocks):
                        block = clean_series[i*k:(i+1)*k]
                        mean_block = np.mean(block)
                        deviations = block - mean_block
                        cumsum = np.cumsum(deviations)
                        R = np.max(cumsum) - np.min(cumsum)
                        S = np.std(block, ddof=1)
                        if S > 0:
                            rs_block.append(R / S)
                    if rs_block:
                        rs_values.append(np.log(np.mean(rs_block)))
                        ns.append(np.log(k))
                if len(ns) >= 2:
                    slope, _ = np.polyfit(ns, rs_values, 1)
                    hurst = float(slope)
                else:
                    hurst = 0.5
            
            # Clip para manter limites físicos [0, 1]
            return max(0.0, min(1.0, float(hurst)))
            
        except Exception as e:
            logger.warning(f"Falha ao calcular Hurst com nolds: {e}. Usando fallback 0.5")
            return 0.5

    def analyze_risk(self, data: pd.Series) -> FractalAnalysisResult:
        hurst = self.calculate_hurst(data)
        
        # Interpretação do Regime Fractal
        if hurst > 0.65:
            regime = "Super-Persistent (Danger Zone)"
            # Se H é alto, o desvio padrão da GEV vai subestimar o futuro.
            # Aumentamos o prêmio agressivamente.
            multiplier = 1.0 + (hurst - 0.5) * 6  # Ex: H=0.75 -> +150% preço
        elif hurst < 0.40:
            regime = "Mean Reverting (Safe)"
            multiplier = 0.90 # Desconto leve, tendência de estabilidade
        else:
            regime = "Random Walk (Normal)"
            multiplier = 1.0
            
        # Dimensão Fractal (D = 2 - H para séries temporais)
        fractal_dim = 2 - hurst

        return FractalAnalysisResult(
            hurst_exponent=round(hurst, 3),
            fractal_dimension=round(fractal_dim, 3),
            regime=regime,
            risk_multiplier=round(multiplier, 2)
        )

# ==============================================================================
# 2.8 SPATIAL DEPENDENCE ENGINE (MAX-STABLE PROCESSES)
# ==============================================================================

class SpatialRiskEngine:
    """
    Analisa a dependência espacial de eventos extremos (Max-Stable Processes).
    Stub para futura implementação com múltiplos locais.
    """
    
    def calculate_spatial_impact(self, lat: float, lon: float, nearby_risks: List[dict]) -> float:
        """
        Calcula multiplicador de risco baseado na correlação de cauda com locais vizinhos.
        Se houve eventos extremos perto, a probabilidade aqui aumenta (Brown-Resnick Process).
        """
        if not nearby_risks:
            return 1.0
            
        # Simulação: Decaimento exponencial da correlação com a distância
        total_risk_boost = 0.0
        for item in nearby_risks:
            dist_km = np.sqrt((lat - item['lat'])**2 + (lon - item['lon'])**2) * 111
            if dist_km < 500: # Raio de influência de 500km
                correlation = np.exp(-dist_km / 100.0) # Decai a cada 100km
                if item['severity'] > 0.9: # Evento extremo vizinho
                    total_risk_boost += correlation * 0.5
                    
        return 1.0 + min(total_risk_boost, 2.0)

# ==============================================================================
# 3. DEFENSIVE PRICING ORCHESTRATOR
# ==============================================================================

class DefensivePricingOrchestrator:
    """
    Orquestra a decisão entre precificação de mercado (Gaussian) e 
    precificação de sobrevivência (EVT).
    Implementa Regret Minimization.
    """
    
    def __init__(self):
        self.evt_model = ExtremeValueTheoryModel()
        self.fractal_engine = FractalRiskEngine()
        self.spatial_engine = SpatialRiskEngine()
        
    def calculate_gaussian_benchmark(self, data: pd.DataFrame, value_col: str, asset_value: float, severity_amount: float, frequency_pct: float, duration_years: int = 1) -> float:
        """
        Calcula um benchmark de prêmio usando distribuição normal e parâmetros da apólice.
        """
        series = data[value_col]
        mu, std = norm.fit(series)
        
        # O prêmio puro baseia-se na perda esperada (frequência * severidade)
        perda_esperada_base = (frequency_pct / 100.0) * min(severity_amount, asset_value)
        
        # Ajuste de volatilidade gaussiana (99.9% de confiança)
        risk_999 = norm.ppf(0.999, loc=mu, scale=std)
        threshold = mu + 2 * std
        
        # Multiplicador de "clima atual" - se o risco de cauda gaussiano for alto
        volatility_buffer = 1.0 + (max(0, risk_999 - threshold) / max(1, std))
        
        base_annual_price = perda_esperada_base * volatility_buffer
        return base_annual_price * duration_years

    def calculate_trend_adjustment(self, data: pd.DataFrame, value_col: str = 'temperature') -> float:
        """
        Calcula o multiplicador de tendência baseado na inclinação histórica.
        """
        try:
            y = data[value_col].values
            x = np.arange(len(y))
            slope, _ = np.polyfit(x, y, 1)
            if slope > 0:
                # Se a tendência é de alta (aquecimento), aumentamos o prêmio
                mean_val = np.mean(y)
                projected_increase = (slope * 365 * 5) / max(1, mean_val)
                return 1.0 + (projected_increase * 2.0) 
            return 1.0
        except:
            return 1.0

    def price_contract(self, data: pd.DataFrame, asset_value: float = 10000.0, severity_amount: float = 1000.0, frequency_pct: float = 10.0, duration_years: int = 1, nearby_risks: List[dict] = None) -> PricingOutput:
        """
        Executa a precificação defensiva integrando Teoria de Valores Extremos e Parâmetros de Apólice.
        """
        # 1. Fit EVT
        self.evt_model.fit(data)
        
        # Projeção
        projection_years = int(duration_years / 2)
        metrics = self.evt_model.calculate_risk_metrics(projection_years=projection_years)
        
        # 2. Cálculo EAL (Expected Annual Loss) via EVT
        threshold = data['temperature'].mean() + (2 * data['temperature'].std())
        
        # 3. Cálculo Financeiro Baseado na Apólice
        perda_esperada_base = (frequency_pct / 100.0) * min(severity_amount, asset_value)
        total_pure_premium = perda_esperada_base * duration_years
        
        # 4. Multiplicadores de Risco de Sobrevivência (EVT)
        tail_multiplier = 1.0
        if metrics.shape_parameter_xi > 0:
            tail_multiplier += metrics.shape_parameter_xi * 3.0
            
        # 5. Carga de Capital de Solvência
        temp_excursion = max(0, metrics.max_probable_loss - threshold)
        capital_charge_rate = min(0.50, (temp_excursion / 10.0) * 0.15)
        capital_charge = (severity_amount * capital_charge_rate) * duration_years
        
        # 6. Ajustes de Tendência, Fractal e Espacial
        trend_multiplier = self.calculate_trend_adjustment(data)
        fractal_metrics = self.fractal_engine.analyze_risk(data['temperature'])
        
        spatial_multiplier = 1.0
        lat, lon = -23.55, -46.63 
        if nearby_risks:
            spatial_multiplier = self.spatial_engine.calculate_spatial_impact(lat, lon, nearby_risks)
        
        # 7. Preço Final Safety First
        safety_price = (total_pure_premium * tail_multiplier + capital_charge) * \
                       trend_multiplier * \
                       fractal_metrics.risk_multiplier * \
                       spatial_multiplier
        
        # Piso de prêmio: 1% do valor do ativo ao ano
        min_premium = (asset_value * 0.01) * duration_years
        safety_price = max(safety_price, min_premium)
        
        # 8. Benchmark Gaussiano
        gaussian_price = self.calculate_gaussian_benchmark(
            data, 'temperature', asset_value, severity_amount, frequency_pct, duration_years
        )
        
        # 9. Arbitragem
        divergence = 0.0
        if gaussian_price > 0:
            divergence = (safety_price - gaussian_price) / gaussian_price
            
        strategy = PricingStrategy.WEIGHTED_ENSEMBLE
        final_price = (safety_price * 0.7) + (gaussian_price * 0.3)
        warnings = []
        
        if divergence > 0.25: 
            strategy = PricingStrategy.SAFETY_FIRST
            final_price = safety_price
            warnings.append("ALERTA: Ativado protocolo Safety First. Modelo Gaussiano descartado por subprecificação de risco de cauda catastrófico.")
            
        if fractal_metrics.risk_multiplier > 1.2:
             warnings.append(f"ALERTA CRÍTICO: Regime Caótico Detectado (Hurst={fractal_metrics.hurst_exponent}). Risco de instabilidade de parâmetros.")
             
        if trend_multiplier > 1.1:
            warnings.append(f"INFO: Tendência de aquecimento secular detectada. Prêmio ajustado preventivamente.")

        return PricingOutput(
            final_premium=round(final_price, 2),
            strategy=strategy,
            risk_metrics=metrics,
            warnings=warnings,
            divergence_factor=round(divergence * 100, 1),
            fractal_metrics=fractal_metrics
        )

# ==============================================================================
# 4. BACKTESTING & STRESS TESTING
# ==============================================================================

class StressTester:
    """
    Simulador de cenários de ruptura para validação da solvência.
    """
    
    @staticmethod
    def run_stress_test(
        data: pd.DataFrame, 
        orchestrator: DefensivePricingOrchestrator,
        temp_shift: float = 4.0
    ) -> StressTestResult:
        """
        Simula um choque climático (+X graus) e verifica se o prêmio cobrado
        pagaria os sinistros resultantes.
        """
        # Duração da simulação baseada nos dados (ex: 20 anos)
        n_years = max(1, int(len(data) / 365))
        
        # 1. Precificar ANTES do choque (Estado atual)
        # Assumindo valores padrão para o stress test
        pricing_result = orchestrator.price_contract(data, duration_years=n_years)
        premium_collected = pricing_result.final_premium
        
        # 2. Simular Choque (Futuro Distópico)
        # Adiciona shift na média e aumenta volatilidade
        future_data = data.copy()
        future_data['temperature'] = future_data['temperature'] + temp_shift
        # Aumentar extremos
        threshold_qk = future_data['temperature'].quantile(0.95)
        future_data['temperature'] = future_data['temperature'].apply(
            lambda x: x * 1.15 if x > threshold_qk else x
        )
        
        # 3. Calcular Sinistros no Futuro (Realized Loss)
        # Limiar de sinistro histórico
        hist_threshold = data['temperature'].mean() + (2 * data['temperature'].std())
        
        # Modelo Gaussiano (Comparativo)
        # Usando valores padrão para o benchmark no stress test
        gaussian_premium = orchestrator.calculate_gaussian_benchmark(
            data, 'temperature', asset_value=10000.0, severity_amount=1000.0, frequency_pct=10.0, duration_years=n_years
        )
        
        # Calcular perdas reais no cenário futuro
        losses = future_data[future_data['temperature'] > hist_threshold]
        total_loss_payout = (losses['temperature'] - hist_threshold).sum() * 50.0 # Custo por grau
        
        # Balanço
        old_model_balance = gaussian_premium - total_loss_payout
        new_model_balance = premium_collected - total_loss_payout
        
        return StressTestResult(
            scenario_name=f"Climate Shift +{temp_shift}°C ({n_years} anos)",
            temperature_shift=temp_shift,
            old_model_loss=round(old_model_balance, 2),
            new_model_profit_or_loss=round(new_model_balance, 2),
            solvency_maintained=new_model_balance >= 0,
            details={
                "premium_collected_new": premium_collected,
                "premium_collected_old": gaussian_premium,
                "total_payout_needed": total_loss_payout,
                "years_simulated": n_years
            }
        )

# ==============================================================================
# EXMPLO DE USO (MAIN)
# ==============================================================================
if __name__ == "__main__":
    # Mock data para teste rápido
    dates = pd.date_range('2000-01-01', periods=365*20)
    # Inject Warming Trend: 0.05 C/year approx
    trend = np.linspace(0, 2.0, len(dates)) 
    temps = np.random.normal(25, 5, len(dates)) + trend
    
    # Inject Black Swan
    temps[1000] = 45.0 
    
    df = pd.DataFrame({'date': dates, 'temperature': temps})
    
    orch = DefensivePricingOrchestrator()
    # Contract for 5 years
    result = orch.price_contract(df, duration_years=5)
    
    print(f"Pricing Result: {result.model_dump_json(indent=2)}")
    
    stress = StressTester.run_stress_test(df, orch, temp_shift=5.0)
    print(f"Stress Test: {stress.model_dump_json(indent=2)}")
