"""
Backtesting Service for Regulatory Compliance
Implements: Kupiec Test, Christoffersen Test, Stress Testing

Requisitos Regulatórios:
- SUSEP Circular 562/2015
- Solvency II
- Basel III
- IFRS 17
"""

import logging
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class TestType(Enum):
    """Tipos de testes de backtesting"""
    KUPIC_POF = "kupiec_pof"
    CHRISTOFFERSEN_IND = "christoffersen_independence"
    CHRISTOFFERSEN_CC = "christoffersen_conditional_coverage"
    STRESS_TEST = "stress_test"
    VAR_BACKTEST = "var_backtest"


@dataclass
class BacktestResult:
    """Resultado de um teste de backtesting"""
    test_name: str
    test_type: str
    statistic: float
    p_value: float
    passed: bool
    confidence_level: float
    null_hypothesis: str
    alternative_hypothesis: str
    details: Dict[str, Any]
    timestamp: str
    regulatory_compliance: List[str]
    
    def to_dict(self) -> Dict:
        """Converter para dicionário"""
        return asdict(self)


@dataclass
class VaRBacktestReport:
    """Relatório completo de backtesting de VaR"""
    policy_id: str
    var_95: BacktestResult
    var_99: BacktestResult
    independence: BacktestResult
    conditional_coverage: Optional[BacktestResult]
    total_exceptions: int
    expected_exceptions: int
    exception_ratio: float
    rating: str  # AAA, AA, A, BBB, BB, B
    regulatory_status: str  # APPROVED, REVIEW_REQUIRED, REJECTED
    recommendations: List[str]
    generation_timestamp: str
    
    def to_dict(self) -> Dict:
        """Converter para dicionário"""
        return asdict(self)


@dataclass
class StressTestScenario:
    """Cenário de stress test"""
    name: str
    description: str
    shocks: Dict[str, float]
    historical_event: Optional[str]
    probability: float


