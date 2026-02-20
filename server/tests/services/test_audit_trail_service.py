"""
Testes Unitários para Audit Trail Service
Validação de integridade e conformidade regulatória
"""

import pytest
import os
import tempfile
from services.audit_trail_service import AuditTrailService, AuditEntry, AuditChainIntegrity


class TestAuditTrailService:
    """Testes para AuditTrailService"""
    
    @pytest.fixture
    def audit_service(self):
        """Fixture para serviço de audit trail com DB em memória"""
        # Usar arquivo temporário
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        service = AuditTrailService(db_path=db_path)
        yield service
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def sample_audit_data(self):
        """Dados de exemplo para testes"""
        return {
            'operation': 'pricing_calculation',
            'user_id': 'actuary_001',
            'policy_id': 'POLICY_2026_001',
            'input_data': {
                'asset_value': 1000000,
                'frequency': 0.1,
                'severity': 50000
            },
            'output_data': {
                'premium': 15000,
                'combined_ratio': 0.85,
                'profit_margin': 0.15
            },
            'model_version': '1.0.0'
        }
    
    def test_service_initialization(self, audit_service):
        """Teste: Inicialização do serviço"""
        assert audit_service.db_path is not None
        assert audit_service.private_key is not None
        assert audit_service.last_hash == "0" * 64  # Genesis hash
    
    def test_add_entry(self, audit_service, sample_audit_data):
        """Teste: Adicionar entrada de audit"""
        entry = audit_service.add_entry(
            operation=sample_audit_data['operation'],
            user_id=sample_audit_data['user_id'],
            policy_id=sample_audit_data['policy_id'],
            input_data=sample_audit_data['input_data'],
            output_data=sample_audit_data['output_data'],
            model_version=sample_audit_data['model_version']
        )
        
        # Verificar estrutura da entrada
        assert isinstance(entry, AuditEntry)
        assert entry.entry_id is not None
        assert len(entry.entry_id) == 64  # SHA-256 hex
        assert entry.operation == sample_audit_data['operation']
        assert entry.user_id == sample_audit_data['user_id']
        assert entry.policy_id == sample_audit_data['policy_id']
        assert len(entry.input_hash) == 64
        assert len(entry.output_hash) == 64
        assert entry.previous_hash == "0" * 64  # Primeira entrada
        assert len(entry.signature) == 64
    
    def test_hash_chaining(self, audit_service, sample_audit_data):
        """Teste: Hash chaining entre entradas"""
        # Adicionar primeira entrada
        entry1 = audit_service.add_entry(
            operation='operation_1',
            user_id='user_1',
            policy_id='policy_1',
            input_data={'test': 'data1'},
            output_data={'result': 'result1'},
            model_version='1.0.0'
        )
        
        # Adicionar segunda entrada
        entry2 = audit_service.add_entry(
            operation='operation_2',
            user_id='user_1',
            policy_id='policy_2',
            input_data={'test': 'data2'},
            output_data={'result': 'result2'},
            model_version='1.0.0'
        )
        
        # Verificar hash chaining
        assert entry2.previous_hash == entry1.output_hash
        
        # Adicionar terceira entrada
        entry3 = audit_service.add_entry(
            operation='operation_3',
            user_id='user_1',
            policy_id='policy_3',
            input_data={'test': 'data3'},
            output_data={'result': 'result3'},
            model_version='1.0.0'
        )
        
        # Verificar hash chaining
        assert entry3.previous_hash == entry2.output_hash
    
    def test_verify_chain_integrity_valid(self, audit_service, sample_audit_data):
        """Teste: Verificar integridade da cadeia (válida)"""
        # Adicionar várias entradas
        for i in range(5):
            audit_service.add_entry(
                operation=f'operation_{i}',
                user_id='user_1',
                policy_id=f'policy_{i}',
                input_data={'index': i},
                output_data={'result': i * 2},
                model_version='1.0.0'
            )
        
        # Verificar integridade
        integrity = audit_service.verify_chain_integrity()
        
        assert isinstance(integrity, AuditChainIntegrity)
        assert integrity.valid is True
        assert integrity.total_entries == 5
        assert integrity.broken_at is None
    
    def test_get_policy_audit_trail(self, audit_service, sample_audit_data):
        """Teste: Recuperar audit trail de policy"""
        # Adicionar entradas para mesma policy
        policy_id = 'POLICY_TEST_001'
        for i in range(3):
            audit_service.add_entry(
                operation=f'operation_{i}',
                user_id='user_1',
                policy_id=policy_id,
                input_data={'index': i},
                output_data={'result': i * 2},
                model_version='1.0.0'
            )
        
        # Adicionar entrada para policy diferente
        audit_service.add_entry(
            operation='other_operation',
            user_id='user_1',
            policy_id='POLICY_OTHER',
            input_data={'test': 'data'},
            output_data={'result': 'result'},
            model_version='1.0.0'
        )
        
        # Recuperar audit trail da policy
        entries = audit_service.get_policy_audit_trail(policy_id)
        
        assert len(entries) == 3
        assert all(e.policy_id == policy_id for e in entries)
        assert entries[0].operation == 'operation_0'
        assert entries[1].operation == 'operation_1'
        assert entries[2].operation == 'operation_2'
    
    def test_get_user_activity(self, audit_service, sample_audit_data):
        """Teste: Recuperar atividade de usuário"""
        # Adicionar entradas para mesmo usuário
        user_id = 'user_test_001'
        for i in range(5):
            audit_service.add_entry(
                operation=f'operation_{i}',
                user_id=user_id,
                policy_id=f'policy_{i}',
                input_data={'index': i},
                output_data={'result': i * 2},
                model_version='1.0.0'
            )
        
        # Recuperar atividade
        entries = audit_service.get_user_activity(user_id, limit=10)
        
        assert len(entries) == 5
        assert all(e.user_id == user_id for e in entries)
    
    def test_export_for_regulator(self, audit_service, sample_audit_data):
        """Teste: Exportar para regulador"""
        policy_id = 'POLICY_EXPORT_TEST'
        
        # Adicionar entradas
        for i in range(3):
            audit_service.add_entry(
                operation=f'operation_{i}',
                user_id='user_1',
                policy_id=policy_id,
                input_data={'index': i},
                output_data={'result': i * 2},
                model_version='1.0.0'
            )
        
        # Exportar
        export_data = audit_service.export_for_regulator(policy_id)
        
        # Verificar estrutura
        assert 'export_version' in export_data
        assert 'export_timestamp' in export_data
        assert 'policy_id' in export_data
        assert 'chain_integrity' in export_data
        assert 'summary' in export_data
        assert 'entries' in export_data
        assert 'regulatory_compliance' in export_data
        
        # Verificar dados
        assert export_data['policy_id'] == policy_id
        assert export_data['chain_integrity']['valid'] is True
        assert export_data['summary']['total_entries'] == 3
        assert len(export_data['entries']) == 3
        assert 'SUSEP' in export_data['regulatory_compliance']
        assert 'Solvency II' in export_data['regulatory_compliance']
    
    def test_get_audit_stats(self, audit_service, sample_audit_data):
        """Teste: Obter estatísticas de audit"""
        # Adicionar entradas variadas
        operations = ['pricing', 'underwriting', 'claims', 'pricing', 'pricing']
        users = ['user_1', 'user_2', 'user_1', 'user_1', 'user_3']
        
        for i in range(5):
            audit_service.add_entry(
                operation=operations[i],
                user_id=users[i],
                policy_id=f'policy_{i}',
                input_data={'index': i},
                output_data={'result': i * 2},
                model_version='1.0.0'
            )
        
        # Obter estatísticas
        stats = audit_service.get_audit_stats()
        
        assert stats['total_entries'] == 5
        assert 'pricing' in stats['operations']
        assert stats['operations']['pricing'] == 3
        assert 'user_1' in stats['top_users']
    
    def test_signature_verification(self, audit_service, sample_audit_data):
        """Teste: Verificação de signature"""
        entry = audit_service.add_entry(
            operation=sample_audit_data['operation'],
            user_id=sample_audit_data['user_id'],
            policy_id=sample_audit_data['policy_id'],
            input_data=sample_audit_data['input_data'],
            output_data=sample_audit_data['output_data'],
            model_version=sample_audit_data['model_version']
        )
        
        # Verificar signature
        is_valid = audit_service._verify_signature(entry)
        assert is_valid is True
        
        # Corromper signature e verificar
        corrupted_entry = AuditEntry(
            entry_id=entry.entry_id,
            timestamp=entry.timestamp,
            operation=entry.operation,
            user_id=entry.user_id,
            policy_id=entry.policy_id,
            input_hash=entry.input_hash,
            output_hash=entry.output_hash,
            previous_hash=entry.previous_hash,
            model_version=entry.model_version,
            signature='corrupted_signature',
            metadata=entry.metadata
        )
        
        is_valid_corrupted = audit_service._verify_signature(corrupted_entry)
        assert is_valid_corrupted is False
    
    def test_hash_calculation_consistency(self, audit_service):
        """Teste: Consistência do cálculo de hash"""
        data = {'test': 'data', 'number': 42}
        
        # Calcular hash múltiplas vezes
        hash1 = audit_service._calculate_hash(data)
        hash2 = audit_service._calculate_hash(data)
        hash3 = audit_service._calculate_hash(data)
        
        # Devem ser idênticos
        assert hash1 == hash2 == hash3
        assert len(hash1) == 64  # SHA-256 hex length
    
    def test_clear_audit_trail(self, audit_service, sample_audit_data):
        """Teste: Limpar audit trail antigo"""
        # Adicionar entradas
        for i in range(10):
            audit_service.add_entry(
                operation=f'operation_{i}',
                user_id='user_1',
                policy_id=f'policy_{i}',
                input_data={'index': i},
                output_data={'result': i * 2},
                model_version='1.0.0'
            )
        
        # Limpar (manter últimos 365 dias - todas as entradas são recentes)
        audit_service.clear_audit_trail(retention_days=365)
        
        # Verificar que entradas foram mantidas
        stats = audit_service.get_audit_stats()
        assert stats['total_entries'] == 10


