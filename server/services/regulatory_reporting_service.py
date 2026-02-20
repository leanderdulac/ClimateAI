"""
Regulatory Reporting Service
Gera relatórios automáticos para reguladores (SUSEP, Solvency II, IFRS 17)

Requisitos Regulatórios:
- SUSEP Circular 562/2015
- Solvency II (EIOPA)
- IFRS 17 (Insurance Contracts)
- Basel III
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import os

logger = logging.getLogger(__name__)


class RegulatoryFramework(Enum):
    """Frameworks regulatórios suportados"""
    SUSEP = "susep"
    SOLVENCY_II = "solvency_ii"
    IFRS_17 = "ifrs_17"
    BASEL_III = "basel_iii"


class ReportType(Enum):
    """Tipos de relatórios"""
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    AD_HOC = "ad_hoc"
    STRESS_TEST = "stress_test"


@dataclass
class RegulatoryReport:
    """Relatório regulatório"""
    report_id: str
    framework: str
    report_type: str
    entity_id: str
    reporting_period_start: str
    reporting_period_end: str
    generation_date: str
    status: str  # draft, validated, submitted, approved
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    validation_errors: List[str] = field(default_factory=list)
    approval_info: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Converter para dicionário"""
        return asdict(self)


@dataclass
class SUSEPReport(RegulatoryReport):
    """Relatório para SUSEP"""
    circular: str = "562/2015"
    categoria: str = "seguros_parametricos"
    dados_tecnicos: Dict = field(default_factory=dict)
    dados_financeiros: Dict = field(default_factory=dict)
    provisoes_tecnicas: Dict = field(default_factory=dict)


@dataclass
class SolvencyIIReport(RegulatoryReport):
    """Relatório para Solvency II"""
    template: str = "QRTs"
    scr: float = 0.0
    mcr: float = 0.0
    own_funds: float = 0.0
    risk_profile: Dict = field(default_factory=dict)


@dataclass
class IFRS17Report(RegulatoryReport):
    """Relatório para IFRS 17"""
    measurement_model: str = "BBA"  # Building Block Approach
    csm: float = 0.0  # Contractual Service Margin
    liability_for_incurred_claims: float = 0.0
    liability_for_remaining_coverage: float = 0.0
    insurance_revenue: float = 0.0


