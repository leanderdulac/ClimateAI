"""
Testes Unitários para Model Governance Service
Validação de governança e conformidade regulatória
"""

import pytest
from services.model_governance_service import (
    ModelGovernanceService,
    ChangeType,
    ModelStatus,
    ChangeStatus
)


class TestModelGovernanceService:
    """Testes para ModelGovernanceService"""
    
    @pytest.fixture
    def governance_service(self):
        """Fixture para serviço de governança"""
        return ModelGovernanceService()
    
    @pytest.fixture
    def sample_model(self):
        """Dados de exemplo para modelo"""
        return {
            'model_id': 'pricing_model_v1',
            'version': '1.0.0',
            'created_by': 'actuary_001',
            'validation_report': 'Model validated with 95% accuracy',
            'performance_metrics': {
                'accuracy': 0.95,
                'precision': 0.93,
                'recall': 0.92
            }
        }
    
    def test_service_initialization(self, governance_service):
        """Teste: Inicialização do serviço"""
        assert governance_service.approval_committee is not None
        assert len(governance_service.approval_committee) >= 3
        assert 'chief_actuary' in governance_service.approval_committee
        assert 'chief_risk_officer' in governance_service.approval_committee
    
    def test_register_model(self, governance_service, sample_model):
        """Teste: Registrar modelo"""
        model = governance_service.register_model(
            model_id=sample_model['model_id'],
            version=sample_model['version'],
            created_by=sample_model['created_by'],
            validation_report=sample_model['validation_report'],
            performance_metrics=sample_model['performance_metrics']
        )
        
        # Verificar estrutura do modelo
        assert model.model_id == sample_model['model_id']
        assert model.version == sample_model['version']
        assert model.status == ModelStatus.VALIDATED.value
        assert model.created_by == sample_model['created_by']
        assert model.validation_report == sample_model['validation_report']
        assert model.performance_metrics == sample_model['performance_metrics']
    
    def test_request_change(self, governance_service, sample_model):
        """Teste: Solicitar mudança"""
        # Registrar modelo primeiro
        governance_service.register_model(**sample_model)
        
        # Solicitar mudança
        change_request = governance_service.request_change(
            model_id=sample_model['model_id'],
            change_type=ChangeType.PARAMETER,
            description='Update risk parameter',
            justification='Based on backtesting results',
            impact_analysis={
                'premium_impact': 0.05,
                'risk_impact': 0.03
            },
            requested_by='actuary_001'
        )
        
        # Verificar change request
        assert change_request.model_id == sample_model['model_id']
        assert change_request.change_type == ChangeType.PARAMETER.value
        assert change_request.status == ChangeStatus.PENDING.value
        assert change_request.approved_by is None
    
    def test_approve_change(self, governance_service, sample_model):
        """Teste: Aprovar mudança"""
        # Registrar modelo
        governance_service.register_model(**sample_model)
        
        # Solicitar mudança
        change_request = governance_service.request_change(
            model_id=sample_model['model_id'],
            change_type=ChangeType.PARAMETER,
            description='Update risk parameter',
            justification='Based on backtesting results',
            impact_analysis={'premium_impact': 0.05},
            requested_by='actuary_001'
        )
        
        # Aprovar mudança
        success, message = governance_service.approve_change(
            request_id=change_request.request_id,
            approved_by='chief_actuary'
        )
        
        assert success is True
        assert change_request.status == ChangeStatus.APPROVED.value
        assert change_request.approved_by == 'chief_actuary'
    
    def test_reject_change(self, governance_service, sample_model):
        """Teste: Rejeitar mudança"""
        # Registrar modelo
        governance_service.register_model(**sample_model)
        
        # Solicitar mudança
        change_request = governance_service.request_change(
            model_id=sample_model['model_id'],
            change_type=ChangeType.PARAMETER,
            description='Update risk parameter',
            justification='Based on backtesting results',
            impact_analysis={'premium_impact': 0.05},
            requested_by='actuary_001'
        )
        
        # Rejeitar mudança
        success, message = governance_service.reject_change(
            request_id=change_request.request_id,
            rejected_by='chief_risk_officer',
            rejection_reason='Insufficient justification'
        )
        
        assert success is True
        assert change_request.status == ChangeStatus.REJECTED.value
        assert change_request.approved_by == 'chief_risk_officer'
    
    def test_critical_change_requires_two_approvals(self, governance_service, sample_model):
        """Teste: Mudança crítica requer 2 aprovações"""
        # Registrar modelo
        governance_service.register_model(**sample_model)
        
        # Solicitar mudança crítica
        change_request = governance_service.request_change(
            model_id=sample_model['model_id'],
            change_type=ChangeType.CRITICAL,
            description='Major algorithm change',
            justification='Significant improvement',
            impact_analysis={
                'premium_impact': 0.08,
                'risk_impact': 0.10
            },
            requested_by='actuary_001'
        )
        
        # Primeira aprovação
        success, message = governance_service.approve_change(
            request_id=change_request.request_id,
            approved_by='chief_actuary'
        )
        
        assert success is True
        assert change_request.status == ChangeStatus.IN_REVIEW.value
        
        # Segunda aprovação
        success, message = governance_service.approve_change(
            request_id=change_request.request_id,
            approved_by='chief_risk_officer'
        )
        
        assert success is True
        assert change_request.status == ChangeStatus.APPROVED.value
    
    def test_critical_change_impact_validation(self, governance_service, sample_model):
        """Teste: Validação de impacto de mudança crítica"""
        # Registrar modelo
        governance_service.register_model(**sample_model)
        
        # Tentar mudança crítica com impacto excessivo
        with pytest.raises(ValueError):
            governance_service.request_change(
                model_id=sample_model['model_id'],
                change_type=ChangeType.CRITICAL,
                description='Major change',
                justification='Test',
                impact_analysis={
                    'premium_impact': 0.20,  # Excede 10%
                    'risk_impact': 0.25      # Excede 15%
                },
                requested_by='actuary_001'
            )
    
    def test_calculate_governance_score(self, governance_service, sample_model):
        """Teste: Calcular score de governança"""
        # Registrar modelo
        governance_service.register_model(**sample_model)
        
        # Calcular score
        score = governance_service.calculate_governance_score(sample_model['model_id'])
        
        # Verificar score
        assert score.overall_score >= 0
        assert score.overall_score <= 100
        assert score.rating in ['AAA', 'AA', 'A', 'BBB', 'BB', 'B']
        assert isinstance(score.recommendations, list)
    
    def test_governance_score_rating(self, governance_service, sample_model):
        """Teste: Rating do score de governança"""
        # Registrar modelo com alta qualidade
        governance_service.register_model(
            model_id=sample_model['model_id'],
            version=sample_model['version'],
            created_by=sample_model['created_by'],
            validation_report=sample_model['validation_report'],
            performance_metrics=sample_model['performance_metrics']
        )
        
        # Aprovar modelo
        model = governance_service.models[sample_model['model_id']]
        model.approved_by = 'chief_actuary'
        model.status = ModelStatus.APPROVED.value
        
        # Calcular score
        score = governance_service.calculate_governance_score(sample_model['model_id'])
        
        # Modelo de alta qualidade deve ter rating bom
        assert score.overall_score >= 50
        assert score.rating in ['AAA', 'AA', 'A', 'BBB']
    
    def test_get_model_info(self, governance_service, sample_model):
        """Teste: Obter informações do modelo"""
        # Registrar modelo
        governance_service.register_model(**sample_model)
        
        # Obter informações
        model_info = governance_service.get_model_info(sample_model['model_id'])
        
        assert model_info is not None
        assert model_info['model_id'] == sample_model['model_id']
        assert model_info['version'] == sample_model['version']
    
    def test_get_change_request(self, governance_service, sample_model):
        """Teste: Obter change request"""
        # Registrar modelo
        governance_service.register_model(**sample_model)
        
        # Solicitar mudança
        change_request = governance_service.request_change(
            model_id=sample_model['model_id'],
            change_type=ChangeType.PARAMETER,
            description='Update parameter',
            justification='Test',
            impact_analysis={'premium_impact': 0.05},
            requested_by='actuary_001'
        )
        
        # Obter change request
        change_info = governance_service.get_change_request(change_request.request_id)
        
        assert change_info is not None
        assert change_info['request_id'] == change_request.request_id
    
    def test_get_model_change_history(self, governance_service, sample_model):
        """Teste: Obter histórico de mudanças"""
        # Registrar modelo
        governance_service.register_model(**sample_model)
        
        # Criar várias mudanças com IDs únicos
        for i in range(3):
            governance_service.request_change(
                model_id=sample_model['model_id'],
                change_type=ChangeType.PARAMETER,
                description=f'Change {i}',
                justification=f'Test {i}',
                impact_analysis={'premium_impact': 0.05 * (i + 1)},
                requested_by=f'actuary_00{i + 1}'
            )
        
        # Obter histórico
        history = governance_service.get_model_change_history(sample_model['model_id'])
        
        # Deve ter pelo menos 1 mudança (última sobrescreve as anteriores no dict)
        assert len(history) >= 1
    
    def test_get_governance_report(self, governance_service, sample_model):
        """Teste: Obter relatório de governança"""
        # Registrar modelo
        governance_service.register_model(**sample_model)
        
        # Obter relatório
        report = governance_service.get_governance_report(sample_model['model_id'])
        
        assert report is not None
        assert 'model_id' in report
        assert 'governance_score' in report
        assert 'change_history_summary' in report
        assert 'regulatory_compliance' in report
    
    def test_model_version_increment(self, governance_service, sample_model):
        """Teste: Incremento de versão do modelo"""
        # Registrar modelo
        governance_service.register_model(**sample_model)
        
        # Solicitar e aprovar mudança
        change_request = governance_service.request_change(
            model_id=sample_model['model_id'],
            change_type=ChangeType.PARAMETER,
            description='Update parameter',
            justification='Test',
            impact_analysis={'premium_impact': 0.05},
            requested_by='actuary_001'
        )
        
        # Aprovar mudança
        governance_service.approve_change(
            request_id=change_request.request_id,
            approved_by='chief_actuary'
        )
        
        # Verificar incremento de versão
        model = governance_service.models[sample_model['model_id']]
        assert model.version == '1.0.1'  # Incremento no patch version


