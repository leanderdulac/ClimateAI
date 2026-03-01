"""
Atlas Integration Service
Integra os dados do Atlas Digital de Desastres com:
1. Oracle - para triggers de payout baseados em eventos históricos
2. Precificação - para cálculo de prêmios baseados em risco histórico
3. Base de dados históricos - para baseline de severidade

Arquitetura:
  Atlas (Dados Históricos) → Oracle (Baseline) → Pricing (Risk Score)
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class HistoricalRiskProfile:
    """
    Perfil de risco histórico baseado em dados do Atlas
    """
    location_latitude: float
    location_longitude: float
    municipio: str
    uf: str
    
    # Frequência de eventos
    total_eventos: int = 0
    eventos_por_ano: float = 0.0
    tipo_mais_comum: str = ""
    
    # Severidade histórica
    severidade_media: float = 0.0
    severidade_maxima: float = 0.0
    severidade_std: float = 0.0
    
    # Impacto humano
    total_mortes: int = 0
    total_afetados: int = 0
    mortes_por_evento: float = 0.0
    
    # Impacto econômico
    total_prejuizo: float = 0.0
    prejuizo_medio: float = 0.0
    
    # Tendência temporal
    tendencia_crescimento: float = 0.0  # positivo = aumentando
    
    # Score de risco composto (0-10)
    risk_score: float = 0.0
    risk_category: str = "UNKNOWN"  # BAIXO, MEDIO, ALTO, MUITO_ALTO
    
    # Metadados
    periodo_analise: Tuple[int, int] = (0, 0)
    fontes_dados: List[str] = field(default_factory=list)


@dataclass
class OracleBaselineEvent:
    """
    Evento baseline para o Oracle baseado em dados históricos do Atlas
    """
    event_id: str
    token_id: Optional[int]
    
    # Localização
    latitude: float
    longitude: float
    municipio: str
    uf: str
    
    # Tipo de evento
    disaster_type: str
    severity_category: str  # BAIXA, MEDIA, ALTA, MUITO_ALTA
    
    # Severidade calculada (1.0-5.0)
    severity_score: float
    severity_percentile: float  # Percentil histórico (0-100)
    
    # Probabilidade de ocorrência
    annual_probability: float  # 0-1
    return_period_years: float  # Período de retorno em anos
    
    # Impacto esperado
    expected_mortes: float
    expected_afetados: float
    expected_prejuizo: float
    
    # Trigger para payout
    payout_threshold_severity: float  # Severidade mínima para payout
    payout_percentage: float  # 0.0-1.0 (0-100%)
    
    # Baseline histórica
    historical_baseline: Dict[str, Any] = field(default_factory=dict)
    
    # Metadados
    calculation_date: datetime = field(default_factory=datetime.now)
    data_source: str = "Atlas Digital MDR"


class AtlasIntegrationService:
    """
    Serviço de integração do Atlas com Oracle e Precificação
    
    Funcionalidades:
    1. Calcular perfil de risco histórico por localização
    2. Gerar baseline para Oracle
    3. Ajustar precificação baseada em risco histórico
    4. Cross-check com eventos em tempo real
    """

    # Thresholds de severidade
    SEVERITY_THRESHOLDS = {
        'BAIXA': (1.0, 2.0),
        'MEDIA': (2.0, 3.0),
        'ALTA': (3.0, 4.0),
        'MUITO_ALTA': (4.0, 5.0),
    }
    
    # Pesos para cálculo de risk score
    RISK_WEIGHTS = {
        'frequencia': 0.25,
        'severidade': 0.30,
        'impacto_humanitario': 0.20,
        'impacto_economico': 0.15,
        'tendencia': 0.10,
    }

    def __init__(self, atlas_service=None, atlas_db_service=None):
        """
        Inicializar serviço de integração
        
        Args:
            atlas_service: AtlasDisasterService
            atlas_db_service: AtlasDatabaseService
        """
        self.atlas_service = atlas_service
        self.atlas_db_service = atlas_db_service
        
        # Cache de perfis de risco
        self._risk_cache: Dict[str, HistoricalRiskProfile] = {}
        
        logger.info("AtlasIntegrationService initialized")

    def calculate_historical_risk_profile(
        self,
        municipio: str,
        uf: str,
        latitude: float,
        longitude: float,
        anos: Tuple[int, int] = (1991, 2024),
    ) -> HistoricalRiskProfile:
        """
        Calcular perfil de risco histórico baseado em dados do Atlas
        
        Args:
            municipio: Nome do município
            uf: Sigla da UF
            latitude: Latitude
            longitude: Longitude
            anos: Período de análise (ano_inicial, ano_final)
            
        Returns:
            HistoricalRiskProfile com métricas de risco
        """
        logger.info(
            f"Calculating risk profile for {municipio}/{uf} ({anos[0]}-{anos[1]})"
        )
        
        # Verificar cache
        cache_key = f"{municipio}_{uf}_{anos[0]}_{anos[1]}"
        if cache_key in self._risk_cache:
            logger.info(f"Using cached risk profile for {cache_key}")
            return self._risk_cache[cache_key]
        
        # Inicializar perfil
        profile = HistoricalRiskProfile(
            location_latitude=latitude,
            location_longitude=longitude,
            municipio=municipio,
            uf=uf,
            periodo_analise=anos,
        )
        
        # Buscar dados históricos
        try:
            if self.atlas_service:
                # Carregar dados do Atlas
                df = self.atlas_service.load_data(use_cache=True)
                
                # Filtrar por município e período
                df_filtered = self.atlas_service.filter_disasters(
                    df=df,
                    anos=anos,
                    uf=uf,
                    municipio=municipio,
                )
                
                if len(df_filtered) > 0:
                    profile = self._compute_profile_from_dataframe(
                        profile=profile,
                        df=df_filtered,
                        anos=anos,
                    )
                    
        except Exception as e:
            logger.error(f"Erro ao calcular perfil de risco: {e}")
            profile.fontes_dados.append("ERRO_NO_CARREGAMENTO")
        
        # Calcular risk score composto
        profile.risk_score = self._calculate_composite_risk_score(profile)
        profile.risk_category = self._categorize_risk(profile.risk_score)
        profile.fontes_dados.append("Atlas Digital MDR")
        
        # Salvar no cache
        self._risk_cache[cache_key] = profile
        
        logger.info(
            f"Risk profile calculated: score={profile.risk_score:.2f}, "
            f"category={profile.risk_category}"
        )
        
        return profile

    def generate_oracle_baseline(
        self,
        risk_profile: HistoricalRiskProfile,
        token_id: Optional[int] = None,
        disaster_type: Optional[str] = None,
    ) -> OracleBaselineEvent:
        """
        Gerar evento baseline para o Oracle baseado em risco histórico
        
        Args:
            risk_profile: Perfil de risco histórico
            token_id: ID do token na blockchain (opcional)
            disaster_type: Tipo de desastre específico
            
        Returns:
            OracleBaselineEvent para configuração do Oracle
        """
        logger.info(f"Generating Oracle baseline for {risk_profile.municipio}/{risk_profile.uf}")
        
        # Calcular severidade score (1.0-5.0) baseado em percentil histórico
        severity_score = self._calculate_severity_score(risk_profile)
        severity_percentile = self._calculate_severity_percentile(risk_profile)
        
        # Calcular probabilidade anual
        annual_probability = min(1.0, risk_profile.eventos_por_ano / 10.0)
        
        # Calcular período de retorno (anos entre eventos significativos)
        if annual_probability > 0:
            return_period_years = 1.0 / annual_probability
        else:
            return_period_years = 100.0  # Evento muito raro
        
        # Determinar categoria de severidade
        severity_category = self._severity_score_to_category(severity_score)
        
        # Calcular thresholds para payout
        payout_threshold = self._calculate_payout_threshold(risk_profile, severity_score)
        payout_percentage = self._calculate_payout_percentage(severity_score)
        
        # Criar evento baseline
        baseline_event = OracleBaselineEvent(
            event_id=f"baseline_{risk_profile.municipio}_{risk_profile.uf}",
            token_id=token_id,
            latitude=risk_profile.location_latitude,
            longitude=risk_profile.location_longitude,
            municipio=risk_profile.municipio,
            uf=risk_profile.uf,
            disaster_type=disaster_type or risk_profile.tipo_mais_comum or "GENÉRICO",
            severity_category=severity_category,
            severity_score=severity_score,
            severity_percentile=severity_percentile,
            annual_probability=annual_probability,
            return_period_years=return_period_years,
            expected_mortes=risk_profile.total_mortes / max(1, risk_profile.total_eventos),
            expected_afetados=risk_profile.total_afetados / max(1, risk_profile.total_eventos),
            expected_prejuizo=risk_profile.prejuizo_medio,
            payout_threshold_severity=payout_threshold,
            payout_percentage=payout_percentage,
            historical_baseline={
                'total_eventos': risk_profile.total_eventos,
                'severidade_media': risk_profile.severidade_media,
                'severidade_maxima': risk_profile.severidade_maxima,
                'eventos_por_ano': risk_profile.eventos_por_ano,
                'tendencia_crescimento': risk_profile.tendencia_crescimento,
                'periodo_analise': risk_profile.periodo_analise,
            },
        )
        
        logger.info(
            f"Oracle baseline generated: severity={severity_score:.2f}, "
            f"payout_threshold={payout_threshold:.2f}, "
            f"return_period={return_period_years:.1f} years"
        )
        
        return baseline_event

    def adjust_pricing_for_historical_risk(
        self,
        base_premium: float,
        risk_profile: HistoricalRiskProfile,
        coverage_amount: float,
    ) -> Dict[str, Any]:
        """
        Ajustar precificação baseada em risco histórico do Atlas
        
        Args:
            base_premium: Prêmio base calculado por outros modelos
            risk_profile: Perfil de risco histórico
            coverage_amount: Valor de cobertura
            
        Returns:
            Dicionário com prêmio ajustado e fatores de ajuste
        """
        logger.info(f"Adjusting pricing for {risk_profile.municipio}/{risk_profile.uf}")
        
        # Fator de frequência (mais eventos = maior prêmio)
        freq_factor = 1.0 + (risk_profile.eventos_por_ano * 0.1)
        freq_factor = min(freq_factor, 3.0)  # Cap em 3x
        
        # Fator de severidade (severidade maior = maior prêmio)
        severity_factor = 1.0 + (risk_profile.severidade_media / 5.0)
        severity_factor = min(severity_factor, 2.5)
        
        # Fator de tendência (tendência crescente = maior prêmio)
        trend_factor = 1.0 + max(0, risk_profile.tendencia_crescimento * 0.2)
        trend_factor = min(trend_factor, 2.0)
        
        # Fator de impacto humano
        human_impact_factor = 1.0 + (risk_profile.mortes_por_evento * 0.05)
        human_impact_factor = min(human_impact_factor, 2.0)
        
        # Fator composto
        composite_factor = (
            freq_factor * self.RISK_WEIGHTS['frequencia'] +
            severity_factor * self.RISK_WEIGHTS['severidade'] +
            trend_factor * self.RISK_WEIGHTS['tendencia'] +
            human_impact_factor * self.RISK_WEIGHTS['impacto_humanitario']
        )
        
        # Normalizar fator composto (0.5 - 3.0)
        composite_factor = max(0.5, min(3.0, composite_factor * 2.0))
        
        # Calcular prêmio ajustado
        adjusted_premium = base_premium * composite_factor
        
        # Calcular prêmio por tipo de risco
        premium_breakdown = {
            'base_premium': base_premium,
            'frequency_adjustment': base_premium * (freq_factor - 1.0),
            'severity_adjustment': base_premium * (severity_factor - 1.0),
            'trend_adjustment': base_premium * (trend_factor - 1.0),
            'human_impact_adjustment': base_premium * (human_impact_factor - 1.0),
            'adjusted_premium': adjusted_premium,
        }
        
        # Calcular pure premium esperado (loss ratio esperado)
        expected_loss_ratio = self._calculate_expected_loss_ratio(risk_profile, coverage_amount)
        expected_losses = coverage_amount * expected_loss_ratio
        
        result = {
            'base_premium': base_premium,
            'adjusted_premium': adjusted_premium,
            'composite_factor': composite_factor,
            'factors': {
                'frequency': freq_factor,
                'severity': severity_factor,
                'trend': trend_factor,
                'human_impact': human_impact_factor,
            },
            'premium_breakdown': premium_breakdown,
            'expected_loss_ratio': expected_loss_ratio,
            'expected_losses': expected_losses,
            'risk_score': risk_profile.risk_score,
            'risk_category': risk_profile.risk_category,
        }
        
        logger.info(
            f"Pricing adjusted: base={base_premium:.2f}, "
            f"adjusted={adjusted_premium:.2f}, factor={composite_factor:.2f}"
        )
        
        return result

    def cross_check_real_time_event(
        self,
        real_time_severity: float,
        latitude: float,
        longitude: float,
        disaster_type: str,
    ) -> Dict[str, Any]:
        """
        Cross-check de evento em tempo real com baseline histórica
        
        Args:
            real_time_severity: Severidade do evento em tempo real (1.0-5.0)
            latitude: Latitude do evento
            longitude: Longitude do evento
            disaster_type: Tipo de desastre
            
        Returns:
            Dicionário com comparação e decisão de payout
        """
        logger.info(f"Cross-checking real-time event at ({latitude}, {longitude})")
        
        # Buscar município mais próximo (simplificado - em produção usaria geocoding)
        municipio, uf = self._get_nearest_municipio(latitude, longitude)
        
        # Obter perfil de risco histórico
        risk_profile = self.calculate_historical_risk_profile(
            municipio=municipio,
            uf=uf,
            latitude=latitude,
            longitude=longitude,
        )
        
        # Gerar baseline
        baseline = self.generate_oracle_baseline(
            risk_profile=risk_profile,
            disaster_type=disaster_type,
        )
        
        # Comparar severidade real-time com baseline
        severity_diff = real_time_severity - baseline.severity_score
        severity_ratio = real_time_severity / max(0.1, baseline.severity_score)
        
        # Percentil do evento atual na distribuição histórica
        current_percentile = self._calculate_event_percentile(
            real_time_severity,
            risk_profile,
        )
        
        # Decisão de payout
        payout_triggered = real_time_severity >= baseline.payout_threshold_severity
        payout_percentage = baseline.payout_percentage if payout_triggered else 0.0
        
        # Se severidade > 4.0, payout automático independente da baseline
        if real_time_severity >= 4.5:
            payout_triggered = True
            payout_percentage = 1.0
            logger.warning(f"CRITICAL: Severity {real_time_severity} >= 4.5 → Automatic payout")
        
        result = {
            'real_time_severity': real_time_severity,
            'baseline_severity': baseline.severity_score,
            'severity_difference': severity_diff,
            'severity_ratio': severity_ratio,
            'current_percentile': current_percentile,
            'payout_triggered': payout_triggered,
            'payout_percentage': payout_percentage,
            'payout_threshold': baseline.payout_threshold_severity,
            'historical_context': {
                'total_historical_events': risk_profile.total_eventos,
                'average_severity': risk_profile.severidade_media,
                'max_severity': risk_profile.severidade_maxima,
                'return_period_years': baseline.return_period_years,
            },
            'recommendation': self._generate_recommendation(
                payout_triggered,
                severity_ratio,
                current_percentile,
            ),
        }
        
        logger.info(
            f"Cross-check complete: payout={payout_triggered}, "
            f"percentage={payout_percentage:.2f}, percentile={current_percentile:.1f}"
        )
        
        return result

    # ─── Métodos Auxiliares ─────────────────────────────────────────────

    def _compute_profile_from_dataframe(
        self,
        profile: HistoricalRiskProfile,
        df,
        anos: Tuple[int, int],
    ) -> HistoricalRiskProfile:
        """Computar métricas do perfil a partir de DataFrame"""
        import pandas as pd
        
        profile.total_eventos = len(df)
        
        # Eventos por ano
        years_span = max(1, anos[1] - anos[0] + 1)
        profile.eventos_por_ano = profile.total_eventos / years_span
        
        # Tipo mais comum
        if 'tipo_desastre' in df.columns:
            profile.tipo_mais_comum = df['tipo_desastre'].mode().iloc[0] if len(df) > 0 else ""
        
        # Severidade (mapear para 1.0-5.0)
        if 'intensidade' in df.columns:
            severity_map = {
                'Baixa': 1.5,
                'Média': 2.5,
                'Alta': 3.5,
                'Muito Alta': 4.5,
            }
            severidades = df['intensidade'].map(severity_map).dropna()
            if len(severidades) > 0:
                profile.severidade_media = severidades.mean()
                profile.severidade_maxima = severidades.max()
                profile.severidade_std = severidades.std()
        
        # Impacto humano
        if 'mortes_diretas' in df.columns:
            profile.total_mortes = int(df['mortes_diretas'].sum())
            profile.mortes_por_evento = profile.total_mortes / max(1, profile.total_eventos)
        
        if 'afetados' in df.columns:
            profile.total_afetados = int(df['afetados'].sum())
        
        # Impacto econômico
        if 'prejuizo_estimado' in df.columns:
            profile.total_prejuizo = float(df['prejuizo_estimado'].sum())
            profile.prejuizo_medio = profile.total_prejuizo / max(1, profile.total_eventos)
        
        # Tendência temporal
        if 'ano' in df.columns and len(df) > 5:
            # Regressão linear simples
            anos_data = df.groupby('ano').size().reset_index(name='count')
            if len(anos_data) > 2:
                x = anos_data['ano'].values
                y = anos_data['count'].values
                slope = np.polyfit(x, y, 1)[0]
                profile.tendencia_crescimento = slope / max(1, y.mean())
        
        return profile

    def _calculate_composite_risk_score(
        self,
        profile: HistoricalRiskProfile,
    ) -> float:
        """Calcular score de risco composto (0-10)"""
        score = 0.0
        
        # Frequência (0-2.5 pontos)
        freq_score = min(10, profile.eventos_por_ano) / 10.0 * 2.5
        
        # Severidade (0-3.0 pontos)
        severity_score = (profile.severidade_media / 5.0) * 3.0
        
        # Impacto humanitário (0-2.0 pontos)
        human_score = min(100, profile.mortes_por_evento * 10) / 100.0 * 2.0
        
        # Impacto econômico (0-1.5 pontos)
        economic_score = min(1000000, profile.prejuizo_medio) / 1000000.0 * 1.5
        
        # Tendência (0-1.0 ponto)
        trend_score = max(0, profile.tendencia_crescimento) * 0.5
        
        score = freq_score + severity_score + human_score + economic_score + trend_score
        
        return min(10.0, max(0.0, score))

    def _categorize_risk(self, risk_score: float) -> str:
        """Categorizar risco baseado no score"""
        if risk_score >= 7.5:
            return "MUITO_ALTO"
        elif risk_score >= 5.0:
            return "ALTO"
        elif risk_score >= 2.5:
            return "MEDIO"
        else:
            return "BAIXO"

    def _calculate_severity_score(
        self,
        profile: HistoricalRiskProfile,
    ) -> float:
        """Calcular severity score (1.0-5.0) baseado em percentil"""
        # Usar severidade média como base
        base_severity = profile.severidade_media
        
        # Ajustar por tendência
        if profile.tendencia_crescimento > 0.1:
            base_severity += 0.5
        
        # Clamp para 1.0-5.0
        return max(1.0, min(5.0, base_severity))

    def _calculate_severity_percentile(
        self,
        profile: HistoricalRiskProfile,
    ) -> float:
        """Calcular percentil de severidade (0-100)"""
        # Simplificado: mapear severity_score para percentil
        severity_score = self._calculate_severity_score(profile)
        return ((severity_score - 1.0) / 4.0) * 100.0

    def _severity_score_to_category(self, severity_score: float) -> str:
        """Converter severity score para categoria"""
        if severity_score >= 4.0:
            return "MUITO_ALTA"
        elif severity_score >= 3.0:
            return "ALTA"
        elif severity_score >= 2.0:
            return "MEDIA"
        else:
            return "BAIXA"

    def _calculate_payout_threshold(
        self,
        profile: HistoricalRiskProfile,
        severity_score: float,
    ) -> float:
        """Calcular threshold de severidade para payout"""
        # Threshold = severidade histórica + margem de segurança
        base_threshold = profile.severidade_media + 0.5
        
        # Ajustar por variabilidade
        if profile.severidade_std > 0.5:
            base_threshold += profile.severidade_std * 0.5
        
        # Clamp para 2.0-4.5
        return max(2.0, min(4.5, base_threshold))

    def _calculate_payout_percentage(
        self,
        severity_score: float,
    ) -> float:
        """Calcular porcentagem de payout baseada na severidade"""
        # Mapear severity (1.0-5.0) para payout (0.0-1.0)
        if severity_score < 2.0:
            return 0.25
        elif severity_score < 3.0:
            return 0.50
        elif severity_score < 4.0:
            return 0.75
        else:
            return 1.0

    def _calculate_expected_loss_ratio(
        self,
        profile: HistoricalRiskProfile,
        coverage_amount: float,
    ) -> float:
        """Calcular loss ratio esperado baseado em dados históricos"""
        if coverage_amount <= 0:
            return 0.0
        
        # Loss ratio = perdas esperadas / prêmio
        expected_annual_loss = (
            profile.eventos_por_ano *
            profile.prejuizo_medio
        )
        
        return min(1.0, expected_annual_loss / coverage_amount)

    def _calculate_event_percentile(
        self,
        real_time_severity: float,
        profile: HistoricalRiskProfile,
    ) -> float:
        """Calcular percentil do evento atual na distribuição histórica"""
        # Assumir distribuição normal com média e std do histórico
        mean = profile.severidade_media
        std = max(0.1, profile.severidade_std)
        
        # Z-score
        z = (real_time_severity - mean) / std
        
        # Converter para percentil (usando aproximação da normal cumulativa)
        from math import erf, sqrt
        percentile = (1 + erf(z / sqrt(2))) / 2 * 100
        
        return max(0, min(100, percentile))

    def _get_nearest_municipio(
        self,
        latitude: float,
        longitude: float,
    ) -> Tuple[str, str]:
        """Obter município mais próximo (simplificado)"""
        # Em produção, usaria geocoding reverso
        # Aqui, retornamos um município genérico baseado na latitude
        if latitude < -20:
            return "Porto Alegre", "RS"
        elif latitude < -10:
            return "São Paulo", "SP"
        elif latitude < 0:
            return "Brasília", "DF"
        else:
            return "Manaus", "AM"

    def _generate_recommendation(
        self,
        payout_triggered: bool,
        severity_ratio: float,
        percentile: float,
    ) -> str:
        """Gerar recomendação baseada na análise"""
        if payout_triggered and percentile >= 95:
            return "PAYOUT_AUTOMATICO - Evento extremo (>95º percentil)"
        elif payout_triggered:
            return "PAYOUT - Severidade acima do threshold"
        elif severity_ratio > 0.8:
            return "MONITORAR - Severidade接近 threshold"
        else:
            return "SEM_ACAO - Severidade dentro do esperado"


# Instância global
atlas_integration_service = AtlasIntegrationService()
