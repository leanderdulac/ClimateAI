"""
Testes Unitários para Regulatory Reporting Service
Validação de relatórios regulatórios e conformidade
"""

import pytest
from datetime import datetime, timedelta
from services.regulatory_reporting_service import (
    RegulatoryReportingService,
    RegulatoryFramework,
    ReportType
)


class TestRegulatoryReportingService:
    """Testes para RegulatoryReportingService"""
    
    @pytest.fixture
    def reporting_service(self):
        """Fixture para serviço de regulatory reporting"""
        return RegulatoryReportingService()
    
    @pytest.fixture
    def sample_susep_data(self):
        """Dados de exemplo para relatório SUSEP"""
        return {
            'entity_id': '00.000.000/0001-00',
            'reporting_period_start': datetime.now() - timedelta(days=90),
            'reporting_period_end': datetime.now(),
            'dados_tecnicos': {
                'modelo_precificacao': 'ensemble_pricing_v1',
                'validacao_atuarial': 'Parecer atuarial nº 001/2026',
                'eventos_cobertos': ['seca', 'inundacao'],
                'regioes_atuacao': ['SP', 'MG', 'RJ']
            },
            'dados_financeiros': {
                'premios_emitidos': 10000000.00,
                'sinistros_ocorridos': 3500000.00,
                'despesas_administrativas': 1500000.00,
                'resultado_tecnico': 5000000.00
            },
            'provisoes_tecnicas': {
                'provisao_sinistros': 2000000.00,
                'provisao_premios_nao_ganhos': 3000000.00,
                'provisao_riscos_em_curso': 1500000.00
            }
        }
    
    @pytest.fixture
    def sample_solvency_ii_data(self):
        """Dados de exemplo para relatório Solvency II"""
        return {
            'entity_id': 'LEI123456789',
            'reporting_period_start': datetime.now() - timedelta(days=90),
            'reporting_period_end': datetime.now(),
            'scr': 5000000.00,
            'mcr': 2000000.00,
            'own_funds': 8000000.00,
            'risk_profile': {
                'market_risk': 2000000.00,
                'credit_risk': 1500000.00,
                'underwriting_risk': 1500000.00
            }
        }
    
    @pytest.fixture
    def sample_ifrs_17_data(self):
        """Dados de exemplo para relatório IFRS 17"""
        return {
            'entity_id': 'ENTITY001',
            'reporting_period_start': datetime.now() - timedelta(days=90),
            'reporting_period_end': datetime.now(),
            'csm': 3000000.00,
            'liability_for_incurred_claims': 2000000.00,
            'liability_for_remaining_coverage': 5000000.00,
            'insurance_revenue': 10000000.00
        }
    
    def test_service_initialization(self, reporting_service):
        """Teste: Inicialização do serviço"""
        assert reporting_service.reports is not None
        assert reporting_service.submission_history is not None
        assert len(reporting_service.validation_rules) > 0
    
    def test_create_susep_report(self, reporting_service, sample_susep_data):
        """Teste: Criar relatório SUSEP"""
        report = reporting_service.create_susep_report(
            entity_id=sample_susep_data['entity_id'],
            reporting_period_start=sample_susep_data['reporting_period_start'],
            reporting_period_end=sample_susep_data['reporting_period_end'],
            dados_tecnicos=sample_susep_data['dados_tecnicos'],
            dados_financeiros=sample_susep_data['dados_financeiros'],
            provisoes_tecnicas=sample_susep_data['provisoes_tecnicas']
        )
        
        # Verificar estrutura do relatório
        assert report.report_id.startswith('SUSEP-')
        assert report.framework == 'susep'
        assert report.circular == '562/2015'
        assert report.categoria == 'seguros_parametricos'
        assert report.dados_tecnicos == sample_susep_data['dados_tecnicos']
        assert report.dados_financeiros == sample_susep_data['dados_financeiros']
        assert report.provisoes_tecnicas == sample_susep_data['provisoes_tecnicas']
    
    def test_create_solvency_ii_report(self, reporting_service, sample_solvency_ii_data):
        """Teste: Criar relatório Solvency II"""
        report = reporting_service.create_solvency_ii_report(
            entity_id=sample_solvency_ii_data['entity_id'],
            reporting_period_start=sample_solvency_ii_data['reporting_period_start'],
            reporting_period_end=sample_solvency_ii_data['reporting_period_end'],
            scr=sample_solvency_ii_data['scr'],
            mcr=sample_solvency_ii_data['mcr'],
            own_funds=sample_solvency_ii_data['own_funds'],
            risk_profile=sample_solvency_ii_data['risk_profile']
        )
        
        # Verificar estrutura do relatório
        assert report.report_id.startswith('SOLVENCY2-')
        assert report.framework == 'solvency_ii'
        assert report.template == 'QRTs'
        assert report.scr == sample_solvency_ii_data['scr']
        assert report.mcr == sample_solvency_ii_data['mcr']
        assert report.own_funds == sample_solvency_ii_data['own_funds']
    
    def test_create_ifrs_17_report(self, reporting_service, sample_ifrs_17_data):
        """Teste: Criar relatório IFRS 17"""
        report = reporting_service.create_ifrs_17_report(
            entity_id=sample_ifrs_17_data['entity_id'],
            reporting_period_start=sample_ifrs_17_data['reporting_period_start'],
            reporting_period_end=sample_ifrs_17_data['reporting_period_end'],
            csm=sample_ifrs_17_data['csm'],
            liability_for_incurred_claims=sample_ifrs_17_data['liability_for_incurred_claims'],
            liability_for_remaining_coverage=sample_ifrs_17_data['liability_for_remaining_coverage'],
            insurance_revenue=sample_ifrs_17_data['insurance_revenue']
        )
        
        # Verificar estrutura do relatório
        assert report.report_id.startswith('IFRS17-')
        assert report.framework == 'ifrs_17'
        assert report.measurement_model == 'BBA'
        assert report.csm == sample_ifrs_17_data['csm']
        assert report.liability_for_incurred_claims == sample_ifrs_17_data['liability_for_incurred_claims']
    
    def test_validate_report_required_fields(self, reporting_service, sample_susep_data):
        """Teste: Validar campos obrigatórios"""
        report = reporting_service.create_susep_report(**sample_susep_data)
        
        # Relatório com todos os campos deve estar validado
        assert report.status in ['validated', 'draft']
        assert len(report.validation_errors) == 0
    
    def test_submit_report(self, reporting_service, sample_susep_data):
        """Teste: Submeter relatório"""
        # Criar relatório
        report = reporting_service.create_susep_report(**sample_susep_data)
        
        # Submeter relatório
        success, message = reporting_service.submit_report(
            report_id=report.report_id,
            submitted_by='compliance_officer'
        )
        
        assert success is True
        assert report.status == 'submitted'
        assert report.approval_info is not None
        assert report.approval_info['submitted_by'] == 'compliance_officer'
    
    def test_approve_report(self, reporting_service, sample_susep_data):
        """Teste: Aprovar relatório"""
        # Criar relatório
        report = reporting_service.create_susep_report(**sample_susep_data)
        
        # Aprovar relatório
        success, message = reporting_service.approve_report(
            report_id=report.report_id,
            approved_by='chief_actuary'
        )
        
        assert success is True
        assert report.status == 'approved'
        assert report.approval_info is not None
        assert report.approval_info['approved_by'] == 'chief_actuary'
    
    def test_get_report(self, reporting_service, sample_susep_data):
        """Teste: Obter relatório"""
        # Criar relatório
        report = reporting_service.create_susep_report(**sample_susep_data)
        
        # Obter relatório
        report_data = reporting_service.get_report(report.report_id)
        
        assert report_data is not None
        assert report_data['report_id'] == report.report_id
        assert report_data['entity_id'] == sample_susep_data['entity_id']
    
    def test_get_reports_by_entity(self, reporting_service, sample_susep_data):
        """Teste: Obter relatórios por entidade"""
        # Criar múltiplos relatórios para entidades diferentes
        for i in range(3):
            data = sample_susep_data.copy()
            data['entity_id'] = f'{sample_susep_data["entity_id"]}_{i}'  # Entity IDs únicos
            data['dados_financeiros'] = sample_susep_data['dados_financeiros'].copy()
            data['dados_financeiros']['premios_emitidos'] = 10000000.00 * (i + 1)
            reporting_service.create_susep_report(**data)
        
        # Obter relatórios da primeira entidade
        reports = reporting_service.get_reports_by_entity(f'{sample_susep_data["entity_id"]}_0')
        
        # Deve ter pelo menos 1 relatório
        assert len(reports) >= 1
        assert all(r['entity_id'] == f'{sample_susep_data["entity_id"]}_0' for r in reports)
    
    def test_get_submission_history(self, reporting_service, sample_susep_data):
        """Teste: Obter histórico de submissões"""
        # Criar relatório
        report = reporting_service.create_susep_report(**sample_susep_data)
        
        # Submeter relatório
        reporting_service.submit_report(report.report_id, 'user_1')
        
        # Aprovar relatório
        reporting_service.approve_report(report.report_id, 'user_2')
        
        # Obter histórico
        history = reporting_service.get_submission_history(report.report_id)
        
        assert len(history) == 2
        assert history[0]['action'] == 'submitted'
        assert history[1]['action'] == 'approved'
    
    def test_export_report_to_json(self, reporting_service, sample_susep_data):
        """Teste: Exportar relatório para JSON"""
        # Criar relatório
        report = reporting_service.create_susep_report(**sample_susep_data)
        
        # Exportar para JSON
        json_data = reporting_service.export_report_to_json(report.report_id)
        
        assert json_data is not None
        assert report.report_id in json_data
        assert 'susep' in json_data
    
    def test_get_regulatory_compliance_summary(self, reporting_service, sample_susep_data):
        """Teste: Obter resumo de conformidade regulatória"""
        # Criar relatório
        report = reporting_service.create_susep_report(**sample_susep_data)
        
        # Submeter relatório
        reporting_service.submit_report(report.report_id, 'compliance_officer')
        
        # Obter resumo
        summary = reporting_service.get_regulatory_compliance_summary(sample_susep_data['entity_id'])
        
        assert summary['entity_id'] == sample_susep_data['entity_id']
        assert summary['total_reports'] == 1
        assert 'susep' in summary['by_framework']
        assert summary['by_framework']['susep'] == 1
        assert summary['compliance_score'] == 100.0
    
    def test_solvency_ii_scr_gte_mcr_validation(self, reporting_service, sample_solvency_ii_data):
        """Teste: Validação SCR >= MCR no Solvency II"""
        # SCR >= MCR (válido)
        report = reporting_service.create_solvency_ii_report(**sample_solvency_ii_data)
        assert len(report.validation_errors) == 0
        
        # SCR < MCR (inválido)
        sample_solvency_ii_data['scr'] = 1000000.00  # Menor que MCR
        report_invalid = reporting_service.create_solvency_ii_report(**sample_solvency_ii_data)
        assert len(report_invalid.validation_errors) > 0
        assert any('SCR' in error and 'MCR' in error for error in report_invalid.validation_errors)
    
    def test_report_status_workflow(self, reporting_service, sample_susep_data):
        """Teste: Workflow de status do relatório"""
        # Criar relatório (status: validated ou draft)
        report = reporting_service.create_susep_report(**sample_susep_data)
        initial_status = report.status
        assert initial_status in ['validated', 'draft']
        
        # Submeter relatório (status: submitted)
        reporting_service.submit_report(report.report_id, 'user_1')
        assert report.status == 'submitted'
        
        # Aprovar relatório (status: approved)
        reporting_service.approve_report(report.report_id, 'user_2')
        assert report.status == 'approved'


class TestRegulatoryFrameworkEnum:
    """Testes para RegulatoryFramework enum"""
    
    def test_framework_values(self):
        """Teste: Valores de RegulatoryFramework"""
        assert RegulatoryFramework.SUSEP.value == 'susep'
        assert RegulatoryFramework.SOLVENCY_II.value == 'solvency_ii'
        assert RegulatoryFramework.IFRS_17.value == 'ifrs_17'
        assert RegulatoryFramework.BASEL_III.value == 'basel_iii'


class TestReportTypeEnum:
    """Testes para ReportType enum"""
    
    def test_report_type_values(self):
        """Teste: Valores de ReportType"""
        assert ReportType.QUARTERLY.value == 'quarterly'
        assert ReportType.ANNUAL.value == 'annual'
        assert ReportType.AD_HOC.value == 'ad_hoc'
        assert ReportType.STRESS_TEST.value == 'stress_test'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
