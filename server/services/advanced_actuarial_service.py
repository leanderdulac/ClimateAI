"""
Serviço avançado de cálculos atuariais com conceitos matemáticos sofisticados
"""

import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy import stats
from scipy.optimize import minimize_scalar


@dataclass
class FractalDimension:
    """Dimensão fractal para análise de padrões climáticos"""

    dimension: float
    lacunarity: float
    persistence: float


@dataclass
class FuzzyRiskLevel:
    """Nível de risco fuzzy com graus de pertinência"""

    very_low: float  # 0-0.2
    low: float  # 0.1-0.4
    medium: float  # 0.3-0.7
    high: float  # 0.6-0.9
    very_high: float  # 0.8-1.0


@dataclass
class ActuarialPremium:
    """Resultado atuarial completo"""

    pure_premium: float
    loading_premium: float
    total_premium: float
    risk_margin: float
    confidence_interval: Tuple[float, float]
    fractal_dimension: FractalDimension
    fuzzy_risk: FuzzyRiskLevel


class AdvancedActuarialService:
    """
    Serviço que combina múltiplas técnicas matemáticas avançadas:
    - Cálculo fratal para padrões climáticos
    - Simulação Monte Carlo expandida
    - Lógica fuzzy para avaliação de risco
    - Física estatística para sistemas complexos
    - Cálculos atuariais específicos do setor de seguros
    """

    def __init__(self):
        self.monte_carlo_iterations = 50000  # Aumentado para maior precisão
        self.fractal_scales = [
            2**i for i in range(1, 12)
        ]  # Escalas para análise fractal

    def calculate_fractal_dimension(self, climate_data: List[Dict]) -> FractalDimension:
        """
        Calcula a dimensão fractal dos dados climáticos usando método de box-counting
        """
        if not climate_data:
            return FractalDimension(1.0, 1.0, 0.5)

        # Extrair séries temporais
        temperatures = [d.get("temperature", 0) for d in climate_data]
        precipitations = [d.get("precipitation", 0) for d in climate_data]

        # Calcular dimensão fractal para temperatura
        temp_dimension = self._box_counting_dimension(temperatures)

        # Calcular dimensão fractal para precipitação
        precip_dimension = self._box_counting_dimension(precipitations)

        # Dimensão média ponderada
        dimension = temp_dimension * 0.6 + precip_dimension * 0.4

        # Calcular lacunaridade (heterogeneidade)
        lacunarity = self._calculate_lacunarity(temperatures + precipitations)

        # Calcular persistência (autocorrelação)
        persistence = self._calculate_persistence(temperatures)

        return FractalDimension(
            dimension=min(max(dimension, 1.0), 2.0),  # Limitar entre 1 e 2
            lacunarity=lacunarity,
            persistence=persistence,
        )

    def _box_counting_dimension(self, data: List[float]) -> float:
        """Implementa o método de box-counting para dimensão fractal"""
        if len(data) < 10:
            return 1.5  # Valor padrão para séries pequenas

        scales = []
        counts = []

        for scale in self.fractal_scales:
            if scale >= len(data):
                continue

            # Contar caixas necessárias
            count = 0
            min_val, max_val = min(data), max(data)
            box_size = (max_val - min_val) / scale

            if box_size == 0:
                continue

            # Box counting simplificado
            boxes = set()
            for i in range(0, len(data) - int(scale) + 1, int(scale)):
                window = data[i : i + int(scale)]
                box_idx = int((sum(window) / len(window) - min_val) / box_size)
                boxes.add(box_idx)

            if len(boxes) > 0:
                scales.append(math.log(1.0 / scale))
                counts.append(math.log(len(boxes)))

        if len(scales) < 2:
            return 1.5

        # Regressão linear para encontrar dimensão
        slope, _ = np.polyfit(scales, counts, 1)
        return max(1.0, min(2.0, slope))

    def _calculate_lacunarity(self, data: List[float]) -> float:
        """Calcula lacunaridade (medida de heterogeneidade)"""
        if len(data) < 10:
            return 1.0

        # Método simplificado de lacunaridade
        mean_val = np.mean(data)
        variance = np.var(data)

        if mean_val == 0:
            return 1.0

        # Lacunaridade baseada no coeficiente de variação ao quadrado
        return 1 + (variance / (mean_val**2))

    def _calculate_persistence(self, data: List[float]) -> float:
        """Calcula persistência através da autocorrelação"""
        if len(data) < 5:
            return 0.5

        # Autocorrelação lag-1
        mean_val = np.mean(data)
        autocorr = np.corrcoef(data[:-1], data[1:])[0, 1]

        return max(0.0, min(1.0, (autocorr + 1) / 2))  # Normalizar para [0,1]

    def fuzzy_risk_assessment(
        self,
        frequency: float,
        severity: float,
        fractal_dim: FractalDimension,
        asset_value: float,
    ) -> FuzzyRiskLevel:
        """
        Avaliação fuzzy do nível de risco baseada em múltiplas variáveis
        """
        # Normalizar entradas
        freq_norm = min(frequency / 100.0, 1.0)
        severity_norm = min(severity / asset_value, 1.0)
        fractal_norm = (fractal_dim.dimension - 1.0) / 1.0  # 1.0-2.0 -> 0.0-1.0

        # Funções de pertinência fuzzy
        def very_low_membership(x: float) -> float:
            return max(0, 1 - x / 0.2)

        def low_membership(x: float) -> float:
            return max(0, min(1, (x - 0.1) / 0.3, 1 - (x - 0.1) / 0.3))

        def medium_membership(x: float) -> float:
            return max(0, min(1, (x - 0.3) / 0.4, 1 - (x - 0.3) / 0.4))

        def high_membership(x: float) -> float:
            return max(0, min(1, (x - 0.6) / 0.3, 1 - (x - 0.6) / 0.3))

        def very_high_membership(x: float) -> float:
            return max(0, (x - 0.8) / 0.2)

        # Calcular risco composto (média ponderada)
        risk_score = freq_norm * 0.3 + severity_norm * 0.4 + fractal_norm * 0.3

        return FuzzyRiskLevel(
            very_low=very_low_membership(risk_score),
            low=low_membership(risk_score),
            medium=medium_membership(risk_score),
            high=high_membership(risk_score),
            very_high=very_high_membership(risk_score),
        )

    def advanced_monte_carlo_simulation(
        self,
        frequency: float,
        severity: float,
        asset_value: float,
        fractal_dim: FractalDimension,
        fuzzy_risk: FuzzyRiskLevel,
    ) -> Dict:
        """
        Simulação Monte Carlo avançada com física estatística
        """
        losses = []

        # Distribuições baseadas na dimensão fractal
        if fractal_dim.dimension > 1.7:  # Alta complexidade
            # Distribuição de Pareto (power-law) para eventos extremos
            shape = 2.5 + fractal_dim.persistence
            scale = severity * 0.1
        elif fractal_dim.dimension > 1.4:  # Complexidade média
            # Distribuição log-normal
            shape = 0.5 + fractal_dim.lacunarity * 0.5
            scale = math.log(severity)
        else:  # Baixa complexidade
            # Distribuição normal truncada
            shape = severity * 0.5
            scale = severity * 0.2

        for _ in range(self.monte_carlo_iterations):
            # Verificar se ocorre evento
            if random.random() < frequency / 100.0:
                # Aplicar lógica fuzzy ao tamanho da perda
                risk_multiplier = (
                    fuzzy_risk.very_low * 0.1
                    + fuzzy_risk.low * 0.3
                    + fuzzy_risk.medium * 0.6
                    + fuzzy_risk.high * 0.9
                    + fuzzy_risk.very_high * 1.2
                )

                if fractal_dim.dimension > 1.7:
                    # Power-law distribution
                    loss = min(asset_value, scale * (random.pareto(shape)))
                elif fractal_dim.dimension > 1.4:
                    # Log-normal distribution
                    loss = min(asset_value, math.exp(random.gauss(scale, shape)))
                else:
                    # Normal distribution
                    loss = min(asset_value, abs(random.gauss(shape, scale)))

                losses.append(loss * risk_multiplier)
            else:
                losses.append(0)

        return {
            "losses": losses,
            "mean_loss": np.mean(losses),
            "std_loss": np.std(losses),
            "var_95": np.percentile(losses, 95),
            "var_99": np.percentile(losses, 99),
            "expected_shortfall": np.mean(
                [l for l in losses if l > np.percentile(losses, 95)]
            ),
        }

    def actuarial_premium_calculation(
        self,
        monte_carlo_results: Dict,
        confidence_level: float,
        expense_loading: float = 0.25,
        profit_loading: float = 0.10,
    ) -> ActuarialPremium:
        """
        Cálculo atuarial completo seguindo princípios do setor de seguros
        """
        mean_loss = monte_carlo_results["mean_loss"]
        std_loss = monte_carlo_results["std_loss"]

        # Prêmio puro (pure premium)
        pure_premium = mean_loss

        # Margem de risco baseada na volatilidade e nível de confiança
        z_score = stats.norm.ppf(confidence_level / 100.0)
        risk_margin = z_score * std_loss / math.sqrt(self.monte_carlo_iterations)

        # Carregamentos atuariais
        total_loading = expense_loading + profit_loading
        loading_premium = pure_premium * total_loading

        # Prêmio total
        total_premium = pure_premium + risk_margin + loading_premium

        # Intervalo de confiança
        confidence_interval = (
            max(0, total_premium - 1.96 * std_loss),
            total_premium + 1.96 * std_loss,
        )

        return ActuarialPremium(
            pure_premium=pure_premium,
            loading_premium=loading_premium,
            total_premium=total_premium,
            risk_margin=risk_margin,
            confidence_interval=confidence_interval,
            fractal_dimension=FractalDimension(1.5, 1.0, 0.5),  # Placeholder
            fuzzy_risk=FuzzyRiskLevel(0, 0, 0, 0, 0),  # Placeholder
        )

    def calculate_comprehensive_premium(
        self,
        frequency: float,
        severity: float,
        asset_value: float,
        confidence_level: float,
        climate_data: List[Dict],
    ) -> ActuarialPremium:
        """
        Método principal que combina todos os conceitos avançados
        """
        # 1. Análise fractal dos dados climáticos
        fractal_dim = self.calculate_fractal_dimension(climate_data)

        # 2. Avaliação fuzzy do risco
        fuzzy_risk = self.fuzzy_risk_assessment(
            frequency, severity, fractal_dim, asset_value
        )

        # 3. Simulação Monte Carlo avançada
        mc_results = self.advanced_monte_carlo_simulation(
            frequency, severity, asset_value, fractal_dim, fuzzy_risk
        )

        # 4. Cálculo atuarial completo
        premium = self.actuarial_premium_calculation(mc_results, confidence_level)

        # Atualizar com dados reais
        premium.fractal_dimension = fractal_dim
        premium.fuzzy_risk = fuzzy_risk

        return premium