class TestAuditEntryDataclass:
    """Testes para AuditEntry dataclass"""
    
    def test_entry_creation(self):
        """Teste: Criar AuditEntry"""
        entry = AuditEntry(
            entry_id='test_id',
            timestamp='2026-02-16T23:00:00',
            operation='test_operation',
            user_id='user_1',
            policy_id='policy_1',
            input_hash='input_hash',
            output_hash='output_hash',
            previous_hash='prev_hash',
            model_version='1.0.0',
            signature='signature'
        )
        
        assert entry.entry_id == 'test_id'
        assert entry.operation == 'test_operation'
        assert entry.metadata == {}  # Default empty dict
    
    def test_entry_to_dict(self):
        """Teste: Converter para dicionário"""
        entry = AuditEntry(
            entry_id='test_id',
            timestamp='2026-02-16T23:00:00',
            operation='test_operation',
            user_id='user_1',
            policy_id='policy_1',
            input_hash='input_hash',
            output_hash='output_hash',
            previous_hash='prev_hash',
            model_version='1.0.0',
            signature='signature',
            metadata={'key': 'value'}
        )
        
        entry_dict = entry.to_dict()
        
        assert isinstance(entry_dict, dict)
        assert entry_dict['entry_id'] == 'test_id'
        assert entry_dict['metadata'] == {'key': 'value'}
    
    def test_entry_from_dict(self):
        """Teste: Criar a partir de dicionário"""
        data = {
            'entry_id': 'test_id',
            'timestamp': '2026-02-16T23:00:00',
            'operation': 'test_operation',
            'user_id': 'user_1',
            'policy_id': 'policy_1',
            'input_hash': 'input_hash',
            'output_hash': 'output_hash',
            'previous_hash': 'prev_hash',
            'model_version': '1.0.0',
            'signature': 'signature',
            'metadata': {'key': 'value'}
        }
        
        entry = AuditEntry.from_dict(data)
        
        assert isinstance(entry, AuditEntry)
        assert entry.entry_id == 'test_id'
        assert entry.metadata == {'key': 'value'}


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