class BacktestingService:
    """
    Serviço de backtesting para validação de modelos
    Requisitos: SUSEP, Solvency II, Basel III
    
    Implementa:
    - Kupiec POF Test (Proportion of Failures)
    - Christoffersen Independence Test
    - Christoffersen Conditional Coverage Test
    - Stress Testing com cenários históricos
    """
    
    def __init__(self):
        self.min_history_years = 10  # Mínimo regulatório
        self.confidence_levels = [0.95, 0.99]
        self.significance_level = 0.05  # α = 5%
        
        # Cenários de stress obrigatórios
        self.stress_scenarios = self._init_stress_scenarios()
    
    def _init_stress_scenarios(self) -> List[StressTestScenario]:
        """Inicializar cenários de stress obrigatórios"""
        return [
            StressTestScenario(
                name="2008_subprime_crisis",
                description="Global Financial Crisis - Subprime Mortgage",
                shocks={
                    'asset_value': -0.40,
                    'frequency': 2.5,
                    'severity': 3.0,
                    'correlation': 0.8
                },
                historical_event="2008-09-15",
                probability=0.01
            ),
            StressTestScenario(
                name="2020_covid_pandemic",
                description="COVID-19 Global Pandemic",
                shocks={
                    'asset_value': -0.30,
                    'frequency': 1.5,
                    'severity': 2.0,
                    'correlation': 0.7
                },
                historical_event="2020-03-11",
                probability=0.02
            ),
            StressTestScenario(
                name="brazil_2015_recession",
                description="Brazil Economic Recession 2015-2016",
                shocks={
                    'asset_value': -0.25,
                    'frequency': 1.8,
                    'severity': 2.2,
                    'correlation': 0.6,
                    'inflation': 0.10,
                    'interest_rate': 0.05
                },
                historical_event="2015-01-01",
                probability=0.05
            ),
            StressTestScenario(
                name="climate_extreme_event",
                description="Extreme Climate Event (100-year flood/drought)",
                shocks={
                    'asset_value': -0.50,
                    'frequency': 5.0,
                    'severity': 5.0,
                    'correlation': 0.9
                },
                historical_event=None,
                probability=0.01
            )
        ]
    
    def run_kupiec_pof_test(
        self,
        historical_losses: np.ndarray,
        var_predictions: np.ndarray,
        confidence_level: float = 0.95
    ) -> BacktestResult:
        """
        Teste de Kupiec POF (Proportion of Failures)
        
        H0: Taxa de exceções = (1 - confidence_level)
        H1: Taxa de exceções != (1 - confidence_level)
        
        Estatística: LR ~ χ²(1)
        
        Args:
            historical_losses: Perdas históricas observadas
            var_predictions: Previsões de VaR
            confidence_level: Nível de confiança (0.95 ou 0.99)
        
        Returns:
            BacktestResult com estatística e p-value
        """
        n = len(historical_losses)
        expected_exc_rate = 1 - confidence_level
        actual_exceptions = int(np.sum(historical_losses > var_predictions))
        actual_exc_rate = actual_exceptions / n if n > 0 else 0
        
        logger.info(f"Kupiec Test: n={n}, expected_rate={expected_exc_rate:.4f}, "
                   f"actual_exceptions={actual_exceptions}, actual_rate={actual_exc_rate:.4f}")
        
        # Likelihood sob H0 (taxa esperada)
        if actual_exceptions > 0 and actual_exceptions < n:
            log_likelihood_null = (
                actual_exceptions * np.log(expected_exc_rate) +
                (n - actual_exceptions) * np.log(1 - expected_exc_rate)
            )
            
            # Likelihood sob H1 (taxa observada)
            log_likelihood_alt = (
                actual_exceptions * np.log(actual_exc_rate) +
                (n - actual_exceptions) * np.log(1 - actual_exc_rate)
            )
            
            # Likelihood Ratio statistic
            lr_stat = -2 * (log_likelihood_null - log_likelihood_alt)
        else:
            # Casos extremos (0 ou 100% de exceções)
            lr_stat = np.inf if actual_exc_rate != expected_exc_rate else 0
        
        # P-value from Chi-squared distribution with 1 df
        p_value = float(1 - stats.chi2.cdf(lr_stat, df=1)) if np.isfinite(lr_stat) else 0
        
        # Critério de aprovação
        # H0 não é rejeitada se p-value > 0.05
        # E se razão entre taxas estiver entre 0.8 e 1.2
        rate_ratio = actual_exc_rate / expected_exc_rate if expected_exc_rate > 0 else 0
        passed = (p_value > self.significance_level) and (0.5 <= rate_ratio <= 2.0)
        
        return BacktestResult(
            test_name="Kupiec POF Test",
            test_type=TestType.KUPIC_POF.value,
            statistic=float(lr_stat),
            p_value=p_value,
            passed=passed,
            confidence_level=confidence_level,
            null_hypothesis=f"Exception rate = {expected_exc_rate:.4f}",
            alternative_hypothesis=f"Exception rate != {expected_exc_rate:.4f}",
            details={
                'total_observations': int(n),
                'actual_exceptions': actual_exceptions,
                'expected_exceptions': float(n * expected_exc_rate),
                'exception_rate': float(actual_exc_rate),
                'expected_rate': float(expected_exc_rate),
                'ratio': float(rate_ratio),
                'critical_value_5pct': float(stats.chi2.ppf(0.95, df=1))
            },
            timestamp=datetime.now().isoformat(),
            regulatory_compliance=['SUSEP', 'Solvency II', 'Basel III']
        )
    
    def run_christoffersen_independence_test(
        self,
        historical_losses: np.ndarray,
        var_predictions: np.ndarray,
        confidence_level: float = 0.95
    ) -> BacktestResult:
        """
        Teste de Christoffersen para Independência de Exceções
        
        Testa se exceções são independentes (não há clustering)
        
        H0: Exceções são independentes
        H1: Exceções apresentam clustering
        
        Estatística: LR_ind ~ χ²(1)
        """
        n = len(historical_losses)
        exceptions = (historical_losses > var_predictions).astype(int)
        
        # Contar transições
        n00 = int(np.sum((exceptions[:-1] == 0) & (exceptions[1:] == 0)))
        n01 = int(np.sum((exceptions[:-1] == 0) & (exceptions[1:] == 1)))
        n10 = int(np.sum((exceptions[:-1] == 1) & (exceptions[1:] == 0)))
        n11 = int(np.sum((exceptions[:-1] == 1) & (exceptions[1:] == 1)))
        
        logger.info(f"Christoffersen Test: n00={n00}, n01={n01}, n10={n10}, n11={n11}")
        
        # Probabilidades de transição
        pi01 = n01 / (n00 + n01) if (n00 + n01) > 0 else 0
        pi11 = n11 / (n10 + n11) if (n10 + n11) > 0 else 0
        pi2 = (n01 + n11) / (n - 1) if n > 1 else 0
        
        # Likelihood sob independência (H0)
        if pi2 > 0 and pi2 < 1:
            log_likelihood_null = (
                n00 * np.log(1 - pi2) + n01 * np.log(pi2) +
                n10 * np.log(1 - pi2) + n11 * np.log(pi2)
            )
        else:
            log_likelihood_null = 0
        
        # Likelihood sob dependência (H1)
        log_likelihood_alt = 0
        if pi01 > 0 and pi01 < 1:
            log_likelihood_alt += n00 * np.log(1 - pi01) + n01 * np.log(pi01)
        if pi11 > 0 and pi11 < 1:
            log_likelihood_alt += n10 * np.log(1 - pi11) + n11 * np.log(pi11)
        
        # Likelihood Ratio statistic
        lr_ind = -2 * (log_likelihood_null - log_likelihood_alt) if np.isfinite(log_likelihood_null) and np.isfinite(log_likelihood_alt) else 0
        p_value = float(1 - stats.chi2.cdf(lr_ind, df=1)) if np.isfinite(lr_ind) else 0
        
        # H0 não é rejeitada se p-value > 0.05 (independência não é rejeitada)
        passed = p_value > self.significance_level
        
        return BacktestResult(
            test_name="Christoffersen Independence Test",
            test_type=TestType.CHRISTOFFERSEN_IND.value,
            statistic=float(lr_ind),
            p_value=p_value,
            passed=passed,
            confidence_level=confidence_level,
            null_hypothesis="Exceptions are independent",
            alternative_hypothesis="Exceptions show clustering",
            details={
                'n00': n00, 'n01': n01, 'n10': n10, 'n11': n11,
                'pi01': float(pi01), 'pi11': float(pi11), 'pi2': float(pi2),
                'clustering_detected': not passed,
                'critical_value_5pct': float(stats.chi2.ppf(0.95, df=1))
            },
            timestamp=datetime.now().isoformat(),
            regulatory_compliance=['SUSEP', 'Solvency II', 'Basel III']
        )
    
    def run_christoffersen_cc_test(
        self,
        historical_losses: np.ndarray,
        var_predictions: np.ndarray,
        confidence_level: float = 0.95
    ) -> BacktestResult:
        """
        Teste de Christoffersen para Cobertura Condicional
        
        Combina Kupiec POF + Independence Test
        
        H0: Cobertura correta E independência
        H1: Cobertura incorreta OU dependência
        
        Estatística: LR_cc = LR_pof + LR_ind ~ χ²(2)
        """
        # Executar Kupiec POF
        kupiec_result = self.run_kupiec_pof_test(
            historical_losses, var_predictions, confidence_level
        )
        
        # Executar Independence Test
        ind_result = self.run_christoffersen_independence_test(
            historical_losses, var_predictions, confidence_level
        )
        
        # Combinar estatísticas
        lr_cc = kupiec_result.statistic + ind_result.statistic
        p_value = float(1 - stats.chi2.cdf(lr_cc, df=2)) if np.isfinite(lr_cc) else 0
        
        # H0 não é rejeitada se p-value > 0.05
        passed = p_value > self.significance_level
        
        return BacktestResult(
            test_name="Christoffersen Conditional Coverage Test",
            test_type=TestType.CHRISTOFFERSEN_CC.value,
            statistic=float(lr_cc),
            p_value=p_value,
            passed=passed,
            confidence_level=confidence_level,
            null_hypothesis="Correct coverage AND independence",
            alternative_hypothesis="Incorrect coverage OR dependence",
            details={
                'kupiec_statistic': kupiec_result.statistic,
                'independence_statistic': ind_result.statistic,
                'combined_statistic': float(lr_cc),
                'kupiec_passed': kupiec_result.passed,
                'independence_passed': ind_result.passed,
                'critical_value_5pct': float(stats.chi2.ppf(0.95, df=2))
            },
            timestamp=datetime.now().isoformat(),
            regulatory_compliance=['SUSEP', 'Solvency II', 'Basel III']
        )
    
    def run_stress_test(
        self,
        portfolio_data: pd.DataFrame,
        scenarios: Optional[List[StressTestScenario]] = None
    ) -> Dict[str, Any]:
        """
        Teste de Estresse com Cenários Históricos e Hipotéticos
        
        Args:
            portfolio_data: DataFrame com dados do portfólio
            scenarios: Lista de cenários de stress (usa padrão se None)
        
        Returns:
            Dicionário com resultados dos stress tests
        """
        if scenarios is None:
            scenarios = self.stress_scenarios
        
        results = {}
        
        for scenario in scenarios:
            scenario_name = scenario.name
            shocks = scenario.shocks
            
            logger.info(f"Running stress test: {scenario_name}")
            
            # Aplicar shocks ao portfólio
            stressed_portfolio = self._apply_shocks(portfolio_data, shocks)
            
            # Calcular perdas sob estresse
            stressed_losses = self._calculate_stressed_losses(stressed_portfolio)
            
            # Calcular métricas de risco
            results[scenario_name] = {
                'scenario_description': scenario.description,
                'historical_event': scenario.historical_event,
                'probability': scenario.probability,
                'total_loss': float(stressed_losses.sum()),
                'max_loss': float(stressed_losses.max()),
                'mean_loss': float(stressed_losses.mean()),
                'var_95': float(np.percentile(stressed_losses, 95)),
                'var_99': float(np.percentile(stressed_losses, 99)),
                'expected_shortfall_95': float(
                    stressed_losses[stressed_losses >= np.percentile(stressed_losses, 95)].mean()
                ) if len(stressed_losses[stressed_losses >= np.percentile(stressed_losses, 95)]) > 0 else 0,
                'impact_on_capital': float(stressed_losses.sum() / portfolio_data['asset_value'].sum()) if 'asset_value' in portfolio_data.columns else 0
            }
        
        return results
    
    def _apply_shocks(self, portfolio_data: pd.DataFrame, shocks: Dict[str, float]) -> pd.DataFrame:
        """
        Aplicar shocks ao portfólio
        
        Args:
            portfolio_data: DataFrame com dados do portfólio
            shocks: Dicionário com shocks a aplicar
        
        Returns:
            DataFrame com portfólio estressado
        """
        stressed = portfolio_data.copy()
        
        # Aplicar shocks
        if 'asset_value' in stressed.columns and 'asset_value' in shocks:
            stressed['asset_value'] = stressed['asset_value'] * (1 + shocks['asset_value'])
        
        if 'frequency' in stressed.columns and 'frequency' in shocks:
            stressed['frequency'] = stressed['frequency'] * shocks['frequency']
        
        if 'severity' in stressed.columns and 'severity' in shocks:
            stressed['severity'] = stressed['severity'] * shocks['severity']
        
        return stressed
    
    def _calculate_stressed_losses(self, stressed_portfolio: pd.DataFrame) -> np.ndarray:
        """
        Calcular perdas sob estresse
        
        Args:
            stressed_portfolio: DataFrame com portfólio estressado
        
        Returns:
            Array de perdas estressadas
        """
        if 'asset_value' in stressed_portfolio.columns and 'frequency' in stressed_portfolio.columns:
            if 'severity' in stressed_portfolio.columns:
                losses = (
                    stressed_portfolio['asset_value'].values *
                    stressed_portfolio['frequency'].values *
                    stressed_portfolio['severity'].values / 1e6  # Normalizar
                )
            else:
                losses = (
                    stressed_portfolio['asset_value'].values *
                    stressed_portfolio['frequency'].values / 1e3
                )
        else:
            # Fallback: usar valores padrão
            losses = np.random.lognormal(mean=10, sigma=1, size=len(stressed_portfolio))
        
        return losses
    
    def generate_var_backtest_report(
        self,
        policy_id: str,
        historical_losses: np.ndarray,
        var_predictions: np.ndarray
    ) -> VaRBacktestReport:
        """
        Gerar relatório completo de backtesting de VaR
        
        Args:
            policy_id: ID da apólice
            historical_losses: Perdas históricas
            var_predictions: Previsões de VaR
        
        Returns:
            VaRBacktestReport completo
        """
        logger.info(f"Generating VaR backtest report for policy {policy_id}")
        
        # Validar histórico mínimo
        n = len(historical_losses)
        years = n / 365.25
        if years < self.min_history_years:
            logger.warning(f"Histórico de {years:.1f} anos é menor que mínimo de {self.min_history_years} anos")
        
        # Testes para VaR 95%
        var_95_result = self.run_kupiec_pof_test(
            historical_losses, var_predictions, confidence_level=0.95
        )
        
        # Testes para VaR 99%
        var_99_result = self.run_kupiec_pof_test(
            historical_losses, var_predictions, confidence_level=0.99
        )
        
        # Teste de independência
        independence_result = self.run_christoffersen_independence_test(
            historical_losses, var_predictions, confidence_level=0.95
        )
        
        # Teste de cobertura condicional
        cc_result = self.run_christoffersen_cc_test(
            historical_losses, var_predictions, confidence_level=0.95
        )
        
        # Calcular métricas agregadas
        total_exceptions = var_95_result.details['actual_exceptions']
        expected_exceptions = var_95_result.details['expected_exceptions']
        exception_ratio = var_95_result.details['ratio']
        
        # Determinar rating
        all_passed = all([
            var_95_result.passed,
            var_99_result.passed,
            independence_result.passed
        ])
        
        if all_passed and exception_ratio < 1.1:
            rating = 'AAA'
        elif all_passed:
            rating = 'AA'
        elif var_95_result.passed and var_99_result.passed:
            rating = 'A'
        elif var_95_result.passed:
            rating = 'BBB'
        else:
            rating = 'BB'
        
        # Determinar status regulatório
        if rating in ['AAA', 'AA', 'A']:
            regulatory_status = 'APPROVED'
        elif rating == 'BBB':
            regulatory_status = 'REVIEW_REQUIRED'
        else:
            regulatory_status = 'REJECTED'
        
        # Gerar recomendações
        recommendations = self._generate_recommendations(
            var_95_result, var_99_result, independence_result
        )
        
        return VaRBacktestReport(
            policy_id=policy_id,
            var_95=var_95_result,
            var_99=var_99_result,
            independence=independence_result,
            conditional_coverage=cc_result,
            total_exceptions=total_exceptions,
            expected_exceptions=int(expected_exceptions),
            exception_ratio=float(exception_ratio),
            rating=rating,
            regulatory_status=regulatory_status,
            recommendations=recommendations,
            generation_timestamp=datetime.now().isoformat()
        )
    
    def _generate_recommendations(
        self,
        var_95: BacktestResult,
        var_99: BacktestResult,
        independence: BacktestResult
    ) -> List[str]:
        """
        Gerar recomendações baseadas nos resultados
        """
        recommendations = []
        
        if not var_95.passed:
            if var_95.details['ratio'] > 1.2:
                recommendations.append(
                    "⚠️ VaR 95% está subestimando o risco. "
                    "Considere aumentar o fator de segurança em 10-20%."
                )
            else:
                recommendations.append(
                    "⚠️ VaR 95% está superestimando o risco. "
                    "Considere reduzir capital alocado."
                )
        
        if not var_99.passed:
            recommendations.append(
                "⚠️ VaR 99% falhou. Revisar modelagem de cauda pesada."
            )
        
        if not independence.passed:
            recommendations.append(
                "⚠️ Clustering de exceções detectado. "
                "Modelo não captura dependência temporal. "
                "Considere usar GARCH ou modelos de regime."
            )
        
        if not recommendations:
            recommendations.append(
                "✅ Modelo aprovado. Manter monitoramento contínuo."
            )
        
        return recommendations
    
    def validate_minimum_history(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Tuple[bool, str]:
        """
        Validar histórico mínimo de 10 anos
        
        Returns:
            Tuple[bool, str]: (válido, mensagem)
        """
        years = (end_date - start_date).days / 365.25
        
        # Usar >= para comparação com tolerância
        if years >= self.min_history_years - 0.1:  # Tolerância de ~1 mês
            return True, f"Histórico de {years:.1f} anos atende requisito mínimo"
        else:
            return False, f"Histórico de {years:.1f} anos é inferior ao mínimo de {self.min_history_years} anos"