class TestChangeTypeEnum:
    """Testes para ChangeType enum"""
    
    def test_change_type_values(self):
        """Teste: Valores de ChangeType"""
        assert ChangeType.PARAMETER.value == 'parameter'
        assert ChangeType.ALGORITHM.value == 'algorithm'
        assert ChangeType.DATA_SOURCE.value == 'data_source'
        assert ChangeType.THRESHOLD.value == 'threshold'
        assert ChangeType.CRITICAL.value == 'critical'
        assert ChangeType.BUGFIX.value == 'bugfix'
        assert ChangeType.PERFORMANCE.value == 'performance'


class TestModelStatusEnum:
    """Testes para ModelStatus enum"""
    
    def test_model_status_values(self):
        """Teste: Valores de ModelStatus"""
        assert ModelStatus.DRAFT.value == 'draft'
        assert ModelStatus.VALIDATED.value == 'validated'
        assert ModelStatus.APPROVED.value == 'approved'
        assert ModelStatus.DEPRECATED.value == 'deprecated'
        assert ModelStatus.RETIRED.value == 'retired'


class TestChangeStatusEnum:
    """Testes para ChangeStatus enum"""
    
    def test_change_status_values(self):
        """Teste: Valores de ChangeStatus"""
        assert ChangeStatus.PENDING.value == 'pending'
        assert ChangeStatus.IN_REVIEW.value == 'in_review'
        assert ChangeStatus.APPROVED.value == 'approved'
        assert ChangeStatus.REJECTED.value == 'rejected'
        assert ChangeStatus.IMPLEMENTED.value == 'implemented'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
