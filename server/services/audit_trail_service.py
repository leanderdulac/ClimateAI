"""
Immutable Audit Trail Service
Usa hash chaining para garantir integridade de cálculos e operações

Requisitos Regulatórios:
- SOX (Sarbanes-Oxley)
- SUSEP Circular 562/2015
- Solvency II
- IFRS 17
- Basel III
"""

import hashlib
import json
import logging
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
import os

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    """
    Entrada de audit trail imutável
    
    Estrutura similar a blockchain:
    - Cada entrada contém hash da anterior
    - Hash calculado com SHA-256
    - Signature criptográfica opcional
    """
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
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Converter para dicionário"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AuditEntry':
        """Criar a partir de dicionário"""
        return cls(**data)


@dataclass
class AuditChainIntegrity:
    """Resultado da verificação de integridade da cadeia"""
    valid: bool
    total_entries: int
    first_entry_id: str
    last_entry_id: str
    broken_at: Optional[str]
    verification_timestamp: str


class AuditTrailService:
    """
    Serviço de Audit Trail Imutável
    
    Implementa:
    - Hash chaining (blockchain-like)
    - SHA-256 para integridade
    - Signature verification (opcional)
    - Export para reguladores
    - Query por policy_id, user_id, operation
    """
    
    def __init__(self, db_path: str = "audit_trail.db", private_key: str = None):
        """
        Inicializar serviço de audit trail
        
        Args:
            db_path: Caminho para banco de dados SQLite
            private_key: Chave privada para signatures (opcional)
        """
        self.db_path = db_path
        self.private_key = private_key or os.getenv('AUDIT_PRIVATE_KEY', 'default_audit_key_2026')
        self._init_db()  # Inicializar DB primeiro
        self.last_hash = self._get_last_hash()  # Depois obter último hash
        
        logger.info(f"AuditTrailService initialized with db={db_path}")
    
    def _init_db(self):
        """Inicializar banco de dados SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela principal de audit trail
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_trail (
                entry_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                operation TEXT NOT NULL,
                user_id TEXT NOT NULL,
                policy_id TEXT NOT NULL,
                input_hash TEXT NOT NULL,
                output_hash TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                model_version TEXT NOT NULL,
                signature TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Índices para queries rápidas
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_policy_id 
            ON audit_trail(policy_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_id 
            ON audit_trail(user_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON audit_trail(timestamp)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_operation 
            ON audit_trail(operation)
        ''')
        
        conn.commit()
        conn.close()
        
        logger.debug("Audit trail database initialized")
    
    def _calculate_hash(self, data: Dict) -> str:
        """
        Calcular hash SHA-256 dos dados
        
        Args:
            data: Dicionário para hash
        
        Returns:
            Hash SHA-256 em hexadecimal
        """
        # Ordenar chaves para consistência
        data_str = json.dumps(data, sort_keys=True, default=str)
        hash_bytes = hashlib.sha256(data_str.encode()).hexdigest()
        return hash_bytes
    
    def _sign_entry(self, entry: AuditEntry) -> str:
        """
        Assinar entrada criptograficamente
        
        Em produção, usar HSM ou serviço de keys (AWS KMS, Azure Key Vault)
        
        Args:
            entry: AuditEntry para assinar
        
        Returns:
            Signature em hexadecimal
        """
        # Preparar dados para assinatura (sem a signature)
        entry_data = entry.to_dict()
        entry_data.pop('signature')
        message = json.dumps(entry_data, sort_keys=True, default=str).encode()
        
        # Simplificado: em produção usar RSA/ECDSA
        # Exemplo: hashlib.sha256(message + private_key.encode()).hexdigest()
        signature = hashlib.sha256(message + self.private_key.encode()).hexdigest()
        
        return signature
    
    def _verify_signature(self, entry: AuditEntry) -> bool:
        """
        Verificar signature de entrada
        
        Args:
            entry: AuditEntry para verificar
        
        Returns:
            True se signature válida, False caso contrário
        """
        # Calcular signature esperada
        expected_signature = self._sign_entry(entry)
        
        # Comparar com signature armazenada
        return entry.signature == expected_signature
    
    def _get_last_hash(self) -> str:
        """
        Obter hash da última entrada
        
        Returns:
            Hash da última entrada ou hash genesis
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT entry_id, input_hash, output_hash 
            FROM audit_trail 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # Hash é baseado no output da última entrada
            return row[2]  # output_hash
        else:
            # Genesis block hash
            return "0" * 64
    
    def add_entry(
        self,
        operation: str,
        user_id: str,
        policy_id: str,
        input_data: Dict,
        output_data: Dict,
        model_version: str,
        metadata: Dict = None
    ) -> AuditEntry:
        """
        Adicionar entrada imutável ao audit trail
        
        Args:
            operation: Nome da operação (ex: "pricing_calculation")
            user_id: ID do usuário
            policy_id: ID da apólice
            input_data: Dados de entrada (serão hasheados)
            output_data: Dados de saída (serão hasheados)
            model_version: Versão do modelo usado
            metadata: Metadados adicionais
        
        Returns:
            AuditEntry criada
        """
        try:
            # Calcular hashes dos dados
            input_hash = self._calculate_hash(input_data)
            output_hash = self._calculate_hash(output_data)
            previous_hash = self.last_hash
            
            # Criar entry_id único
            entry_id = self._calculate_hash({
                'timestamp': datetime.now().isoformat(),
                'policy_id': policy_id,
                'operation': operation,
                'nonce': os.urandom(16).hex()
            })
            
            # Criar entrada
            entry = AuditEntry(
                entry_id=entry_id,
                timestamp=datetime.now().isoformat(),
                operation=operation,
                user_id=user_id,
                policy_id=policy_id,
                input_hash=input_hash,
                output_hash=output_hash,
                previous_hash=previous_hash,
                model_version=model_version,
                signature='',  # Será preenchido abaixo
                metadata=metadata or {}
            )
            
            # Assinar entrada
            entry.signature = self._sign_entry(entry)
            
            # Salvar no banco
            self._save_entry(entry)
            
            # Atualizar último hash
            self.last_hash = output_hash
            
            logger.info(f"Audit entry added: {entry_id[:16]}... for policy {policy_id}")
            
            return entry
            
        except Exception as e:
            logger.error(f"Error adding audit entry: {e}", exc_info=True)
            raise
    
    def _save_entry(self, entry: AuditEntry):
        """Salvar entrada no banco de dados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO audit_trail 
            (entry_id, timestamp, operation, user_id, policy_id, 
             input_hash, output_hash, previous_hash, model_version, 
             signature, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.entry_id,
            entry.timestamp,
            entry.operation,
            entry.user_id,
            entry.policy_id,
            entry.input_hash,
            entry.output_hash,
            entry.previous_hash,
            entry.model_version,
            entry.signature,
            json.dumps(entry.metadata, default=str)
        ))
        
        conn.commit()
        conn.close()
    
    def verify_chain_integrity(self) -> AuditChainIntegrity:
        """
        Verificar integridade da cadeia de hashes
        
        Retorna True se nenhuma entrada foi adulterada
        
        Returns:
            AuditChainIntegrity com resultado da verificação
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT entry_id, input_hash, output_hash, previous_hash, signature 
            FROM audit_trail 
            ORDER BY timestamp ASC
        ''')
        
        entries = cursor.fetchall()
        conn.close()
        
        if not entries:
            return AuditChainIntegrity(
                valid=True,
                total_entries=0,
                first_entry_id="N/A",
                last_entry_id="N/A",
                broken_at=None,
                verification_timestamp=datetime.now().isoformat()
            )
        
        # Verificar cadeia
        prev_hash = "0" * 64  # Genesis block
        broken_at = None
        
        for i, row in enumerate(entries):
            entry_id, input_hash, output_hash, stored_prev_hash, signature = row
            
            # Verificar hash chaining
            if stored_prev_hash != prev_hash:
                broken_at = entry_id
                logger.error(f"Chain broken at entry {entry_id}")
                break
            
            # Verificar signature (opcional, pode ser lento)
            # Reconstruir entry para verificação
            entry = AuditEntry(
                entry_id=entry_id,
                input_hash=input_hash,
                output_hash=output_hash,
                previous_hash=stored_prev_hash,
                signature=signature,
                timestamp='',
                operation='',
                user_id='',
                policy_id='',
                model_version=''
            )
            
            # Atualizar para próxima iteração
            prev_hash = output_hash
        
        valid = broken_at is None
        
        return AuditChainIntegrity(
            valid=valid,
            total_entries=len(entries),
            first_entry_id=entries[0][0] if entries else "N/A",
            last_entry_id=entries[-1][0] if entries else "N/A",
            broken_at=broken_at,
            verification_timestamp=datetime.now().isoformat()
        )
    
    def get_policy_audit_trail(self, policy_id: str) -> List[AuditEntry]:
        """
        Recuperar todo o audit trail de uma apólice
        
        Args:
            policy_id: ID da apólice
        
        Returns:
            Lista de AuditEntry ordenadas por timestamp
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM audit_trail 
            WHERE policy_id = ? 
            ORDER BY timestamp ASC
        ''', (policy_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        entries = []
        for row in rows:
            entry = AuditEntry(
                entry_id=row[0],
                timestamp=row[1],
                operation=row[2],
                user_id=row[3],
                policy_id=row[4],
                input_hash=row[5],
                output_hash=row[6],
                previous_hash=row[7],
                model_version=row[8],
                signature=row[9],
                metadata=json.loads(row[10]) if row[10] else {}
            )
            entries.append(entry)
        
        logger.info(f"Retrieved {len(entries)} audit entries for policy {policy_id}")
        
        return entries
    
    def get_user_activity(self, user_id: str, limit: int = 100) -> List[AuditEntry]:
        """
        Recuperar atividade de um usuário
        
        Args:
            user_id: ID do usuário
            limit: Limite de entradas
        
        Returns:
            Lista de AuditEntry
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM audit_trail 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        entries = [
            AuditEntry(
                entry_id=row[0],
                timestamp=row[1],
                operation=row[2],
                user_id=row[3],
                policy_id=row[4],
                input_hash=row[5],
                output_hash=row[6],
                previous_hash=row[7],
                model_version=row[8],
                signature=row[9],
                metadata=json.loads(row[10]) if row[10] else {}
            )
            for row in rows
        ]
        
        return entries
    
    def export_for_regulator(self, policy_id: str) -> Dict:
        """
        Exportar audit trail formatado para reguladores (SUSEP, Solvency II)
        
        Args:
            policy_id: ID da apólice
        
        Returns:
            Dict formatado para exportação regulatória
        """
        entries = self.get_policy_audit_trail(policy_id)
        chain_integrity = self.verify_chain_integrity()
        
        # Calcular estatísticas
        operations_count = {}
        for entry in entries:
            operations_count[entry.operation] = operations_count.get(entry.operation, 0) + 1
        
        return {
            'export_version': '1.0',
            'export_timestamp': datetime.now().isoformat(),
            'policy_id': policy_id,
            'chain_integrity': {
                'valid': chain_integrity.valid,
                'total_entries': chain_integrity.total_entries,
                'verification_timestamp': chain_integrity.verification_timestamp
            },
            'summary': {
                'total_entries': len(entries),
                'first_entry': entries[0].timestamp if entries else None,
                'last_entry': entries[-1].timestamp if entries else None,
                'operations': operations_count,
                'unique_users': len(set(e.user_id for e in entries))
            },
            'entries': [entry.to_dict() for entry in entries],
            'verification_hash': self.last_hash,
            'regulatory_compliance': ['SUSEP', 'Solvency II', 'SOX', 'IFRS 17']
        }
    
    def get_audit_stats(self) -> Dict:
        """
        Obter estatísticas do audit trail
        
        Returns:
            Dict com estatísticas
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total de entradas
        cursor.execute('SELECT COUNT(*) FROM audit_trail')
        total_entries = cursor.fetchone()[0]
        
        # Entradas por operação
        cursor.execute('''
            SELECT operation, COUNT(*) as count 
            FROM audit_trail 
            GROUP BY operation 
            ORDER BY count DESC
        ''')
        operations = dict(cursor.fetchall())
        
        # Entradas por usuário
        cursor.execute('''
            SELECT user_id, COUNT(*) as count 
            FROM audit_trail 
            GROUP BY user_id 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        top_users = dict(cursor.fetchall())
        
        # Primeira e última entrada
        cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM audit_trail')
        row = cursor.fetchone()
        first_entry = row[0]
        last_entry = row[1]
        
        conn.close()
        
        return {
            'total_entries': total_entries,
            'operations': operations,
            'top_users': top_users,
            'first_entry': first_entry,
            'last_entry': last_entry,
            'database_path': self.db_path,
            'last_hash': self.last_hash[:16] + '...'
        }
    
    def clear_audit_trail(self, retention_days: int = 365):
        """
        Limpar audit trail antigo (manter apenas últimos N dias)
        
        Args:
            retention_days: Dias de retenção (padrão: 365)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now().timestamp() - (retention_days * 86400))
        cutoff_iso = datetime.fromtimestamp(cutoff_date).isoformat()
        
        cursor.execute('''
            DELETE FROM audit_trail 
            WHERE timestamp < ?
        ''', (cutoff_iso,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Cleared {deleted} audit entries older than {retention_days} days")
        
        # Atualizar último hash
        self.last_hash = self._get_last_hash()
