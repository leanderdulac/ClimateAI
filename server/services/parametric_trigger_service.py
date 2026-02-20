"""
Parametric Trigger Verification Service
Serviço para verificação automática de gatilhos paramétricos

Funcionalidades:
- Verificar se gatilhos foram atingidos
- Calcular valor de indenização
- Notificar segurados
- Rastrear histórico de verificações
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np

from services.brazil_disaster_alerts_service import BrazilDisasterAlertService
from services.brazil_weather_service import BrazilWeatherService
from services.copernicus_service import CopernicusService

logger = logging.getLogger(__name__)


class TriggerStatus(Enum):
    """Status do gatilho"""
    NOT_TRIGGERED = "not_triggered"
    TRIGGERED = "triggered"
    PENDING_VERIFICATION = "pending_verification"
    EXPIRED = "expired"


class TriggerType(Enum):
    """Tipo de gatilho paramétrico"""
    RAINFALL = "rainfall"  # Chuva acumulada
    WIND_SPEED = "wind_speed"  # Velocidade do vento
    TEMPERATURE = "temperature"  # Temperatura extrema
    DROUGHT = "drought"  # Seca
    FLOOD = "flood"  # Inundação
    EARTHQUAKE = "earthquake"  # Terremoto (não implementado)


@dataclass
class TriggerVerification:
    """Resultado da verificação de gatilho"""
    verification_id: str
    policy_id: str
    trigger_type: str
    trigger_status: str
    threshold_value: float
    actual_value: float
    trigger_date: Optional[datetime]
    verification_date: datetime
    payout_amount: float
    description: str
    data_source: str
    confidence_level: float


@dataclass
class ParametricPolicy:
    """Apólice paramétrica"""
    policy_id: str
    insured_id: str
    trigger_type: str
    threshold_value: float
    payout_amount: float
    location_latitude: float
    location_longitude: float
    start_date: datetime
    end_date: datetime
    status: str  # active, expired, triggered, paid


class ParametricTriggerService:
    """
    Serviço de verificação de gatilhos paramétricos
    """
    
    def __init__(self):
        """Inicializar serviço"""
        self.disaster_alerts = BrazilDisasterAlertService()
        self.weather_service = BrazilWeatherService()
        self.copernicus_service = CopernicusService()
        
        # Cache de verificações
        self.verifications: Dict[str, TriggerVerification] = {}
        self.policies: Dict[str, ParametricPolicy] = {}
        
        logger.info("ParametricTriggerService initialized")
    
    def register_policy(self, policy: ParametricPolicy):
        """
        Registrar apólice paramétrica
        
        Args:
            policy: Apólice para registrar
        """
        self.policies[policy.policy_id] = policy
        logger.info(f"Policy {policy.policy_id} registered")
    
    def verify_trigger(
        self,
        policy_id: str,
        use_real_data: bool = True
    ) -> TriggerVerification:
        """
        Verificar se gatilho foi atingido
        
        Args:
            policy_id: ID da apólice
            use_real_data: Usar dados reais ou mock
        
        Returns:
            TriggerVerification com resultado
        """
        policy = self.policies.get(policy_id)
        
        if not policy:
            raise ValueError(f"Policy {policy_id} not found")
        
        # Verificar se apólice está ativa
        now = datetime.now()
        if not (policy.start_date <= now <= policy.end_date):
            return self._create_verification(
                policy=policy,
                status=TriggerStatus.EXPIRED,
                actual_value=0,
                payout=0,
                description="Apólice expirada"
            )
        
        # Obter dados climáticos
        if use_real_data:
            actual_value = self._get_actual_value(policy)
        else:
            actual_value = self._get_mock_value(policy)
        
        # Verificar se gatilho foi atingido
        threshold = policy.threshold_value
        
        # Lógica de verificação depende do tipo
        if policy.trigger_type == TriggerType.RAINFALL.value:
            triggered = actual_value >= threshold
        elif policy.trigger_type == TriggerType.WIND_SPEED.value:
            triggered = actual_value >= threshold
        elif policy.trigger_type == TriggerType.TEMPERATURE.value:
            # Temperatura pode ser máxima ou mínima
            triggered = abs(actual_value - threshold) > 5  # 5°C de diferença
        elif policy.trigger_type == TriggerType.DROUGHT.value:
            triggered = actual_value <= threshold  # Seca = valor baixo
        else:
            triggered = actual_value >= threshold
        
        status = TriggerStatus.TRIGGERED if triggered else TriggerStatus.NOT_TRIGGERED
        payout = policy.payout_amount if triggered else 0
        
        verification = self._create_verification(
            policy=policy,
            status=status,
            actual_value=actual_value,
            payout=payout,
            description=f"Gatilho {'atingido' if triggered else 'não atingido'}"
        )
        
        # Armazenar verificação
        self.verifications[verification.verification_id] = verification
        
        logger.info(
            f"Verification {verification.verification_id}: "
            f"status={status.value}, actual={actual_value}, threshold={threshold}"
        )
        
        return verification
    
    def _get_actual_value(self, policy: ParametricPolicy) -> float:
        """
        Obter valor real dos dados climáticos
        
        Args:
            policy: Apólice
        
        Returns:
            Valor atual medido
        """
        try:
            # Obter dados dos últimos dias
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            # Tentar múltiplas fontes
            sources = [
                self.weather_service.get_historical_data,
                self.copernicus_service.get_era5_data
            ]
            
            for source in sources:
                try:
                    data = source(
                        latitude=policy.location_latitude,
                        longitude=policy.location_longitude,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    if data:
                        return self._extract_value_from_data(policy, data)
                        
                except Exception as e:
                    logger.warning(f"Source failed: {e}")
                    continue
            
            # Fallback para mock
            return self._get_mock_value(policy)
            
        except Exception as e:
            logger.error(f"Error getting actual value: {e}")
            return self._get_mock_value(policy)
    
    def _extract_value_from_data(
        self,
        policy: ParametricPolicy,
        data: Any
    ) -> float:
        """
        Extrair valor relevante dos dados climáticos
        
        Args:
            policy: Apólice
            data: Dados climáticos
        
        Returns:
            Valor extraído
        """
        if policy.trigger_type == TriggerType.RAINFALL.value:
            # Somar precipitação dos últimos 7 dias
            if isinstance(data, list):
                return sum(getattr(d, 'precipitation', 0) for d in data)
            return 0
            
        elif policy.trigger_type == TriggerType.WIND_SPEED.value:
            # Máxima velocidade do vento
            if isinstance(data, list):
                return max(getattr(d, 'wind_speed', 0) for d in data)
            return 0
            
        elif policy.trigger_type == TriggerType.TEMPERATURE.value:
            # Temperatura média
            if isinstance(data, list):
                temps = [getattr(d, 'temperature_avg', getattr(d, 'temperature_2m', 0)) for d in data]
                return sum(temps) / len(temps) if temps else 0
            return 0
            
        elif policy.trigger_type == TriggerType.DROUGHT.value:
            # Precipitação acumulada (baixa = seca)
            if isinstance(data, list):
                return sum(getattr(d, 'precipitation', 0) for d in data)
            return 0
        
        return 0
    
    def _get_mock_value(self, policy: ParametricPolicy) -> float:
        """
        Gerar valor mock para desenvolvimento
        
        Args:
            policy: Apólice
        
        Returns:
            Valor mock
        """
        np.random.seed(hash(policy.policy_id) % 2**32)
        
        if policy.trigger_type == TriggerType.RAINFALL.value:
            # Chuva: 0-100mm
            return float(np.random.uniform(10, 80))
        elif policy.trigger_type == TriggerType.WIND_SPEED.value:
            # Vento: 20-120 km/h
            return float(np.random.uniform(40, 100))
        elif policy.trigger_type == TriggerType.TEMPERATURE.value:
            # Temperatura: 15-35°C
            return float(np.random.uniform(20, 30))
        elif policy.trigger_type == TriggerType.DROUGHT.value:
            # Seca: 0-50mm (baixo = seca)
            return float(np.random.uniform(5, 40))
        
        return 0
    
    def _create_verification(
        self,
        policy: ParametricPolicy,
        status: TriggerStatus,
        actual_value: float,
        payout: float,
        description: str
    ) -> TriggerVerification:
        """
        Criar objeto de verificação
        
        Args:
            policy: Apólice
            status: Status do gatilho
            actual_value: Valor medido
            payout: Valor de indenização
            description: Descrição
        
        Returns:
            TriggerVerification
        """
        verification_id = f"VER-{policy.policy_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Determinar fonte de dados
        data_source = "Mock" if actual_value == self._get_mock_value(policy) else "Real"
        
        # Calcular nível de confiança
        confidence = 0.95 if data_source == "Real" else 0.70
        
        return TriggerVerification(
            verification_id=verification_id,
            policy_id=policy.policy_id,
            trigger_type=policy.trigger_type,
            trigger_status=status.value,
            threshold_value=policy.threshold_value,
            actual_value=actual_value,
            trigger_date=datetime.now() if status == TriggerStatus.TRIGGERED else None,
            verification_date=datetime.now(),
            payout_amount=payout,
            description=description,
            data_source=data_source,
            confidence_level=confidence
        )
    
    def get_policy_verifications(
        self,
        policy_id: str
    ) -> List[TriggerVerification]:
        """
        Obter histórico de verificações de uma apólice
        
        Args:
            policy_id: ID da apólice
        
        Returns:
            Lista de verificações
        """
        return [
            v for v in self.verifications.values()
            if v.policy_id == policy_id
        ]
    
    def get_triggered_policies(self) -> List[ParametricPolicy]:
        """
        Obter apólices com gatilhos atingidos
        
        Returns:
            Lista de apólices triggeradas
        """
        triggered_policy_ids = set(
            v.policy_id for v in self.verifications.values()
            if v.trigger_status == TriggerStatus.TRIGGERED.value
        )
        
        return [
            p for p in self.policies.values()
            if p.policy_id in triggered_policy_ids
        ]
    
    def calculate_payout(
        self,
        policy_id: str,
        actual_value: float = None
    ) -> Tuple[float, str]:
        """
        Calcular valor de indenização
        
        Args:
            policy_id: ID da apólice
            actual_value: Valor medido (opcional)
        
        Returns:
            Tuple (payout_amount, description)
        """
        policy = self.policies.get(policy_id)
        
        if not policy:
            return 0, "Apólice não encontrada"
        
        if actual_value is None:
            actual_value = self._get_actual_value(policy)
        
        # Verificar se gatilho foi atingido
        threshold = policy.threshold_value
        
        if policy.trigger_type in [TriggerType.RAINFALL.value, TriggerType.WIND_SPEED.value]:
            triggered = actual_value >= threshold
        elif policy.trigger_type == TriggerType.DROUGHT.value:
            triggered = actual_value <= threshold
        else:
            triggered = actual_value >= threshold
        
        if triggered:
            return policy.payout_amount, f"Gatilho atingido: {actual_value} >= {threshold}"
        else:
            return 0, f"Gatilho não atingido: {actual_value} < {threshold}"
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Obter status do serviço
        
        Returns:
            Dict com status
        """
        return {
            'service': 'Parametric Trigger Verification',
            'status': 'active',
            'total_policies': len(self.policies),
            'total_verifications': len(self.verifications),
            'triggered_count': len([
                v for v in self.verifications.values()
                if v.trigger_status == TriggerStatus.TRIGGERED.value
            ]),
            'data_sources': {
                'brazil_weather': 'active',
                'copernicus': 'active',
                'disaster_alerts': 'active'
            }
        }
