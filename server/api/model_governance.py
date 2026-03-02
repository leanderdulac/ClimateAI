"""
Model Governance API Endpoints
Regulatory compliance endpoints for model governance
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field, ConfigDict

from services.model_governance_service import (
    ModelGovernanceService,
    ChangeType,
    ModelStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["model-governance"])

# Instância global do serviço
governance_service = ModelGovernanceService()


# ============================================================================
# Request/Response Models
# ============================================================================

class RegisterModelRequest(BaseModel):
    """Request para registrar modelo"""
    model_id: str = Field(..., description="ID único do modelo")
    version: str = Field(..., description="Versão (ex: 1.0.0)")
    created_by: str = Field(..., description="Criador do modelo")
    validation_report: Optional[str] = Field(default=None, description="Relatório de validação")
    performance_metrics: Optional[Dict] = Field(default=None, description="Métricas de performance")

    model_config = ConfigDict(protected_namespaces=())


class ChangeRequestRequest(BaseModel):
    """Request para solicitar mudança"""
    model_id: str = Field(..., description="ID do modelo")
    change_type: str = Field(..., description="Tipo de mudança (parameter, algorithm, critical, etc)")
    description: str = Field(..., description="Descrição da mudança")
    justification: str = Field(..., description="Justificativa")
    impact_analysis: Dict = Field(..., description="Análise de impacto")
    requested_by: str = Field(..., description="Solicitante")
    rollback_plan: Optional[str] = Field(default=None, description="Plano de rollback")

    model_config = ConfigDict(protected_namespaces=())


class ApproveChangeRequest(BaseModel):
    """Request para aprovar mudança"""
    approved_by: str = Field(..., description="Aprovador")
    implementation_notes: Optional[str] = Field(default=None, description="Notas de implementação")


class RejectChangeRequest(BaseModel):
    """Request para rejeitar mudança"""
    rejected_by: str = Field(..., description="Rejeitador")
    rejection_reason: str = Field(..., description="Motivo da rejeição")


class ModelInfoResponse(BaseModel):
    """Resposta de informações do modelo"""
    model_id: str
    version: str
    status: str
    created_at: str
    created_by: str
    approved_by: Optional[str]
    validation_report: Optional[str]
    changes_from_previous: List[str]
    performance_metrics: Dict
    regulatory_approval: Dict

    model_config = ConfigDict(protected_namespaces=())


class ChangeRequestResponse(BaseModel):
    """Resposta de change request"""
    request_id: str
    model_id: str
    change_type: str
    description: str
    justification: str
    impact_analysis: Dict
    requested_by: str
    requested_at: str
    approved_by: Optional[str]
    approved_at: Optional[str]
    status: str

    model_config = ConfigDict(protected_namespaces=())


class GovernanceScoreResponse(BaseModel):
    """Resposta de governance score"""
    overall_score: float
    documentation_score: float
    validation_score: float
    change_management_score: float
    performance_score: float
    compliance_score: float
    rating: str
    recommendations: List[str]
    assessment_date: str


class GovernanceReportResponse(BaseModel):
    """Resposta de relatório de governança"""
    model_id: str
    current_version: str
    status: str
    governance_score: Dict
    change_history_summary: Dict
    regulatory_approvals: Dict
    performance_metrics: Dict
    assessment_date: str
    regulatory_compliance: List[str]

    model_config = ConfigDict(protected_namespaces=())


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/register-model", response_model=ModelInfoResponse)
async def register_model(request: RegisterModelRequest):
    """
    Registrar novo modelo com validação
    
    **Requisitos:**
    - Versionamento semântico (ex: 1.0.0)
    - Validation report (recomendado)
    - Performance metrics (recomendado)
    """
    try:
        model = governance_service.register_model(
            model_id=request.model_id,
            version=request.version,
            created_by=request.created_by,
            validation_report=request.validation_report,
            performance_metrics=request.performance_metrics
        )
        
        return ModelInfoResponse(
            model_id=model.model_id,
            version=model.version,
            status=model.status,
            created_at=model.created_at,
            created_by=model.created_by,
            approved_by=model.approved_by,
            validation_report=model.validation_report,
            changes_from_previous=model.changes_from_previous,
            performance_metrics=model.performance_metrics,
            regulatory_approval=model.regulatory_approval
        )
        
    except Exception as e:
        logger.error(f"Error registering model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/request-change", response_model=ChangeRequestResponse)
async def request_change(request: ChangeRequestRequest):
    """
    Solicitar mudança em modelo
    
    **Tipos de Mudança:**
    - parameter: Mudança de parâmetros
    - algorithm: Mudança de algoritmo
    - data_source: Mudança de fonte de dados
    - threshold: Mudança de threshold
    - critical: Mudança crítica (requer aprovação de 2+ membros)
    - bugfix: Correção de bug
    - performance: Melhoria de performance
    """
    try:
        change_type = ChangeType(request.change_type)
        
        change_request = governance_service.request_change(
            model_id=request.model_id,
            change_type=change_type,
            description=request.description,
            justification=request.justification,
            impact_analysis=request.impact_analysis,
            requested_by=request.requested_by,
            rollback_plan=request.rollback_plan
        )
        
        return ChangeRequestResponse(
            request_id=change_request.request_id,
            model_id=change_request.model_id,
            change_type=change_request.change_type,
            description=change_request.description,
            justification=change_request.justification,
            impact_analysis=change_request.impact_analysis,
            requested_by=change_request.requested_by,
            requested_at=change_request.requested_at,
            approved_by=change_request.approved_by,
            approved_at=change_request.approved_at,
            status=change_request.status
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error requesting change: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/approve-change/{request_id}")
async def approve_change(request_id: str, request: ApproveChangeRequest):
    """
    Aprovar mudança
    
    **Requisitos:**
    - Aprovador deve estar no comitê
    - Mudanças críticas requerem 2+ aprovações
    """
    try:
        success, message = governance_service.approve_change(
            request_id=request_id,
            approved_by=request.approved_by,
            implementation_notes=request.implementation_notes
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return {
            "success": True,
            "message": message,
            "request_id": request_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving change: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/reject-change/{request_id}")
async def reject_change(request_id: str, request: RejectChangeRequest):
    """
    Rejeitar mudança
    
    **Requisitos:**
    - Rejeitador deve estar no comitê
    - Motivo deve ser fornecido
    """
    try:
        success, message = governance_service.reject_change(
            request_id=request_id,
            rejected_by=request.rejected_by,
            rejection_reason=request.rejection_reason
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return {
            "success": True,
            "message": message,
            "request_id": request_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting change: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/model/{model_id}", response_model=ModelInfoResponse)
async def get_model_info(model_id: str):
    """
    Obter informações do modelo
    """
    try:
        model_info = governance_service.get_model_info(model_id)
        
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return ModelInfoResponse(**model_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/change-request/{request_id}", response_model=ChangeRequestResponse)
async def get_change_request(request_id: str):
    """
    Obter informações de change request
    """
    try:
        change_info = governance_service.get_change_request(request_id)
        
        if not change_info:
            raise HTTPException(status_code=404, detail="Change request not found")
        
        return ChangeRequestResponse(**change_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting change request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/model/{model_id}/change-history", response_model=List[ChangeRequestResponse])
async def get_model_change_history(model_id: str):
    """
    Obter histórico de mudanças do modelo
    """
    try:
        change_history = governance_service.get_model_change_history(model_id)
        
        return [ChangeRequestResponse(**change) for change in change_history]
        
    except Exception as e:
        logger.error(f"Error getting change history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/model/{model_id}/governance-score", response_model=GovernanceScoreResponse)
async def get_governance_score(model_id: str):
    """
    Calcular score de governança do modelo
    
    **Scores por Categoria:**
    - Documentation (20%)
    - Validation (25%)
    - Change Management (25%)
    - Performance (15%)
    - Compliance (15%)
    
    **Rating:**
    - AAA: >= 95
    - AA: >= 85
    - A: >= 75
    - BBB: >= 65
    - BB: >= 55
    - B: < 55
    """
    try:
        score = governance_service.calculate_governance_score(model_id)
        
        return GovernanceScoreResponse(
            overall_score=score.overall_score,
            documentation_score=score.documentation_score,
            validation_score=score.validation_score,
            change_management_score=score.change_management_score,
            performance_score=score.performance_score,
            compliance_score=score.compliance_score,
            rating=score.rating,
            recommendations=score.recommendations,
            assessment_date=score.assessment_date
        )
        
    except Exception as e:
        logger.error(f"Error calculating governance score: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/model/{model_id}/governance-report", response_model=GovernanceReportResponse)
async def get_governance_report(model_id: str):
    """
    Gerar relatório de governança para reguladores
    
    **Inclui:**
    - Informações do modelo
    - Governance score
    - Histórico de mudanças
    - Aprovações regulatórias
    - Performance metrics
    """
    try:
        report = governance_service.get_governance_report(model_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return GovernanceReportResponse(**report)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting governance report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/committee-members")
async def get_committee_members():
    """
    Obter membros do comitê de governança
    """
    return {
        "committee_members": governance_service.approval_committee,
        "total_members": len(governance_service.approval_committee)
    }


@router.get("/change-types")
async def get_change_types():
    """
    Obter tipos de mudança disponíveis
    """
    return {
        "change_types": [
            {
                "type": ct.value,
                "description": _get_change_type_description(ct.value),
                "approval_required": "2+ committee" if ct == ChangeType.CRITICAL else "1 committee"
            }
            for ct in ChangeType
        ]
    }


def _get_change_type_description(change_type: str) -> str:
    """Obter descrição do tipo de mudança"""
    descriptions = {
        'parameter': 'Mudança de parâmetros do modelo',
        'algorithm': 'Mudança de algoritmo',
        'data_source': 'Mudança de fonte de dados',
        'threshold': 'Mudança de threshold',
        'critical': 'Mudança crítica com impacto significativo',
        'bugfix': 'Correção de bug',
        'performance': 'Melhoria de performance'
    }
    return descriptions.get(change_type, 'Tipo de mudança não especificado')


@router.get("/example-model")
async def get_example_model():
    """
    Obter exemplo de modelo para referência
    """
    return {
        "example": {
            "model_id": "pricing_model_v1",
            "version": "1.0.0",
            "status": "approved",
            "created_by": "actuary_001",
            "validation_report": "Model validated with 95% accuracy",
            "performance_metrics": {
                "accuracy": 0.95,
                "precision": 0.93,
                "recall": 0.92
            },
            "regulatory_approval": {
                "susep": True,
                "solvency_ii": False,
                "ifrs_17": False
            }
        },
        "description": "Example model structure for governance"
    }