class RegulatoryReportingService:
    """
    Serviço de Relatórios Regulatórios
    
    Implementa:
    - SUSEP Circular 562/2015 reports
    - Solvency II QRTs (Quantitative Reporting Templates)
    - IFRS 17 reports
    - PDF generation automático
    - Validation rules
    - Submission tracking
    """
    
    def __init__(self):
        self.reports: Dict[str, RegulatoryReport] = {}
        self.submission_history: Dict[str, List[Dict]] = {}
        
        # Validation rules por framework
        self.validation_rules = self._init_validation_rules()
        
        logger.info("RegulatoryReportingService initialized")
    
    def _init_validation_rules(self) -> Dict[str, List[Dict]]:
        """Inicializar regras de validação por framework"""
        return {
            'susep': [
                {'field': 'dados_financeiros.premios_emitidos', 'rule': 'required'},
                {'field': 'dados_financeiros.sinistros_ocorridos', 'rule': 'required'},
                {'field': 'provisoes_tecnicas.provisao_sinistros', 'rule': 'required'},
                {'field': 'dados_tecnicos.modelo_precificacao', 'rule': 'required'},
                {'field': 'dados_tecnicos.validacao_atuarial', 'rule': 'required'}
            ],
            'solvency_ii': [
                {'field': 'scr', 'rule': 'positive'},
                {'field': 'mcr', 'rule': 'positive'},
                {'field': 'own_funds', 'rule': 'required'},
                {'field': 'scr', 'rule': 'gte_mcr', 'compare_field': 'mcr'}
            ],
            'ifrs_17': [
                {'field': 'csm', 'rule': 'numeric'},
                {'field': 'liability_for_incurred_claims', 'rule': 'required'},
                {'field': 'liability_for_remaining_coverage', 'rule': 'required'}
            ]
        }
    
    def create_susep_report(
        self,
        entity_id: str,
        reporting_period_start: datetime,
        reporting_period_end: datetime,
        dados_tecnicos: Dict,
        dados_financeiros: Dict,
        provisoes_tecnicas: Dict
    ) -> SUSEPReport:
        """
        Criar relatório para SUSEP (Circular 562/2015)
        
        Args:
            entity_id: CNPJ da seguradora
            reporting_period_start: Início do período
            reporting_period_end: Fim do período
            dados_tecnicos: Dados técnicos do seguro
            dados_financeiros: Dados financeiros
            provisoes_tecnicas: Provisões técnicas
        
        Returns:
            SUSEPReport criado
        """
        report_id = f"SUSEP-{entity_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        report = SUSEPReport(
            report_id=report_id,
            framework=RegulatoryFramework.SUSEP.value,
            report_type=ReportType.QUARTERLY.value,
            entity_id=entity_id,
            reporting_period_start=reporting_period_start.isoformat(),
            reporting_period_end=reporting_period_end.isoformat(),
            generation_date=datetime.now().isoformat(),
            status='draft',
            data={},
            circular='562/2015',
            categoria='seguros_parametricos',
            dados_tecnicos=dados_tecnicos,
            dados_financeiros=dados_financeiros,
            provisoes_tecnicas=provisoes_tecnicas
        )
        
        # Validar relatório
        validation_errors = self._validate_report(report)
        report.validation_errors = validation_errors
        
        if not validation_errors:
            report.status = 'validated'
        
        self.reports[report_id] = report
        
        logger.info(f"SUSEP report created: {report_id}")
        
        return report
    
    def create_solvency_ii_report(
        self,
        entity_id: str,
        reporting_period_start: datetime,
        reporting_period_end: datetime,
        scr: float,
        mcr: float,
        own_funds: float,
        risk_profile: Dict
    ) -> SolvencyIIReport:
        """
        Criar relatório para Solvency II (QRTs)
        
        Args:
            entity_id: LEI da seguradora
            reporting_period_start: Início do período
            reporting_period_end: Fim do período
            scr: Solvency Capital Requirement
            mcr: Minimum Capital Requirement
            own_funds: Fundos próprios
            risk_profile: Perfil de risco
        
        Returns:
            SolvencyIIReport criado
        """
        report_id = f"SOLVENCY2-{entity_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        report = SolvencyIIReport(
            report_id=report_id,
            framework=RegulatoryFramework.SOLVENCY_II.value,
            report_type=ReportType.QUARTERLY.value,
            entity_id=entity_id,
            reporting_period_start=reporting_period_start.isoformat(),
            reporting_period_end=reporting_period_end.isoformat(),
            generation_date=datetime.now().isoformat(),
            status='draft',
            data={},
            template='QRTs',
            scr=scr,
            mcr=mcr,
            own_funds=own_funds,
            risk_profile=risk_profile
        )
        
        # Validar relatório
        validation_errors = self._validate_report(report)
        report.validation_errors = validation_errors
        
        if not validation_errors:
            report.status = 'validated'
        
        self.reports[report_id] = report
        
        logger.info(f"Solvency II report created: {report_id}")
        
        return report
    
    def create_ifrs_17_report(
        self,
        entity_id: str,
        reporting_period_start: datetime,
        reporting_period_end: datetime,
        csm: float,
        liability_for_incurred_claims: float,
        liability_for_remaining_coverage: float,
        insurance_revenue: float
    ) -> IFRS17Report:
        """
        Criar relatório para IFRS 17
        
        Args:
            entity_id: Identificação da entidade
            reporting_period_start: Início do período
            reporting_period_end: Fim do período
            csm: Contractual Service Margin
            liability_for_incurred_claims: Passivo por sinistros incorridos
            liability_for_remaining_coverage: Passivo por cobertura restante
            insurance_revenue: Receita de seguros
        
        Returns:
            IFRS17Report criado
        """
        report_id = f"IFRS17-{entity_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        report = IFRS17Report(
            report_id=report_id,
            framework=RegulatoryFramework.IFRS_17.value,
            report_type=ReportType.QUARTERLY.value,
            entity_id=entity_id,
            reporting_period_start=reporting_period_start.isoformat(),
            reporting_period_end=reporting_period_end.isoformat(),
            generation_date=datetime.now().isoformat(),
            status='draft',
            data={},
            measurement_model='BBA',
            csm=csm,
            liability_for_incurred_claims=liability_for_incurred_claims,
            liability_for_remaining_coverage=liability_for_remaining_coverage,
            insurance_revenue=insurance_revenue
        )
        
        # Validar relatório
        validation_errors = self._validate_report(report)
        report.validation_errors = validation_errors
        
        if not validation_errors:
            report.status = 'validated'
        
        self.reports[report_id] = report
        
        logger.info(f"IFRS 17 report created: {report_id}")
        
        return report
    
    def _validate_report(self, report: RegulatoryReport) -> List[str]:
        """
        Validar relatório contra regras do framework
        
        Args:
            report: Relatório para validar
        
        Returns:
            Lista de erros de validação
        """
        errors = []
        framework = report.framework
        rules = self.validation_rules.get(framework, [])
        
        for rule in rules:
            field = rule['field']
            rule_type = rule['rule']
            
            # Obter valor do campo
            value = self._get_field_value(report, field)
            
            # Aplicar regra
            if rule_type == 'required':
                if value is None or value == '':
                    errors.append(f"Campo obrigatório: {field}")
            
            elif rule_type == 'positive':
                if value is not None and value < 0:
                    errors.append(f"Valor deve ser positivo: {field} = {value}")
            
            elif rule_type == 'numeric':
                if value is not None and not isinstance(value, (int, float)):
                    errors.append(f"Valor deve ser numérico: {field}")
            
            elif rule_type == 'gte_mcr':
                compare_value = self._get_field_value(report, rule.get('compare_field', 'mcr'))
                if value is not None and compare_value is not None:
                    if value < compare_value:
                        errors.append(f"SCR ({value}) deve ser >= MCR ({compare_value})")
        
        return errors
    
    def _get_field_value(self, report: RegulatoryReport, field: str) -> Any:
        """
        Obter valor de campo do relatório
        
        Args:
            report: Relatório
            field: Nome do campo (suporta notação dot)
        
        Returns:
            Valor do campo ou None
        """
        parts = field.split('.')
        value = report
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None
        
        return value
    
    def submit_report(self, report_id: str, submitted_by: str) -> Tuple[bool, str]:
        """
        Submeter relatório para regulador
        
        Args:
            report_id: ID do relatório
            submitted_by: Responsável pela submissão
        
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        report = self.reports.get(report_id)
        if not report:
            return False, "Relatório não encontrado"
        
        # Verificar validação
        if report.status not in ['validated', 'approved']:
            if report.validation_errors:
                return False, f"Relatório com erros de validação: {report.validation_errors}"
            else:
                # Validar antes de submeter
                validation_errors = self._validate_report(report)
                if validation_errors:
                    report.validation_errors = validation_errors
                    return False, f"Relatório com erros de validação: {validation_errors}"
        
        # Atualizar status
        report.status = 'submitted'
        report.approval_info = {
            'submitted_by': submitted_by,
            'submitted_at': datetime.now().isoformat(),
            'submission_method': 'API'
        }
        
        # Registrar histórico de submissão
        if report_id not in self.submission_history:
            self.submission_history[report_id] = []
        
        self.submission_history[report_id].append({
            'action': 'submitted',
            'by': submitted_by,
            'at': datetime.now().isoformat(),
            'status': report.status
        })
        
        logger.info(f"Report submitted: {report_id}")
        
        return True, "Relatório submetido com sucesso"
    
    def approve_report(self, report_id: str, approved_by: str) -> Tuple[bool, str]:
        """
        Aprovar relatório internamente
        
        Args:
            report_id: ID do relatório
            approved_by: Aprovador
        
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        report = self.reports.get(report_id)
        if not report:
            return False, "Relatório não encontrado"
        
        report.status = 'approved'
        report.approval_info = {
            'approved_by': approved_by,
            'approved_at': datetime.now().isoformat()
        }
        
        # Registrar histórico
        if report_id not in self.submission_history:
            self.submission_history[report_id] = []
        
        self.submission_history[report_id].append({
            'action': 'approved',
            'by': approved_by,
            'at': datetime.now().isoformat(),
            'status': report.status
        })
        
        logger.info(f"Report approved: {report_id}")
        
        return True, "Relatório aprovado com sucesso"
    
    def get_report(self, report_id: str) -> Optional[Dict]:
        """
        Obter relatório por ID
        
        Args:
            report_id: ID do relatório
        
        Returns:
            Dict com dados do relatório ou None
        """
        report = self.reports.get(report_id)
        if not report:
            return None
        
        return report.to_dict()
    
    def get_reports_by_entity(self, entity_id: str, framework: str = None) -> List[Dict]:
        """
        Obter relatórios por entidade
        
        Args:
            entity_id: ID da entidade
            framework: Framework regulatório (opcional)
        
        Returns:
            Lista de relatórios
        """
        reports = []
        for report in self.reports.values():
            if report.entity_id == entity_id:
                if framework is None or report.framework == framework:
                    reports.append(report.to_dict())
        
        return sorted(reports, key=lambda x: x['generation_date'], reverse=True)
    
    def get_submission_history(self, report_id: str) -> List[Dict]:
        """
        Obter histórico de submissões
        
        Args:
            report_id: ID do relatório
        
        Returns:
            Lista de eventos de submissão
        """
        return self.submission_history.get(report_id, [])
    
    def export_report_to_json(self, report_id: str) -> str:
        """
        Exportar relatório para JSON
        
        Args:
            report_id: ID do relatório
        
        Returns:
            JSON string
        """
        report = self.reports.get(report_id)
        if not report:
            return json.dumps({'error': 'Report not found'})
        
        return json.dumps(report.to_dict(), indent=2, default=str)
    
    def get_regulatory_compliance_summary(self, entity_id: str) -> Dict:
        """
        Obter resumo de conformidade regulatória
        
        Args:
            entity_id: ID da entidade
        
        Returns:
            Dict com resumo de conformidade
        """
        reports = self.get_reports_by_entity(entity_id)
        
        summary = {
            'entity_id': entity_id,
            'total_reports': len(reports),
            'by_framework': {},
            'by_status': {},
            'compliance_score': 0.0,
            'last_submission': None
        }
        
        # Contar por framework e status
        for report in reports:
            framework = report['framework']
            status = report['status']
            
            if framework not in summary['by_framework']:
                summary['by_framework'][framework] = 0
            summary['by_framework'][framework] += 1
            
            if status not in summary['by_status']:
                summary['by_status'][status] = 0
            summary['by_status'][status] += 1
            
            # Atualizar última submissão
            if report['status'] in ['submitted', 'approved']:
                if summary['last_submission'] is None or report['generation_date'] > summary['last_submission']:
                    summary['last_submission'] = report['generation_date']
        
        # Calcular compliance score
        submitted = summary['by_status'].get('submitted', 0) + summary['by_status'].get('approved', 0)
        if summary['total_reports'] > 0:
            summary['compliance_score'] = (submitted / summary['total_reports']) * 100
        
        return summary
