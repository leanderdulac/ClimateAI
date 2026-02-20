"""
Parametric Trigger Verification API Router
Endpoints para verificação de gatilhos paramétricos
"""

import logging
from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from datetime import datetime

from services.parametric_trigger_service import (
    ParametricTriggerService,
    ParametricPolicy,
    TriggerVerification,
    TriggerType,
    TriggerStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/parametric-triggers", tags=["parametric-triggers"])

# Instância global do serviço
trigger_service = ParametricTriggerService()


# ============================================================================
# Request/Response Models
# ============================================================================

class RegisterPolicyRequest(BaseModel):
    """Request para registrar apólice"""
    policy_id: str
    insured_id: str
    trigger_type: str
    threshold_value: float
    payout_amount: float
    location_latitude: float
    location_longitude: float
    start_date: str
    end_date: str


class PolicyResponse(BaseModel):
    """Resposta de apólice"""
    policy_id: str
    insured_id: str
    trigger_type: str
    threshold_value: float
    payout_amount: float
    location_latitude: float
    location_longitude: float
    start_date: str
    end_date: str
    status: str


class TriggerVerificationResponse(BaseModel):
    """Resposta de verificação"""
    verification_id: str
    policy_id: str
    trigger_type: str
    trigger_status: str
    threshold_value: float
    actual_value: float
    trigger_date: Optional[str]
    verification_date: str
    payout_amount: float
    description: str
    data_source: str
    confidence_level: float


class VerifyTriggerRequest(BaseModel):
    """Request para verificar gatilho"""
    policy_id: str
    use_real_data: bool = True


class PayoutCalculationResponse(BaseModel):
    """Resposta de cálculo de indenização"""
    policy_id: str
    payout_amount: float
    description: str
    triggered: bool


class ServiceStatusResponse(BaseModel):
    """Status do serviço"""
    service: str
    status: str
    total_policies: int
    total_verifications: int
    triggered_count: int
    data_sources: Dict[str, str]


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/policies/register")
async def register_policy(request: RegisterPolicyRequest):
    """
    Registrar apólice paramétrica
    
    **Parâmetros:**
    - policy_id: ID único da apólice
    - insured_id: ID do segurado
    - trigger_type: rainfall, wind_speed, temperature, drought
    - threshold_value: Valor do gatilho
    - payout_amount: Valor de indenização
    - location: Latitude/Longitude da localização segurada
    - start_date/end_date: Período de cobertura
    """
    try:
        policy = ParametricPolicy(
            policy_id=request.policy_id,
            insured_id=request.insured_id,
            trigger_type=request.trigger_type,
            threshold_value=request.threshold_value,
            payout_amount=request.payout_amount,
            location_latitude=request.location_latitude,
            location_longitude=request.location_longitude,
            start_date=datetime.fromisoformat(request.start_date),
            end_date=datetime.fromisoformat(request.end_date),
            status='active'
        )
        
        trigger_service.register_policy(policy)
        
        return {
            "success": True,
            "message": f"Policy {policy.policy_id} registered successfully",
            "policy_id": policy.policy_id
        }
        
    except Exception as e:
        logger.error(f"Error registering policy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/verify", response_model=TriggerVerificationResponse)
async def verify_trigger(request: VerifyTriggerRequest):
    """
    Verificar se gatilho foi atingido
    
    **Processo:**
    1. Obter dados climáticos reais
    2. Comparar com threshold da apólice
    3. Calcular indenização se aplicável
    4. Retornar resultado da verificação
    """
    try:
        verification = trigger_service.verify_trigger(
            policy_id=request.policy_id,
            use_real_data=request.use_real_data
        )
        
        return TriggerVerificationResponse(
            verification_id=verification.verification_id,
            policy_id=verification.policy_id,
            trigger_type=verification.trigger_type,
            trigger_status=verification.trigger_status,
            threshold_value=verification.threshold_value,
            actual_value=verification.actual_value,
            trigger_date=verification.trigger_date.isoformat() if verification.trigger_date else None,
            verification_date=verification.verification_date.isoformat(),
            payout_amount=verification.payout_amount,
            description=verification.description,
            data_source=verification.data_source,
            confidence_level=verification.confidence_level
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error verifying trigger: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/calculate-payout", response_model=PayoutCalculationResponse)
async def calculate_payout(
    policy_id: str = Query(..., description="ID da apólice"),
    actual_value: Optional[float] = Query(default=None, description="Valor medido (opcional)")
):
    """
    Calcular valor de indenização
    
    **Retorna:**
    - payout_amount: Valor a ser pago
    - description: Explicação do cálculo
    - triggered: Se gatilho foi atingido
    """
    try:
        payout, description = trigger_service.calculate_payout(
            policy_id=policy_id,
            actual_value=actual_value
        )
        
        triggered = payout > 0
        
        return PayoutCalculationResponse(
            policy_id=policy_id,
            payout_amount=payout,
            description=description,
            triggered=triggered
        )
        
    except Exception as e:
        logger.error(f"Error calculating payout: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/policies/{policy_id}", response_model=PolicyResponse)
async def get_policy(policy_id: str):
    """
    Obter detalhes de uma apólice
    """
    policy = trigger_service.policies.get(policy_id)
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return PolicyResponse(
        policy_id=policy.policy_id,
        insured_id=policy.insured_id,
        trigger_type=policy.trigger_type,
        threshold_value=policy.threshold_value,
        payout_amount=policy.payout_amount,
        location_latitude=policy.location_latitude,
        location_longitude=policy.location_longitude,
        start_date=policy.start_date.isoformat(),
        end_date=policy.end_date.isoformat(),
        status=policy.status
    )


@router.get("/policies/{policy_id}/verifications", response_model=List[TriggerVerificationResponse])
async def get_policy_verifications(policy_id: str):
    """
    Obter histórico de verificações de uma apólice
    """
    verifications = trigger_service.get_policy_verifications(policy_id)
    
    return [
        TriggerVerificationResponse(
            verification_id=v.verification_id,
            policy_id=v.policy_id,
            trigger_type=v.trigger_type,
            trigger_status=v.trigger_status,
            threshold_value=v.threshold_value,
            actual_value=v.actual_value,
            trigger_date=v.trigger_date.isoformat() if v.trigger_date else None,
            verification_date=v.verification_date.isoformat(),
            payout_amount=v.payout_amount,
            description=v.description,
            data_source=v.data_source,
            confidence_level=v.confidence_level
        )
        for v in verifications
    ]


@router.get("/triggered-policies", response_model=List[PolicyResponse])
async def get_triggered_policies():
    """
    Obter apólices com gatilhos atingidos
    """
    policies = trigger_service.get_triggered_policies()
    
    return [
        PolicyResponse(
            policy_id=p.policy_id,
            insured_id=p.insured_id,
            trigger_type=p.trigger_type,
            threshold_value=p.threshold_value,
            payout_amount=p.payout_amount,
            location_latitude=p.location_latitude,
            location_longitude=p.location_longitude,
            start_date=p.start_date.isoformat(),
            end_date=p.end_date.isoformat(),
            status=p.status
        )
        for p in policies
    ]


@router.get("/status", response_model=ServiceStatusResponse)
async def get_service_status():
    """
    Obter status do serviço de verificação
    """
    try:
        status = trigger_service.get_service_status()
        
        return ServiceStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"Error getting service status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/example")
async def get_example():
    """
    Obter exemplo de uso
    """
    return {
        "example_policy": {
            "policy_id": "PARAM-001",
            "insured_id": "FARMER-123",
            "trigger_type": "rainfall",
            "threshold_value": 50.0,  # 50mm de chuva
            "payout_amount": 10000.0,  # R$ 10.000
            "location_latitude": -23.5505,
            "location_longitude": -46.6333,
            "start_date": "2026-01-01T00:00:00",
            "end_date": "2026-12-31T23:59:59",
            "status": "active"
        },
        "example_verification": {
            "verification_id": "VER-PARAM-001-20260216",
            "policy_id": "PARAM-001",
            "trigger_type": "rainfall",
            "trigger_status": "triggered",
            "threshold_value": 50.0,
            "actual_value": 75.5,  # 75.5mm medidos
            "trigger_date": "2026-02-16T10:00:00",
            "verification_date": "2026-02-16T12:00:00",
            "payout_amount": 10000.0,
            "description": "Gatilho atingido: 75.5mm >= 50mm threshold",
            "data_source": "Real",
            "confidence_level": 0.95
        },
        "trigger_types": {
            "rainfall": "Chuva acumulada (mm)",
            "wind_speed": "Velocidade do vento (km/h)",
            "temperature": "Temperatura extrema (°C)",
            "drought": "Seca (precipitação baixa)"
        },
        "verification_process": [
            "1. Registrar apólice paramétrica",
            "2. Aguardar período de cobertura",
            "3. Verificar gatilho automaticamente",
            "4. Calcular indenização se gatilho atingido",
            "5. Pagar segurado automaticamente"
        ]
    }
