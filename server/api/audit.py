"""
Audit Trail API Endpoints
Regulatory compliance endpoints for SOX, SUSEP, Solvency II, IFRS 17
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from pydantic import BaseModel, Field, ConfigDict
import json

from middleware.auth_middleware import require_admin, require_auditor
from models.schemas import User
from services.audit_trail_service import AuditTrailService, AuditEntry, AuditChainIntegrity

logger = logging.getLogger(__name__)

router = APIRouter()

# Instância global do serviço
audit_service = AuditTrailService()


# ============================================================================
# Request/Response Models
# ============================================================================

class AuditEntryRequest(BaseModel):
    """Request para adicionar entrada de audit"""
    operation: str = Field(..., description="Nome da operação")
    user_id: str = Field(..., description="ID do usuário")
    policy_id: str = Field(..., description="ID da apólice")
    input_data: Dict = Field(..., description="Dados de entrada")
    output_data: Dict = Field(..., description="Dados de saída")
    model_version: str = Field(..., description="Versão do modelo")
    metadata: Optional[Dict] = Field(default=None, description="Metadados")

    model_config = ConfigDict(protected_namespaces=())


class AuditEntryResponse(BaseModel):
    """Resposta de entrada de audit"""
    entry_id: str
    timestamp: str
    operation: str
    user_id: str
    policy_id: str
    input_hash: str
    output_hash: str
    previous_hash: str
    model_version: str
    signature: str
    has_metadata: bool

    model_config = ConfigDict(protected_namespaces=())


class AuditTrailResponse(BaseModel):
    """Resposta de audit trail de policy"""
    policy_id: str
    total_entries: int
    entries: List[AuditEntryResponse]
    chain_valid: bool
    first_entry: str
    last_entry: str


class ChainIntegrityResponse(BaseModel):
    """Resposta de integridade da cadeia"""
    valid: bool
    total_entries: int
    first_entry_id: str
    last_entry_id: str
    broken_at: Optional[str]
    verification_timestamp: str


class RegulatoryExportResponse(BaseModel):
    """Resposta de exportação regulatória"""
    export_version: str
    export_timestamp: str
    policy_id: str
    chain_integrity: Dict
    summary: Dict
    entries_count: int
    regulatory_compliance: List[str]


class AuditStatsResponse(BaseModel):
    """Resposta de estatísticas"""
    total_entries: int
    operations: Dict[str, int]
    top_users: Dict[str, int]
    first_entry: str
    last_entry: str


class AddAuditEntryResponse(BaseModel):
    """Resposta ao adicionar entrada"""
    success: bool
    entry_id: str
    timestamp: str
    message: str


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/entry", response_model=AddAuditEntryResponse)
async def add_audit_entry(
    request: AuditEntryRequest,
    current_user: User = Depends(require_admin),
):
    """
    Adicionar entrada imutável ao audit trail
    
    **Requisitos Regulatórios:**
    - SOX (Sarbanes-Oxley)
    - SUSEP Circular 562/2015
    - Solvency II
    - IFRS 17
    
    **Dados Incluídos:**
    - Hash dos dados de entrada
    - Hash dos dados de saída
    - Hash da entrada anterior (hash chaining)
    - Signature criptográfica
    """
    try:
        entry = audit_service.add_entry(
            operation=request.operation,
            user_id=current_user.id,
            policy_id=request.policy_id,
            input_data=request.input_data,
            output_data=request.output_data,
            model_version=request.model_version,
            metadata=request.metadata
        )
        
        return AddAuditEntryResponse(
            success=True,
            entry_id=entry.entry_id,
            timestamp=entry.timestamp,
            message="Audit entry added successfully"
        )
        
    except Exception as e:
        logger.error(f"Error adding audit entry: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error adding audit entry: {str(e)}")


@router.get("/policy/{policy_id}", response_model=AuditTrailResponse)
async def get_policy_audit_trail(
    policy_id: str,
    current_user: User = Depends(require_auditor),
    limit: int = Query(default=100, ge=1, le=1000, description="Max entries to return")
):
    """
    Recuperar audit trail completo de uma apólice
    
    **Útil para:**
    - Auditoria de apólice específica
    - Reconstruir histórico de cálculos
    - Compliance regulatório
    """
    try:
        entries = audit_service.get_policy_audit_trail(policy_id)
        
        # Limitar resultados
        entries = entries[:limit]
        
        # Verificar integridade
        integrity = audit_service.verify_chain_integrity()
        
        return AuditTrailResponse(
            policy_id=policy_id,
            total_entries=len(entries),
            entries=[
                AuditEntryResponse(
                    entry_id=e.entry_id,
                    timestamp=e.timestamp,
                    operation=e.operation,
                    user_id=e.user_id,
                    policy_id=e.policy_id,
                    input_hash=e.input_hash,
                    output_hash=e.output_hash,
                    previous_hash=e.previous_hash,
                    model_version=e.model_version,
                    signature=e.signature,
                    has_metadata=bool(e.metadata)
                )
                for e in entries
            ],
            chain_valid=integrity.valid,
            first_entry=entries[0].timestamp if entries else None,
            last_entry=entries[-1].timestamp if entries else None
        )
        
    except Exception as e:
        logger.error(f"Error getting policy audit trail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/user/{user_id}", response_model=List[AuditEntryResponse])
async def get_user_activity(
    user_id: str,
    current_user: User = Depends(require_auditor),
    limit: int = Query(default=100, ge=1, le=500, description="Max entries"),
    hours: int = Query(default=24, ge=1, le=720, description="Last N hours")
):
    """
    Recuperar atividade de um usuário
    
    **Útil para:**
    - Monitorar atividade de usuários
    - Detectar comportamento anômalo
    - Auditoria de segurança
    """
    try:
        entries = audit_service.get_user_activity(user_id, limit)
        
        # Filtrar por tempo (últimas N horas)
        cutoff = datetime.now() - timedelta(hours=hours)
        entries = [
            e for e in entries 
            if datetime.fromisoformat(e.timestamp) > cutoff
        ]
        
        return [
            AuditEntryResponse(
                entry_id=e.entry_id,
                timestamp=e.timestamp,
                operation=e.operation,
                user_id=e.user_id,
                policy_id=e.policy_id,
                input_hash=e.input_hash,
                output_hash=e.output_hash,
                previous_hash=e.previous_hash,
                model_version=e.model_version,
                signature=e.signature,
                has_metadata=bool(e.metadata)
            )
            for e in entries
        ]
        
    except Exception as e:
        logger.error(f"Error getting user activity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/verify-chain", response_model=ChainIntegrityResponse)
async def verify_chain_integrity(current_user: User = Depends(require_auditor)):
    """
    Verificar integridade da cadeia de hashes
    
    **Importante para:**
    - Validar que nenhum dado foi adulterado
    - Compliance SOX
    - Auditoria externa
    """
    try:
        integrity = audit_service.verify_chain_integrity()
        
        return ChainIntegrityResponse(
            valid=integrity.valid,
            total_entries=integrity.total_entries,
            first_entry_id=integrity.first_entry_id,
            last_entry_id=integrity.last_entry_id,
            broken_at=integrity.broken_at,
            verification_timestamp=integrity.verification_timestamp
        )
        
    except Exception as e:
        logger.error(f"Error verifying chain: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/export/{policy_id}", response_model=RegulatoryExportResponse)
async def export_for_regulator(
    policy_id: str,
    current_user: User = Depends(require_auditor),
    format: str = Query(default="json", description="Export format (json, csv)")
):
    """
    Exportar audit trail para reguladores
    
    **Formatos Suportados:**
    - JSON (padrão)
    - CSV (em breve)
    
    **Conformidade:**
    - SUSEP
    - Solvency II
    - SOX
    - IFRS 17
    """
    try:
        export_data = audit_service.export_for_regulator(policy_id)
        
        return RegulatoryExportResponse(
            export_version=export_data['export_version'],
            export_timestamp=export_data['export_timestamp'],
            policy_id=policy_id,
            chain_integrity=export_data['chain_integrity'],
            summary=export_data['summary'],
            entries_count=len(export_data['entries']),
            regulatory_compliance=export_data['regulatory_compliance']
        )
        
    except Exception as e:
        logger.error(f"Error exporting for regulator: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/stats", response_model=AuditStatsResponse)
async def get_audit_stats(current_user: User = Depends(require_auditor)):
    """
    Obter estatísticas do audit trail
    
    **Inclui:**
    - Total de entradas
    - Operações por tipo
    - Top usuários
    - Período coberto
    """
    try:
        stats = audit_service.get_audit_stats()
        
        return AuditStatsResponse(
            total_entries=stats['total_entries'],
            operations=stats['operations'],
            top_users=stats['top_users'],
            first_entry=stats['first_entry'],
            last_entry=stats['last_entry']
        )
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/clear")
async def clear_audit_trail(
    current_user: User = Depends(require_admin),
    retention_days: int = Query(default=365, ge=30, le=2555, description="Days to retain")
):
    """
    Limpar audit trail antigo
    
    **Atenção:**
    - Requer privilégios de admin
    - Mantém últimos N dias (padrão: 365)
    - Não remove entradas sob investigação
    """
    try:
        audit_service.clear_audit_trail(retention_days)
        
        return {
            'success': True,
            'message': f"Audit trail cleared, retained last {retention_days} days",
            'retention_days': retention_days
        }
        
    except Exception as e:
        logger.error(f"Error clearing audit trail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/example")
async def get_example_audit_entry():
    """
    Obter exemplo de entrada de audit para referência
    """
    example = {
        "entry_id": "abc123...",
        "timestamp": "2026-02-16T23:00:00",
        "operation": "pricing_calculation",
        "user_id": "actuary_001",
        "policy_id": "POLICY_2026_001",
        "input_hash": "sha256...",
        "output_hash": "sha256...",
        "previous_hash": "sha256...",
        "model_version": "1.0.0",
        "signature": "sha256...",
        "metadata": {
            "calculation_method": "ensemble_pricing",
            "confidence_level": 0.95,
            "processing_time_ms": 245
        }
    }
    
    return {
        "example": example,
        "description": "Example audit trail entry structure",
        "hash_algorithm": "SHA-256",
        "chain_type": "Blockchain-like hash chaining"
    }


# ============================================================================
# Integration Helper
# ============================================================================

def log_audit_entry(
    operation: str,
    user_id: str,
    policy_id: str,
    input_data: Dict,
    output_data: Dict,
    model_version: str,
    metadata: Dict = None
):
    """
    Helper function para log de audit em outros módulos
    
    Uso:
    from api.audit import log_audit_entry
    
    log_audit_entry(
        operation="pricing_calculation",
        user_id=current_user.id,
        policy_id=policy.id,
        input_data=request.dict(),
        output_data=response.dict(),
        model_version="1.0.0"
    )
    """
    try:
        audit_service.add_entry(
            operation=operation,
            user_id=user_id,
            policy_id=policy_id,
            input_data=input_data,
            output_data=output_data,
            model_version=model_version,
            metadata=metadata
        )
    except Exception as e:
        logger.error(f"Failed to log audit entry: {e}", exc_info=True)
        # Não levantar exceção para não quebrar o fluxo principal
