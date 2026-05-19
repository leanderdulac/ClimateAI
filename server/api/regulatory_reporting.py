"""
Regulatory Reporting API Endpoints
Endpoints para geração e submissão de relatórios regulatórios
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field

from middleware.auth_middleware import require_admin, require_auditor
from models.schemas import User
from services.regulatory_reporting_service import (
    RegulatoryReportingService,
    RegulatoryFramework,
    ReportType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["regulatory-reporting"])

# Instância global do serviço
reporting_service = RegulatoryReportingService()


# ============================================================================
# Request/Response Models
# ============================================================================

class SUSEPReportRequest(BaseModel):
    """Request para criar relatório SUSEP"""
    entity_id: str = Field(..., description="CNPJ da seguradora")
    reporting_period_start: datetime = Field(..., description="Início do período")
    reporting_period_end: datetime = Field(..., description="Fim do período")
    dados_tecnicos: Dict = Field(..., description="Dados técnicos")
    dados_financeiros: Dict = Field(..., description="Dados financeiros")
    provisoes_tecnicas: Dict = Field(..., description="Provisões técnicas")


class SolvencyIIReportRequest(BaseModel):
    """Request para criar relatório Solvency II"""
    entity_id: str = Field(..., description="LEI da seguradora")
    reporting_period_start: datetime = Field(..., description="Início do período")
    reporting_period_end: datetime = Field(..., description="Fim do período")
    scr: float = Field(..., description="Solvency Capital Requirement")
    mcr: float = Field(..., description="Minimum Capital Requirement")
    own_funds: float = Field(..., description="Fundos próprios")
    risk_profile: Dict = Field(..., description="Perfil de risco")


class IFRS17ReportRequest(BaseModel):
    """Request para criar relatório IFRS 17"""
    entity_id: str = Field(..., description="Identificação da entidade")
    reporting_period_start: datetime = Field(..., description="Início do período")
    reporting_period_end: datetime = Field(..., description="Fim do período")
    csm: float = Field(..., description="Contractual Service Margin")
    liability_for_incurred_claims: float = Field(..., description="Passivo por sinistros")
    liability_for_remaining_coverage: float = Field(..., description="Passivo por cobertura")
    insurance_revenue: float = Field(..., description="Receita de seguros")


class SubmitReportRequest(BaseModel):
    """Request para submeter relatório"""
    submitted_by: str = Field(..., description="Responsável pela submissão")


class ApproveReportRequest(BaseModel):
    """Request para aprovar relatório"""
    approved_by: str = Field(..., description="Aprovador")


class ReportResponse(BaseModel):
    """Resposta de relatório"""
    report_id: str
    framework: str
    report_type: str
    entity_id: str
    reporting_period_start: str
    reporting_period_end: str
    generation_date: str
    status: str
    validation_errors: List[str]
    approval_info: Optional[Dict]


class ComplianceSummaryResponse(BaseModel):
    """Resumo de conformidade"""
    entity_id: str
    total_reports: int
    by_framework: Dict[str, int]
    by_status: Dict[str, int]
    compliance_score: float
    last_submission: Optional[str]


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/susep/create", response_model=ReportResponse)
async def create_susep_report(
    request: SUSEPReportRequest,
    current_user: User = Depends(require_admin),
):
    """
    Criar relatório para SUSEP (Circular 562/2015)
    
    **Requisitos:**
    - CNPJ da seguradora
    - Período de reporte (trimestral)
    - Dados técnicos do seguro paramétrico
    - Dados financeiros
    - Provisões técnicas
    """
    try:
        report = reporting_service.create_susep_report(
            entity_id=request.entity_id,
            reporting_period_start=request.reporting_period_start,
            reporting_period_end=request.reporting_period_end,
            dados_tecnicos=request.dados_tecnicos,
            dados_financeiros=request.dados_financeiros,
            provisoes_tecnicas=request.provisoes_tecnicas
        )
        
        return ReportResponse(
            report_id=report.report_id,
            framework=report.framework,
            report_type=report.report_type,
            entity_id=report.entity_id,
            reporting_period_start=report.reporting_period_start,
            reporting_period_end=report.reporting_period_end,
            generation_date=report.generation_date,
            status=report.status,
            validation_errors=report.validation_errors,
            approval_info=report.approval_info
        )
        
    except Exception as e:
        logger.error(f"Error creating SUSEP report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/solvency-ii/create", response_model=ReportResponse)
async def create_solvency_ii_report(
    request: SolvencyIIReportRequest,
    current_user: User = Depends(require_admin),
):
    """
    Criar relatório para Solvency II (QRTs)
    
    **Requisitos:**
    - LEI da seguradora
    - SCR (Solvency Capital Requirement)
    - MCR (Minimum Capital Requirement)
    - Own Funds (Fundos próprios)
    - Risk Profile (Perfil de risco)
    """
    try:
        report = reporting_service.create_solvency_ii_report(
            entity_id=request.entity_id,
            reporting_period_start=request.reporting_period_start,
            reporting_period_end=request.reporting_period_end,
            scr=request.scr,
            mcr=request.mcr,
            own_funds=request.own_funds,
            risk_profile=request.risk_profile
        )
        
        return ReportResponse(
            report_id=report.report_id,
            framework=report.framework,
            report_type=report.report_type,
            entity_id=report.entity_id,
            reporting_period_start=report.reporting_period_start,
            reporting_period_end=report.reporting_period_end,
            generation_date=report.generation_date,
            status=report.status,
            validation_errors=report.validation_errors,
            approval_info=report.approval_info
        )
        
    except Exception as e:
        logger.error(f"Error creating Solvency II report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/ifrs-17/create", response_model=ReportResponse)
async def create_ifrs_17_report(
    request: IFRS17ReportRequest,
    current_user: User = Depends(require_admin),
):
    """
    Criar relatório para IFRS 17
    
    **Requisitos:**
    - Identificação da entidade
    - CSM (Contractual Service Margin)
    - Liability for incurred claims
    - Liability for remaining coverage
    - Insurance revenue
    """
    try:
        report = reporting_service.create_ifrs_17_report(
            entity_id=request.entity_id,
            reporting_period_start=request.reporting_period_start,
            reporting_period_end=request.reporting_period_end,
            csm=request.csm,
            liability_for_incurred_claims=request.liability_for_incurred_claims,
            liability_for_remaining_coverage=request.liability_for_remaining_coverage,
            insurance_revenue=request.insurance_revenue
        )
        
        return ReportResponse(
            report_id=report.report_id,
            framework=report.framework,
            report_type=report.report_type,
            entity_id=report.entity_id,
            reporting_period_start=report.reporting_period_start,
            reporting_period_end=report.reporting_period_end,
            generation_date=report.generation_date,
            status=report.status,
            validation_errors=report.validation_errors,
            approval_info=report.approval_info
        )
        
    except Exception as e:
        logger.error(f"Error creating IFRS 17 report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/{report_id}/submit")
async def submit_report(
    report_id: str,
    request: SubmitReportRequest,
    current_user: User = Depends(require_admin),
):
    """
    Submeter relatório para regulador
    
    **Requisitos:**
    - Relatório deve estar validado
    - Sem erros de validação
    """
    try:
        success, message = reporting_service.submit_report(
            report_id=report_id,
            submitted_by=current_user.email
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return {
            "success": True,
            "message": message,
            "report_id": report_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/{report_id}/approve")
async def approve_report(
    report_id: str,
    request: ApproveReportRequest,
    current_user: User = Depends(require_admin),
):
    """
    Aprovar relatório internamente
    
    **Requisitos:**
    - Aprovador deve ter autorização
    """
    try:
        success, message = reporting_service.approve_report(
            report_id=report_id,
            approved_by=current_user.email
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return {
            "success": True,
            "message": message,
            "report_id": report_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    current_user: User = Depends(require_auditor),
):
    """
    Obter relatório por ID
    """
    try:
        report_data = reporting_service.get_report(report_id)
        
        if not report_data:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return ReportResponse(**report_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/entity/{entity_id}/reports", response_model=List[ReportResponse])
async def get_reports_by_entity(
    entity_id: str,
    current_user: User = Depends(require_auditor),
    framework: Optional[str] = Query(default=None, description="Framework regulatório")
):
    """
    Obter relatórios por entidade
    """
    try:
        reports = reporting_service.get_reports_by_entity(entity_id, framework)
        
        return [ReportResponse(**report) for report in reports]
        
    except Exception as e:
        logger.error(f"Error getting reports: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/{report_id}/submission-history", response_model=List[Dict])
async def get_submission_history(
    report_id: str,
    current_user: User = Depends(require_auditor),
):
    """
    Obter histórico de submissões do relatório
    """
    try:
        history = reporting_service.get_submission_history(report_id)
        
        return history
        
    except Exception as e:
        logger.error(f"Error getting submission history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/{report_id}/export-json")
async def export_report_to_json(
    report_id: str,
    current_user: User = Depends(require_auditor),
):
    """
    Exportar relatório para JSON
    """
    try:
        json_data = reporting_service.export_report_to_json(report_id)
        
        return {
            "report_id": report_id,
            "format": "json",
            "data": json_data
        }
        
    except Exception as e:
        logger.error(f"Error exporting report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/entity/{entity_id}/compliance-summary", response_model=ComplianceSummaryResponse)
async def get_regulatory_compliance_summary(
    entity_id: str,
    current_user: User = Depends(require_auditor),
):
    """
    Obter resumo de conformidade regulatória da entidade
    
    **Inclui:**
    - Total de relatórios
    - Relatórios por framework
    - Relatórios por status
    - Compliance score (0-100)
    - Última submissão
    """
    try:
        summary = reporting_service.get_regulatory_compliance_summary(entity_id)
        
        return ComplianceSummaryResponse(**summary)
        
    except Exception as e:
        logger.error(f"Error getting compliance summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/frameworks")
async def get_regulatory_frameworks():
    """
    Obter frameworks regulatórios suportados
    """
    return {
        "frameworks": [
            {
                "id": fw.value,
                "name": fw.name.replace('_', ' ').title(),
                "description": _get_framework_description(fw.value)
            }
            for fw in RegulatoryFramework
        ]
    }


def _get_framework_description(framework: str) -> str:
    """Obter descrição do framework"""
    descriptions = {
        'susep': 'Superintendência de Seguros Privados - Circular 562/2015 (Brasil)',
        'solvency_ii': 'Solvency II Directive (European Union)',
        'ifrs_17': 'IFRS 17 Insurance Contracts (International)',
        'basel_iii': 'Basel III Banking Regulations (International)'
    }
    return descriptions.get(framework, 'Framework regulatório')


@router.get("/report-types")
async def get_report_types():
    """
    Obter tipos de relatórios disponíveis
    """
    return {
        "report_types": [
            {
                "id": rt.value,
                "name": rt.name.replace('_', ' ').title(),
                "description": _get_report_type_description(rt.value)
            }
            for rt in ReportType
        ]
    }


def _get_report_type_description(report_type: str) -> str:
    """Obter descrição do tipo de relatório"""
    descriptions = {
        'quarterly': 'Relatório trimestral',
        'annual': 'Relatório anual',
        'ad_hoc': 'Relatório sob demanda',
        'stress_test': 'Teste de estresse'
    }
    return descriptions.get(report_type, 'Tipo de relatório')


@router.get("/example/susep")
async def get_example_susep_report():
    """
    Obter exemplo de relatório SUSEP para referência
    """
    return {
        "example": {
            "entity_id": "00.000.000/0001-00",
            "reporting_period_start": "2026-01-01T00:00:00",
            "reporting_period_end": "2026-03-31T23:59:59",
            "dados_tecnicos": {
                "modelo_precificacao": "ensemble_pricing_v1",
                "validacao_atuarial": "Parecer atuarial nº 001/2026",
                "eventos_cobertos": ["seca", "inundacao", "vento"],
                "regioes_atuacao": ["SP", "MG", "RJ"]
            },
            "dados_financeiros": {
                "premios_emitidos": 10000000.00,
                "sinistros_ocorridos": 3500000.00,
                "despesas_administrativas": 1500000.00,
                "resultado_tecnico": 5000000.00
            },
            "provisoes_tecnicas": {
                "provisao_sinistros": 2000000.00,
                "provisao_premios_nao_ganhos": 3000000.00,
                "provisao_riscos_em_curso": 1500000.00
            }
        },
        "description": "Example SUSEP report structure for parametric insurance"
    }
