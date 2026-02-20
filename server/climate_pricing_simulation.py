
import numpy as np
import pandas as pd
from scipy.stats import norm, genextreme, genpareto
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Dict, Optional

# ==============================================================================
# 1. GERADOR DE CENÁRIOS CLIMÁTICOS (COM "CISNES NEGROS")
# ==============================================================================
class ClimateDataGenerator:
    """
    Gera dados sintéticos que imitam a realidade climática:
    - Tendência Linear (Aquecimento Global)
    - Sazonalidade (Verão/Inverno)
    - Ruído Branco (Variação diária)
    - Eventos de Cauda (Cisnes Negros/Choques)
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
        # Probabilidade de 0.1% de ocorrer um salto de temperatura brutal
        black_swans = np.random.choice([0, 1], size=self.days, p=[0.999, 0.001])
        impact = np.random.exponential(scale=8, size=self.days) * black_swans # Cauda longa
        
        final_temp = base_temp + impact

        return pd.DataFrame({'date': dates, 'temperature': final_temp, 'is_extreme': black_swans})

# ==============================================================================
# 2. MOTORES DE PRECIFICAÇÃO (MODELOS MATEMÁTICOS)
# ==============================================================================

@dataclass
class PricingResult:
    model_name: str
    predicted_max_risk: float  # Temperatura máxima prevista (VaR 99.9%)
    premium_price: float       # Preço sugerido do contrato
    confidence_interval: tuple

class GaussianModel:
    """
    MODELO LEGADO (Atual): Assume distribuição Normal.
    Perigo: Subestima eventos extremos (Caudas Finas).
    """
    def predict_risk(self, data: pd.Series) -> PricingResult:
        mu, std = norm.fit(data)
        # Value at Risk (VaR) a 99.9% (1 evento em 1000)
        risk_999 = norm.ppf(0.999, loc=mu, scale=std)
        
        # Preço base simples (linear ao risco)
        price = risk_999 * 10 
        
        return PricingResult(
            model_name="Gaussian (Naive)",
            predicted_max_risk=risk_999,
            premium_price=price,
            confidence_interval=(risk_999 - 1.96*std, risk_999 + 1.96*std)
        )

class ExtremeValueTheoryModel:
    """
    NOVO MODELO (Proposto): Usa GEV (Generalized Extreme Value).
    Vantagem: Projetado matematicamente para modelar máximos e colapsos.
    """
    def predict_risk(self, df: pd.DataFrame) -> PricingResult:
        # Passo 1: Block Maxima (Pegar o pior caso de cada ano)
        df['year'] = df['date'].dt.year
        annual_maxima = df.groupby('year')['temperature'].max()

        # Passo 2: Ajustar Distribuição GEV aos máximos
        # c = shape parameter (controla a gordura da cauda)
        try:
            c, loc, scale = genextreme.fit(annual_maxima)
        except Exception as e:
            # Fallback seguro caso o fit falhe
            print(f"Aviso: GEV fit falou ({e}), usando parametros padrao")
            c, loc, scale = -0.1, annual_maxima.mean(), annual_maxima.std()

        # Passo 3: Calcular "Return Level" para 100 anos (1% risk)
        # Probabilidade de exceder = 1/100
        return_level_100 = genextreme.ppf(1 - (1/100), c, loc, scale)
        
        # Ajuste de segurança para o "Não Previsto" (Cisne Negro)
        # Adiciona buffer baseado na incerteza do parametro 'c' (shape)
        uncertainty_buffer = abs(c) * scale * 5
        final_risk = return_level_100 + uncertainty_buffer

        price = final_risk * 15 # Multiplicador maior devido à volatilidade da cauda

        return PricingResult(
            model_name="GEV (Extreme Value)",
            predicted_max_risk=final_risk,
            premium_price=price,
            confidence_interval=(return_level_100, return_level_100 + uncertainty_buffer)
        )

# ==============================================================================
# 3. ORQUESTRADOR UNIFICADO (COM LÓGICA DE SEGURANÇA)
# ==============================================================================
class UnifiedPricingOrchestrator:
    def __init__(self):
        self.models = [GaussianModel(), ExtremeValueTheoryModel()]

    def price_contract(self, data: pd.DataFrame):
        print(f"--- Iniciando Precificação para {len(data)} dias de histórico ---")
        
        results = []
        for model in self.models:
            # O modelo GEV precisa do dataframe completo, o Gaussiano só da série
            if isinstance(model, ExtremeValueTheoryModel):
                res = model.predict_risk(data)
            else:
                res = model.predict_risk(data['temperature'])
            results.append(res)
            print(f"[{res.model_name}] Risco Max: {res.predicted_max_risk:.2f}°C | Prêmio: ${res.premium_price:.2f}")

        # LÓGICA DE ARBITRAGEM (REGRET MINIMIZATION)
        # Em vez de média, usamos o princípio da precaução para catástrofes.
        # Se a divergência entre os modelos for alta (> 20%), confiamos no modelo de Cauda (GEV).
        
        price_gauss = results[0].premium_price
        price_gev = results[1].premium_price
        
        divergence = (price_gev - price_gauss) / price_gauss if price_gauss > 0 else 1.0
        
        print(f"\n>> Divergência de Modelagem: {divergence*100:.1f}%")
        
        if divergence > 0.2:
            final_price = price_gev
            strategy = "Safety First (GEV Dominance)"
            warning = "ALERTA: O modelo Gaussiano está subprecificando riscos extremos severamente."
        else:
            final_price = (price_gauss * 0.4) + (price_gev * 0.6)
            strategy = "Weighted Ensemble"
            warning = "Riscos dentro da normalidade estatística."

        return {
            "final_price": final_price,
            "strategy": strategy,
            "warning": warning,
            "details": results
        }

# ==============================================================================
# 4. EXECUÇÃO DA SIMULAÇÃO
# ==============================================================================

if __name__ == "__main__":
    # 1. Gerar dados (Mundo real com caos)
    gen = ClimateDataGenerator(years=50) # 50 anos de dados
    data = gen.generate()

    # Visualização Rápida dos "Cisnes Negros" gerados
    print(f"Número de Eventos Extremos (Cisnes Negros) gerados: {data['is_extreme'].sum()}")
    max_temp = data['temperature'].max()
    print(f"Temperatura Máxima Histórica Observada: {max_temp:.2f}°C\n")

    # 2. Executar Orquestrador
    orchestrator = UnifiedPricingOrchestrator()
    decision = orchestrator.price_contract(data)

    # 3. Relatório Final
    print("\n" + "="*40)
    print("     DECISÃO FINAL DE PRECIFICAÇÃO")
    print("="*40)
    print(f"Prêmio Final:       ${decision['final_price']:.2f}")
    print(f"Estratégia Adotada: {decision['strategy']}")
    print(f"Diagnóstico:        {decision['warning']}")
    print("="*40)
