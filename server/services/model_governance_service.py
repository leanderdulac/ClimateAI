"""
Model Governance Service
Implementa controles de governança embutidos no código para conformidade regulatória

Requisitos Regulatórios:
- SUSEP Circular 562/2015
- Solvency II
- IFRS 17
- Basel III
- SOX
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import os

logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    """Status do modelo"""
    DRAFT = "draft"
    VALIDATED = "validated"
    APPROVED = "approved"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class ChangeType(Enum):
    """Tipo de mudança"""
    PARAMETER = "parameter"
    ALGORITHM = "algorithm"
    DATA_SOURCE = "data_source"
    THRESHOLD = "threshold"
    CRITICAL = "critical"
    BUGFIX = "bugfix"
    PERFORMANCE = "performance"


class ChangeStatus(Enum):
    """Status da mudança"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


@dataclass
class ModelVersion:
    """Versão de modelo"""
    model_id: str
    version: str
    status: str
    created_at: str
    created_by: str
    approved_by: Optional[str]
    validation_report: Optional[str]
    changes_from_previous: List[str]
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    regulatory_approval: Dict[str, bool] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Converter para dicionário"""
        return asdict(self)


@dataclass
class ChangeRequest:
    """Solicitação de mudança"""
    request_id: str
    model_id: str
    change_type: str
    description: str
    justification: str
    impact_analysis: Dict[str, Any]
    requested_by: str
    requested_at: str
    approved_by: Optional[str]
    approved_at: Optional[str]
    status: str
    implementation_notes: Optional[str] = None
    rollback_plan: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Converter para dicionário"""
        return asdict(self)


@dataclass
class GovernanceScore:
    """Score de governança do modelo"""
    overall_score: float
    documentation_score: float
    validation_score: float
    change_management_score: float
    performance_score: float
    compliance_score: float
    rating: str  # AAA, AA, A, BBB, BB, B
    recommendations: List[str]
    assessment_date: str


