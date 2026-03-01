"""
Unified Earth-Space Climate Platform
Plataforma Unificada Terra-Espaço para Análise Climática

Integra:
1. Atlas Digital de Desastres (dados históricos terrestres)
2. CelesTrak (dados de satélites e clima espacial)
3. OpenMeteo (dados climáticos em tempo real)
4. Oracle Simulation (payouts automáticos)
5. Blockchain (transações Hathor)

Arquitetura:
┌─────────────────────────────────────────────────────────┐
│            CLIMATEWISE UNIFIED PLATFORM                   │
├─────────────────────────────────────────────────────────┤
│  SPACE LAYER (CelesTrak)                                │
│  • Satellite tracking (TLE)                             │
│  • Conjunction alerts (SOCRATES)                        │
│  • Space weather (Kp index, solar storms)               │
│  • GPS/GNSS data                                        │
├─────────────────────────────────────────────────────────┤
│  ATMOSPHERE LAYER (OpenMeteo, INMET, NOAA)              │
│  • Real-time weather                                    │
│  • Climate indices                                      │
│  • Seasonal forecasts                                   │
├─────────────────────────────────────────────────────────┤
│  SURFACE LAYER (Atlas Digital)                          │
│  • Historical disasters (1991-2024)                     │
│  • Risk assessment                                      │
│  • Impact analysis                                      │
├─────────────────────────────────────────────────────────┤
│  ORACLE LAYER (Simulation + Real Data)                  │
│  • Parametric triggers                                  │
│  • Automated payouts                                    │
│  • Blockchain settlement                                │
└─────────────────────────────────────────────────────────┘
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from services.atlas_disaster_service import AtlasDisasterService
from services.celestrak_service import CelesTrakService
from services.atlas_realtime_climate_service import AtlasRealTimeClimateService
from services.atlas_oracle_simulation_service import AtlasOracleSimulationService

logger = logging.getLogger(__name__)


class DataLayer(str, Enum):
    """Camadas de dados da plataforma"""
    SPACE = "space"
    ATMOSPHERE = "atmosphere"
    SURFACE = "surface"
    ORACLE = "oracle"


class RiskDomain(str, Enum):
    """Domínios de risco cobertos"""
    TERRESTRIAL = "terrestrial"  # Desastres naturais em terra
    SPACE = "space"              # Eventos espaciais
    ATMOSPHERIC = "atmospheric"  # Eventos climáticos
    CROSS_DOMAIN = "cross_domain"  # Eventos interconectados


@dataclass
class UnifiedRiskAssessment:
    """Avaliação unificada de risco Terra-Espaço"""
    assessment_id: str
    timestamp: datetime
    location: Dict[str, float]  # lat, lon, altitude (km)
    
    # Riscos por camada
    space_risk: Optional[Dict[str, Any]] = None
    atmospheric_risk: Optional[Dict[str, Any]] = None
    surface_risk: Optional[Dict[str, Any]] = None
    
    # Risco composto
    composite_risk_score: float = 0.0  # 0-10
    composite_risk_level: str = "UNKNOWN"
    
    # Correlações cruzadas
    cross_domain_correlations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Recomendações
    recommendations: List[str] = field(default_factory=list)
    
    # Metadados
    data_sources: List[str] = field(default_factory=list)
    confidence_score: float = 0.0


@dataclass
class IntegratedInsuranceProduct:
    """Produto de seguro integrado Terra-Espaço"""
    product_id: str
    name: str
    description: str
    
    # Domínios cobertos
    covered_domains: List[RiskDomain]
    
    # Triggers paramétricos
    triggers: List[Dict[str, Any]]
    
    # Estrutura de payout
    payout_structure: Dict[str, Any]
    
    # Prêmio
    premium_calculation: Dict[str, Any]
    
    # Dados necessários
    required_data_sources: List[str]


class UnifiedEarthSpacePlatform:
    """
    Plataforma Unificada Terra-Espaço
    
    Orquestra todos os serviços de dados para fornecer:
    1. Avaliação de risco composta
    2. Produtos de seguro integrados
    3. Oracle unificado para payouts
    4. Dashboard unificado
    """

    def __init__(self):
        """Inicializar plataforma unificada"""
        # Serviços de dados
        self.atlas_service = AtlasDisasterService()
        self.celestrak_service = CelesTrakService()
        self.realtime_climate = AtlasRealTimeClimateService()
        self.oracle_simulation = AtlasOracleSimulationService()
        
        # Cache de avaliações
        self._risk_cache: Dict[str, UnifiedRiskAssessment] = {}
        
        logger.info("UnifiedEarthSpacePlatform initialized")

    def get_unified_risk_assessment(
        self,
        latitude: float,
        longitude: float,
        altitude_km: float = 0.0,
        include_space: bool = True,
        include_atmosphere: bool = True,
        include_surface: bool = True,
    ) -> UnifiedRiskAssessment:
        """
        Obter avaliação unificada de risco
        
        Args:
            latitude: Latitude
            longitude: Longitude
            altitude_km: Altitude em km (0 = superfície, >400 = órbita)
            include_space: Incluir riscos espaciais
            include_atmosphere: Incluir riscos atmosféricos
            include_surface: Incluir riscos de superfície
            
        Returns:
            UnifiedRiskAssessment
        """
        logger.info(f"Getting unified risk assessment for ({latitude}, {longitude}, {altitude_km}km)")
        
        # Determinar domínios relevantes baseado na altitude
        if altitude_km > 100:
            # Órbita: foco em espaço
            primary_domain = RiskDomain.SPACE
        elif altitude_km > 10:
            # Atmosfera: foco em clima
            primary_domain = RiskDomain.ATMOSPHERIC
        else:
            # Superfície: foco em desastres terrestres
            primary_domain = RiskDomain.TERRESTRIAL
        
        # Coletar dados de cada camada
        assessment = UnifiedRiskAssessment(
            assessment_id=f"risk_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            location={
                'latitude': latitude,
                'longitude': longitude,
                'altitude_km': altitude_km,
            },
        )
        
        # Camada SPACE
        if include_space and altitude_km > 0:
            assessment.space_risk = self._get_space_risk(latitude, longitude, altitude_km)
            assessment.data_sources.append("CelesTrak")
        
        # Camada ATMOSPHERE
        if include_atmosphere:
            assessment.atmospheric_risk = self._get_atmospheric_risk(latitude, longitude)
            assessment.data_sources.append("OpenMeteo")
        
        # Camada SURFACE
        if include_surface and altitude_km < 10:
            assessment.surface_risk = self._get_surface_risk(latitude, longitude)
            assessment.data_sources.append("Atlas Digital")
        
        # Calcular risco composto
        assessment.composite_risk_score = self._calculate_composite_risk(assessment)
        assessment.composite_risk_level = self._get_risk_level(assessment.composite_risk_score)
        
        # Identificar correlações cruzadas
        assessment.cross_domain_correlations = self._find_cross_domain_correlations(assessment)
        
        # Gerar recomendações
        assessment.recommendations = self._generate_recommendations(assessment)
        
        # Calcular confidence score
        assessment.confidence_score = len(assessment.data_sources) / 3.0  # 0-1
        
        # Salvar no cache
        cache_key = f"{latitude}_{longitude}_{altitude_km}"
        self._risk_cache[cache_key] = assessment
        
        logger.info(f"Risk assessment complete: score={assessment.composite_risk_score:.2f}, level={assessment.composite_risk_level}")
        
        return assessment

    def _get_space_risk(
        self,
        latitude: float,
        longitude: float,
        altitude_km: float
    ) -> Dict[str, Any]:
        """Obter riscos da camada espacial"""
        risk = {
            'altitude_km': altitude_km,
            'in_orbit': altitude_km > 100,
            'conjunction_risk': None,
            'space_weather_risk': None,
            'radiation_risk': None,
        }
        
        if altitude_km > 100:
            # Obter alertas de conjunção
            alerts = self.celestrak_service.get_conjunction_alerts(
                min_probability=1e-6,
                max_distance_km=5.0
            )
            
            if alerts:
                max_prob = max(a.collision_probability for a in alerts)
                risk['conjunction_risk'] = {
                    'active_alerts': len(alerts),
                    'max_probability': max_prob,
                    'risk_level': 'HIGH' if max_prob > 1e-4 else 'MEDIUM' if max_prob > 1e-5 else 'LOW',
                }
            
            # Obter clima espacial
            space_weather = self.celestrak_service.get_space_weather()
            if space_weather:
                risk['space_weather_risk'] = {
                    'kp_index': space_weather.kp_index,
                    'geomagnetic_storm': space_weather.geomagnetic_storm,
                    'storm_level': space_weather.storm_level,
                    'risk_level': 'HIGH' if space_weather.kp_index >= 6 else 'MEDIUM' if space_weather.kp_index >= 4 else 'LOW',
                }
        
        return risk

    def _get_atmospheric_risk(
        self,
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        """Obter riscos da camada atmosférica"""
        # Obter dados climáticos em tempo real
        # (usando coordenadas aproximadas para demo)
        weather_data = self.realtime_climate.get_real_time_weather(
            city='sao_paulo',  # Em produção, usar geocoding reverso
            use_cache=True
        )
        
        if not weather_data:
            return {'error': 'No weather data available'}
        
        risk_indicators = weather_data.get('risk_indicators', {})
        
        return {
            'current_conditions': weather_data.get('current', {}),
            'risk_indicators': risk_indicators,
            'risk_score': risk_indicators.get('risk_score', 0),
            'risk_level': risk_indicators.get('risk_level', 'UNKNOWN'),
            'flood_risk': risk_indicators.get('flood_risk', False),
            'drought_risk': risk_indicators.get('drought_risk', False),
            'storm_risk': risk_indicators.get('storm_risk', False),
        }

    def _get_surface_risk(
        self,
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        """Obter riscos da camada de superfície"""
        # Em produção, buscar histórico do Atlas para esta localização
        # Aqui usamos dados simulados
        return {
            'historical_disasters': {
                'total_events': 15,  # Mock
                'most_common_type': 'inundacao',
                'average_severity': 3.2,
                'last_event_date': '2024-01-15',
            },
            'risk_score': 6.5,  # Mock
            'risk_level': 'HIGH',
            'flood_zone': True,
            'drought_prone': False,
            'earthquake_zone': False,
        }

    def _calculate_composite_risk(
        self,
        assessment: UnifiedRiskAssessment
    ) -> float:
        """Calcular risco composto (0-10)"""
        scores = []
        weights = []
        
        # Peso de cada camada baseado na altitude
        altitude = assessment.location.get('altitude_km', 0)
        
        if altitude > 100:
            # Órbita: espaço 60%, atmosfera 30%, superfície 10%
            space_weight, atm_weight, surface_weight = 0.6, 0.3, 0.1
        elif altitude > 10:
            # Atmosfera: espaço 20%, atmosfera 60%, superfície 20%
            space_weight, atm_weight, surface_weight = 0.2, 0.6, 0.2
        else:
            # Superfície: espaço 10%, atmosfera 30%, superfície 60%
            space_weight, atm_weight, surface_weight = 0.1, 0.3, 0.6
        
        # Espaço
        if assessment.space_risk:
            space_score = 0
            if assessment.space_risk.get('conjunction_risk'):
                prob = assessment.space_risk['conjunction_risk']['max_probability']
                space_score += min(10, -prob.log10() - 3) if prob > 0 else 0
            if assessment.space_risk.get('space_weather_risk'):
                kp = assessment.space_weather_risk['kp_index']
                space_score += kp * 1.5
            scores.append(space_score)
            weights.append(space_weight)
        
        # Atmosfera
        if assessment.atmospheric_risk:
            atm_score = assessment.atmospheric_risk.get('risk_score', 0) * 2
            scores.append(atm_score)
            weights.append(atm_weight)
        
        # Superfície
        if assessment.surface_risk:
            surface_score = assessment.surface_risk.get('risk_score', 0)
            scores.append(surface_score)
            weights.append(surface_weight)
        
        # Calcular média ponderada
        if not scores or not weights:
            return 0.0
        
        composite = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        return min(10.0, max(0.0, composite))

    def _get_risk_level(self, score: float) -> str:
        """Converter score para nível de risco"""
        if score >= 7.5:
            return "CRITICAL"
        elif score >= 5.0:
            return "HIGH"
        elif score >= 2.5:
            return "MEDIUM"
        else:
            return "LOW"

    def _find_cross_domain_correlations(
        self,
        assessment: UnifiedRiskAssessment
    ) -> List[Dict[str, Any]]:
        """Identificar correlações entre domínios"""
        correlations = []
        
        # Exemplo: Tempestade geomagnética → afeta clima terrestre
        if assessment.space_risk and assessment.space_risk.get('space_weather_risk'):
            if assessment.space_risk['space_weather_risk'].get('geomagnetic_storm'):
                correlations.append({
                    'type': 'space_weather_to_atmosphere',
                    'description': 'Tempestade geomagnética pode afetar padrões climáticos',
                    'confidence': 0.6,
                    'impact': 'Moderate impact on atmospheric circulation',
                })
        
        # Exemplo: Clima severo → afeta operações de satélite
        if assessment.atmospheric_risk and assessment.space_risk:
            if assessment.atmospheric_risk.get('storm_risk'):
                correlations.append({
                    'type': 'atmosphere_to_space',
                    'description': 'Tempestades podem afetar comunicações com satélites',
                    'confidence': 0.8,
                    'impact': 'Potential signal degradation',
                })
        
        return correlations

    def _generate_recommendations(
        self,
        assessment: UnifiedRiskAssessment
    ) -> List[str]:
        """Gerar recomendações baseadas no risco"""
        recommendations = []
        
        # Recomendações por nível de risco
        if assessment.composite_risk_level == "CRITICAL":
            recommendations.append("⚠️ RISCO CRÍTICO: Considerar evacuação ou ações emergenciais")
            recommendations.append("📡 Ativar monitoramento contínuo de todas as camadas")
        
        if assessment.composite_risk_level == "HIGH":
            recommendations.append("⚠️ RISCO ALTO: Revisar apólices de seguro")
            recommendations.append("🔔 Configurar alertas automáticos")
        
        # Recomendações específicas por domínio
        if assessment.space_risk:
            if assessment.space_risk.get('conjunction_risk'):
                recommendations.append("🛰️ Alerta de conjunção orbital detectado")
            if assessment.space_risk.get('space_weather_risk', {}).get('geomagnetic_storm'):
                recommendations.append("🌞 Tempestade geomagnética em andamento")
        
        if assessment.atmospheric_risk:
            if assessment.atmospheric_risk.get('flood_risk'):
                recommendations.append("🌊 Risco de inundação elevado")
            if assessment.atmospheric_risk.get('storm_risk'):
                recommendations.append("⛈️ Condições de tempestade detectadas")
        
        if assessment.surface_risk:
            if assessment.surface_risk.get('historical_disasters', {}).get('most_common_type') == 'inundacao':
                recommendations.append("📊 Histórico de inundações na região")
        
        return recommendations

    def get_integrated_insurance_products(self) -> List[IntegratedInsuranceProduct]:
        """
        Obter produtos de seguro integrados Terra-Espaço
        
        Returns:
            Lista de produtos disponíveis
        """
        products = [
            IntegratedInsuranceProduct(
                product_id="earth_space_comprehensive",
                name="Earth-Space Comprehensive Coverage",
                description="Cobertura integrada para riscos terrestres e espaciais",
                covered_domains=[
                    RiskDomain.TERRESTRIAL,
                    RiskDomain.SPACE,
                    RiskDomain.ATMOSPHERIC,
                ],
                triggers=[
                    {
                        'type': 'natural_disaster',
                        'source': 'Atlas Digital',
                        'conditions': {'severity_min': 3.5},
                    },
                    {
                        'type': 'space_weather',
                        'source': 'CelesTrak',
                        'conditions': {'kp_index_min': 7},
                    },
                    {
                        'type': 'satellite_conjunction',
                        'source': 'SOCRATES',
                        'conditions': {'probability_min': 1e-4},
                    },
                ],
                payout_structure={
                    'base_amount': 100000,
                    'multipliers': {
                        'critical': 2.0,
                        'high': 1.5,
                        'medium': 1.0,
                    },
                },
                premium_calculation={
                    'base_rate': 0.05,
                    'risk_adjustment': True,
                    'multi_domain_discount': 0.15,
                },
                required_data_sources=[
                    'Atlas Digital',
                    'CelesTrak',
                    'OpenMeteo',
                ],
            ),
            IntegratedInsuranceProduct(
                product_id="satellite_operator_bundle",
                name="Satellite Operator Bundle",
                description="Pacote completo para operadores de satélites",
                covered_domains=[
                    RiskDomain.SPACE,
                    RiskDomain.ATMOSPHERIC,
                ],
                triggers=[
                    {
                        'type': 'collision',
                        'source': 'SOCRATES',
                        'conditions': {'probability_min': 1e-4, 'distance_max_km': 100},
                    },
                    {
                        'type': 'geomagnetic_storm',
                        'source': 'CelesTrak',
                        'conditions': {'kp_index_min': 6},
                    },
                ],
                payout_structure={
                    'base_amount': 1000000,
                    'per_event_cap': 5000000,
                    'annual_cap': 20000000,
                },
                premium_calculation={
                    'base_rate': 0.08,
                    'orbit_adjustment': True,
                    'constellation_discount': 0.20,
                },
                required_data_sources=[
                    'CelesTrak TLE',
                    'SOCRATES Plus',
                    'NOAA SWPC',
                ],
            ),
            IntegratedInsuranceProduct(
                product_id="climate_resilience_package",
                name="Climate Resilience Package",
                description="Proteção contra eventos climáticos extremos",
                covered_domains=[
                    RiskDomain.TERRESTRIAL,
                    RiskDomain.ATMOSPHERIC,
                ],
                triggers=[
                    {
                        'type': 'flood',
                        'source': 'Atlas Digital',
                        'conditions': {'affected_min': 1000},
                    },
                    {
                        'type': 'drought',
                        'source': 'OpenMeteo',
                        'conditions': {'precipitation_max_mm': 50, 'duration_days': 30},
                    },
                    {
                        'type': 'severe_storm',
                        'source': 'OpenMeteo',
                        'conditions': {'wind_speed_min_kmh': 100},
                    },
                ],
                payout_structure={
                    'base_amount': 500000,
                    'index_based': True,
                    'formula': 'base * (severity / threshold)',
                },
                premium_calculation={
                    'base_rate': 0.06,
                    'historical_adjustment': True,
                    'mitigation_credit': 0.10,
                },
                required_data_sources=[
                    'Atlas Digital',
                    'OpenMeteo',
                    'INMET',
                ],
            ),
        ]
        
        return products


# Instância global
unified_platform = UnifiedEarthSpacePlatform()