class ModelGovernanceService:
    """
    Serviço de Governança de Modelos
    
    Implementa:
    - Change management workflow
    - Approval committee
    - Version control automático
    - Governance score calculation
    - Regulatory compliance tracking
    """
    
    def __init__(self):
        self.models: Dict[str, ModelVersion] = {}
        self.change_requests: Dict[str, ChangeRequest] = {}
        self.approval_committee = [
            'chief_actuary',
            'chief_risk_officer',
            'cto',
            'compliance_officer'
        ]
        
        # Thresholds de impacto
        self.impact_thresholds = {
            'premium_change_max': 0.10,  # Máximo 10% de mudança no prêmio
            'risk_change_max': 0.15,     # Máximo 15% de mudança no risco
            'performance_degradation_max': 0.05  # Máximo 5% de degradação
        }
        
        logger.info("ModelGovernanceService initialized")
    
    def register_model(
        self,
        model_id: str,
        version: str,
        created_by: str,
        validation_report: str = None,
        performance_metrics: Dict = None
    ) -> ModelVersion:
        """
        Registrar novo modelo com validação
        
        Args:
            model_id: ID único do modelo
            version: Versão (ex: "1.0.0")
            created_by: Criador do modelo
            validation_report: Relatório de validação
            performance_metrics: Métricas de performance
        
        Returns:
            ModelVersion registrada
        """
        model = ModelVersion(
            model_id=model_id,
            version=version,
            status=ModelStatus.VALIDATED.value,
            created_at=datetime.now().isoformat(),
            created_by=created_by,
            approved_by=None,
            validation_report=validation_report,
            changes_from_previous=[],
            performance_metrics=performance_metrics or {},
            regulatory_approval={
                'susep': False,
                'solvency_ii': False,
                'ifrs_17': False
            }
        )
        
        self.models[model_id] = model
        
        logger.info(f"Model registered: {model_id} v{version}")
        
        return model
    
    def request_change(
        self,
        model_id: str,
        change_type: ChangeType,
        description: str,
        justification: str,
        impact_analysis: Dict[str, Any],
        requested_by: str,
        rollback_plan: str = None
    ) -> ChangeRequest:
        """
        Solicitar mudança em modelo
        
        Args:
            model_id: ID do modelo
            change_type: Tipo de mudança
            description: Descrição da mudança
            justification: Justificativa
            impact_analysis: Análise de impacto
            requested_by: Solicitante
            rollback_plan: Plano de rollback
        
        Returns:
            ChangeRequest criada
        """
        # Validar impacto para mudanças críticas
        if change_type == ChangeType.CRITICAL:
            if not self._validate_critical_change_impact(impact_analysis):
                raise ValueError(
                    f"Impacto de mudança crítica excede limites: "
                    f"{impact_analysis}"
                )
        
        # Criar solicitação
        request = ChangeRequest(
            request_id=f"CR-{model_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            model_id=model_id,
            change_type=change_type.value,
            description=description,
            justification=justification,
            impact_analysis=impact_analysis,
            requested_by=requested_by,
            requested_at=datetime.now().isoformat(),
            approved_by=None,
            approved_at=None,
            status=ChangeStatus.PENDING.value,
            rollback_plan=rollback_plan
        )
        
        self.change_requests[request.request_id] = request
        
        logger.info(f"Change request created: {request.request_id}")
        
        return request
    
    def approve_change(
        self,
        request_id: str,
        approved_by: str,
        implementation_notes: str = None
    ) -> Tuple[bool, str]:
        """
        Aprovar mudança
        
        Para mudanças críticas, requer aprovação de pelo menos 2 membros do comitê
        
        Args:
            request_id: ID da solicitação
            approved_by: Aprovador
            implementation_notes: Notas de implementação
        
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        request = self.change_requests.get(request_id)
        if not request:
            return False, "Change request not found"
        
        # Verificar se aprovador está no comitê
        if approved_by not in self.approval_committee:
            return False, f"Aprovador {approved_by} não está no comitê"
        
        # Para mudanças críticas, requer aprovação de pelo menos 2 membros
        if request.change_type == ChangeType.CRITICAL.value:
            # Verificar se já tem aprovação anterior de membro diferente
            if request.approved_by and request.approved_by != approved_by:
                # Já tem 2 aprovações, aprovar definitivamente
                request.status = ChangeStatus.APPROVED.value
                request.approved_by = f"{request.approved_by}, {approved_by}"
                request.approved_at = datetime.now().isoformat()
                request.implementation_notes = implementation_notes
                
                # Aplicar mudança
                self._apply_change(request)
                
                logger.info(f"Critical change request approved with 2 approvals: {request_id}")
                return True, "Mudança crítica aprovada com 2 aprovações"
            else:
                # Primeira aprovação
                request.approved_by = approved_by
                request.approved_at = datetime.now().isoformat()
                request.status = ChangeStatus.IN_REVIEW.value
                request.implementation_notes = "Awaiting second committee approval"
                
                logger.info(f"First approval for critical change: {request_id}")
                return True, "Aguardando aprovação de mais 1 membro do comitê"
        
        # Para mudanças não-críticas, aprovação única
        request.approved_by = approved_by
        request.approved_at = datetime.now().isoformat()
        request.status = ChangeStatus.APPROVED.value
        request.implementation_notes = implementation_notes
        
        # Atualizar modelo
        self._apply_change(request)
        
        logger.info(f"Change request approved: {request_id}")
        
        return True, "Mudança aprovada com sucesso"
    
    def reject_change(
        self,
        request_id: str,
        rejected_by: str,
        rejection_reason: str
    ) -> Tuple[bool, str]:
        """
        Rejeitar mudança
        
        Args:
            request_id: ID da solicitação
            rejected_by: Rejeitador
            rejection_reason: Motivo da rejeição
        
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        request = self.change_requests.get(request_id)
        if not request:
            return False, "Change request not found"
        
        if rejected_by not in self.approval_committee:
            return False, f"Rejeitador {rejected_by} não está no comitê"
        
        request.status = ChangeStatus.REJECTED.value
        request.approved_by = rejected_by
        request.approved_at = datetime.now().isoformat()
        request.implementation_notes = f"Rejected: {rejection_reason}"
        
        logger.info(f"Change request rejected: {request_id}")
        
        return True, "Mudança rejeitada"
    
    def _validate_critical_change_impact(self, impact_analysis: Dict) -> bool:
        """
        Validar se impacto de mudança crítica está dentro dos limites
        
        Args:
            impact_analysis: Análise de impacto
        
        Returns:
            bool: True se dentro dos limites
        """
        premium_impact = abs(impact_analysis.get('premium_impact', 0))
        risk_impact = abs(impact_analysis.get('risk_impact', 0))
        performance_impact = abs(impact_analysis.get('performance_impact', 0))
        
        return (
            premium_impact <= self.impact_thresholds['premium_change_max'] and
            risk_impact <= self.impact_thresholds['risk_change_max'] and
            performance_impact <= self.impact_thresholds['performance_degradation_max']
        )
    
    def _get_committee_approvals(self, request_id: str) -> List[str]:
        """
        Obter aprovações do comitê para uma solicitação
        
        Args:
            request_id: ID da solicitação
        
        Returns:
            Lista de aprovadores
        """
        request = self.change_requests.get(request_id)
        if not request or not request.approved_by:
            return []
        
        if request.approved_by in self.approval_committee:
            return [request.approved_by]
        
        return []
    
    def _apply_change(self, request: ChangeRequest):
        """
        Aplicar mudança ao modelo
        
        Args:
            request: ChangeRequest aprovada
        """
        model = self.models.get(request.model_id)
        if not model:
            return
        
        # Atualizar versão
        current_version = model.version.split('.')
        if request.change_type == ChangeType.CRITICAL.value:
            current_version[0] = str(int(current_version[0]) + 1)
            current_version[1] = '0'
            current_version[2] = '0'
        elif request.change_type == ChangeType.ALGORITHM.value:
            current_version[1] = str(int(current_version[1]) + 1)
            current_version[2] = '0'
        else:
            current_version[2] = str(int(current_version[2]) + 1)
        
        new_version = '.'.join(current_version)
        
        # Criar nova versão do modelo
        new_model = ModelVersion(
            model_id=model.model_id,
            version=new_version,
            status=ModelStatus.APPROVED.value,
            created_at=datetime.now().isoformat(),
            created_by=model.created_by,
            approved_by=request.approved_by,
            validation_report=model.validation_report,
            changes_from_previous=[request.description],
            performance_metrics=model.performance_metrics,
            regulatory_approval=model.regulatory_approval
        )
        
        self.models[request.model_id] = new_model
        
        logger.info(f"Model {request.model_id} updated to v{new_version}")
    
    def calculate_governance_score(self, model_id: str) -> GovernanceScore:
        """
        Calcular score de governança do modelo
        
        Args:
            model_id: ID do modelo
        
        Returns:
            GovernanceScore
        """
        model = self.models.get(model_id)
        if not model:
            return GovernanceScore(
                overall_score=0.0,
                documentation_score=0.0,
                validation_score=0.0,
                change_management_score=0.0,
                performance_score=0.0,
                compliance_score=0.0,
                rating='B',
                recommendations=['Model not found'],
                assessment_date=datetime.now().isoformat()
            )
        
        # Calcular scores por categoria
        documentation_score = self._calculate_documentation_score(model)
        validation_score = self._calculate_validation_score(model)
        change_management_score = self._calculate_change_management_score(model_id)
        performance_score = self._calculate_performance_score(model)
        compliance_score = self._calculate_compliance_score(model)
        
        # Score overall (média ponderada)
        overall_score = (
            documentation_score * 0.20 +
            validation_score * 0.25 +
            change_management_score * 0.25 +
            performance_score * 0.15 +
            compliance_score * 0.15
        )
        
        # Determinar rating
        if overall_score >= 95:
            rating = 'AAA'
        elif overall_score >= 85:
            rating = 'AA'
        elif overall_score >= 75:
            rating = 'A'
        elif overall_score >= 65:
            rating = 'BBB'
        elif overall_score >= 55:
            rating = 'BB'
        else:
            rating = 'B'
        
        # Gerar recomendações
        recommendations = self._generate_recommendations(
            documentation_score,
            validation_score,
            change_management_score,
            performance_score,
            compliance_score
        )
        
        return GovernanceScore(
            overall_score=overall_score,
            documentation_score=documentation_score,
            validation_score=validation_score,
            change_management_score=change_management_score,
            performance_score=performance_score,
            compliance_score=compliance_score,
            rating=rating,
            recommendations=recommendations,
            assessment_date=datetime.now().isoformat()
        )
    
    def _calculate_documentation_score(self, model: ModelVersion) -> float:
        """Calcular score de documentação (0-100)"""
        score = 0.0
        
        # Validation report presente (40 pontos)
        if model.validation_report:
            score += 40
        
        # Performance metrics presentes (30 pontos)
        if model.performance_metrics and len(model.performance_metrics) > 0:
            score += 30
        
        # Changes documented (30 pontos)
        if model.changes_from_previous and len(model.changes_from_previous) > 0:
            score += 30
        
        return min(score, 100)
    
    def _calculate_validation_score(self, model: ModelVersion) -> float:
        """Calcular score de validação (0-100)"""
        score = 0.0
        
        # Model approved (50 pontos)
        if model.status == ModelStatus.APPROVED.value:
            score += 50
        elif model.status == ModelStatus.VALIDATED.value:
            score += 30
        
        # Approved by committee (50 pontos)
        if model.approved_by and model.approved_by in self.approval_committee:
            score += 50
        
        return min(score, 100)
    
    def _calculate_change_management_score(self, model_id: str) -> float:
        """Calcular score de change management (0-100)"""
        # Contar mudanças aprovadas vs rejeitadas
        model_changes = [
            cr for cr in self.change_requests.values()
            if cr.model_id == model_id
        ]
        
        if not model_changes:
            return 100.0  # Sem mudanças = score máximo
        
        approved = len([c for c in model_changes if c.status == ChangeStatus.APPROVED.value])
        rejected = len([c for c in model_changes if c.status == ChangeStatus.REJECTED.value])
        pending = len([c for c in model_changes if c.status == ChangeStatus.PENDING.value])
        
        total = len(model_changes)
        
        # Score baseado em taxa de aprovação e tempo de aprovação
        approval_rate = approved / total if total > 0 else 1.0
        pending_rate = pending / total if total > 0 else 0.0
        
        score = (
            approval_rate * 70 +  # 70 pontos para taxa de aprovação
            (1 - pending_rate) * 30  # 30 pontos para baixo pending
        )
        
        return min(max(score, 0), 100)
    
    def _calculate_performance_score(self, model: ModelVersion) -> float:
        """Calcular score de performance (0-100)"""
        if not model.performance_metrics:
            return 50.0  # Score padrão se sem métricas
        
        score = 0.0
        
        # Verificar métricas de performance
        if 'accuracy' in model.performance_metrics:
            accuracy = model.performance_metrics['accuracy']
            score += min(accuracy * 40, 40)  # Até 40 pontos
        
        if 'precision' in model.performance_metrics:
            precision = model.performance_metrics['precision']
            score += min(precision * 30, 30)  # Até 30 pontos
        
        if 'recall' in model.performance_metrics:
            recall = model.performance_metrics['recall']
            score += min(recall * 30, 30)  # Até 30 pontos
        
        return min(score, 100)
    
    def _calculate_compliance_score(self, model: ModelVersion) -> float:
        """Calcular score de compliance regulatório (0-100)"""
        if not model.regulatory_approval:
            return 0.0
        
        approvals = model.regulatory_approval.values()
        approved_count = sum(1 for a in approvals if a)
        
        # 3 regulatórios principais: SUSEP, Solvency II, IFRS 17
        score = (approved_count / 3) * 100
        
        return min(score, 100)
    
    def _generate_recommendations(
        self,
        documentation_score: float,
        validation_score: float,
        change_management_score: float,
        performance_score: float,
        compliance_score: float
    ) -> List[str]:
        """Gerar recomendações baseadas nos scores"""
        recommendations = []
        
        if documentation_score < 70:
            recommendations.append(
                "Melhorar documentação do modelo (validation report, performance metrics)"
            )
        
        if validation_score < 70:
            recommendations.append(
                "Obter aprovação formal do comitê de governança"
            )
        
        if change_management_score < 70:
            recommendations.append(
                "Reduzir pendências de change requests e melhorar taxa de aprovação"
            )
        
        if performance_score < 70:
            recommendations.append(
                "Melhorar métricas de performance (accuracy, precision, recall)"
            )
        
        if compliance_score < 70:
            recommendations.append(
                "Obter aprovações regulatórias (SUSEP, Solvency II, IFRS 17)"
            )
        
        if not recommendations:
            recommendations.append(
                "Modelo em conformidade. Manter monitoramento contínuo."
            )
        
        return recommendations
    
    def get_model_info(self, model_id: str) -> Optional[Dict]:
        """
        Obter informações do modelo
        
        Args:
            model_id: ID do modelo
        
        Returns:
            Dict com informações do modelo ou None
        """
        model = self.models.get(model_id)
        if not model:
            return None
        
        return model.to_dict()
    
    def get_change_request(self, request_id: str) -> Optional[Dict]:
        """
        Obter informações de change request
        
        Args:
            request_id: ID da solicitação
        
        Returns:
            Dict com informações ou None
        """
        request = self.change_requests.get(request_id)
        if not request:
            return None
        
        return request.to_dict()
    
    def get_model_change_history(self, model_id: str) -> List[Dict]:
        """
        Obter histórico de mudanças do modelo
        
        Args:
            model_id: ID do modelo
        
        Returns:
            Lista de change requests
        """
        model_changes = [
            cr.to_dict() for cr in self.change_requests.values()
            if cr.model_id == model_id
        ]
        
        return sorted(
            model_changes,
            key=lambda x: x['requested_at'],
            reverse=True
        )
    
    def get_governance_report(self, model_id: str) -> Dict:
        """
        Gerar relatório de governança para reguladores
        
        Args:
            model_id: ID do modelo
        
        Returns:
            Dict com relatório completo
        """
        model = self.models.get(model_id)
        if not model:
            return {}
        
        governance_score = self.calculate_governance_score(model_id)
        change_history = self.get_model_change_history(model_id)
        
        return {
            'model_id': model_id,
            'current_version': model.version,
            'status': model.status,
            'governance_score': governance_score.to_dict() if hasattr(governance_score, 'to_dict') else asdict(governance_score),
            'change_history_summary': {
                'total_changes': len(change_history),
                'approved_changes': len([c for c in change_history if c['status'] == 'approved']),
                'rejected_changes': len([c for c in change_history if c['status'] == 'rejected']),
                'pending_changes': len([c for c in change_history if c['status'] == 'pending'])
            },
            'regulatory_approvals': model.regulatory_approval,
            'performance_metrics': model.performance_metrics,
            'assessment_date': governance_score.assessment_date,
            'regulatory_compliance': ['SUSEP', 'Solvency II', 'IFRS 17']
        }
