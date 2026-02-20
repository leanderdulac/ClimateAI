#!/usr/bin/env python3
"""
Sistema de Backup Automático para ClimateAI

Suporta:
- PostgreSQL backups
- Backup verification e restore
- Retenção automática de backups
- Upload para S3/Google Cloud Storage
- Notifications de sucesso/falha
"""

import gzip
import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# ============================================================================
# Configuração
# ============================================================================


class BackupTarget(Enum):
    """Destinos de backup suportados"""

    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"  # Google Cloud Storage
    AZURE = "azure"


class BackupConfig:
    """Configuração centralizada de backups"""

    # Diretórios
    BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "/var/backups/fimce"))
    LOG_DIR = BACKUP_DIR / "logs"
    RESTORE_DIR = BACKUP_DIR / "restore"

    # Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql://user:pass@localhost:5432/climateai"
    )

    # Retenção
    RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
    RETENTION_COUNT = int(os.getenv("BACKUP_RETENTION_COUNT", "10"))

    # Compressão
    COMPRESS = os.getenv("BACKUP_COMPRESS", "true").lower() == "true"
    COMPRESSION_LEVEL = int(os.getenv("BACKUP_COMPRESSION_LEVEL", "6"))

    # Verificação
    VERIFY_BACKUP = os.getenv("BACKUP_VERIFY", "true").lower() == "true"

    # S3
    S3_BUCKET = os.getenv("BACKUP_S3_BUCKET", "")
    S3_PREFIX = os.getenv("BACKUP_S3_PREFIX", "backups/climateai")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

    # GCS
    GCS_BUCKET = os.getenv("BACKUP_GCS_BUCKET", "")
    GCS_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")

    # Azure
    AZURE_CONTAINER = os.getenv("BACKUP_AZURE_CONTAINER", "")
    AZURE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT", "")

    # Notificações
    SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL", "")
    EMAIL_TO = os.getenv("BACKUP_EMAIL_TO", "")

    @classmethod
    def validate(cls):
        """Validar configuração"""
        cls.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        cls.RESTORE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Logging
# ============================================================================


def setup_logging(backup_id: str) -> logging.Logger:
    """Configurar logging para este backup"""
    BackupConfig.validate()

    log_file = BackupConfig.LOG_DIR / f"{backup_id}.log"

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


# ============================================================================
# Backup Operations
# ============================================================================


class DatabaseBackup:
    """Gerenciador de backups de PostgreSQL"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.backup_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def parse_connection_string(self) -> Dict[str, str]:
        """Extrair parâmetros da connection string PostgreSQL"""
        url = BackupConfig.DATABASE_URL

        # Simples parsing de postgresql://user:pass@host:5432/database
        if url.startswith("postgresql://") or url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql://", "").replace("postgresql+asyncpg://", "")

            # user:pass@host:port/database
            auth_part, db_part = url.split("@")
            user, password = auth_part.split(":")

            host_port, database = db_part.split("/")
            
            if ":" in host_port:
                host, port = host_port.split(":")
            else:
                host = host_port
                port = "5432"

            return {
                "user": user,
                "password": password,
                "host": host,
                "port": port,
                "database": database,
            }

        raise ValueError(f"Invalid PostgreSQL URL: {url}")

    def create_backup(self) -> Path:
        """Criar backup do banco de dados"""
        self.logger.info(f"Iniciando backup {self.backup_id}")

        try:
            conn_params = self.parse_connection_string()

            # Caminho do arquivo de backup
            backup_file = BackupConfig.BACKUP_DIR / f"backup_{self.backup_id}.sql"

            # Comando pg_dump
            env = os.environ.copy()
            env["PGPASSWORD"] = conn_params["password"]

            cmd = [
                "pg_dump",
                "-U",
                conn_params["user"],
                "-h",
                conn_params["host"],
                "-p",
                conn_params["port"],
                "-d",
                conn_params["database"],
                "--verbose",
                "--no-privileges",
                "--format=plain",
            ]

            self.logger.info(f"Executando: {' '.join(cmd)}")

            with open(backup_file, "w") as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    timeout=3600,  # 1 hora timeout
                )

            if result.returncode != 0:
                self.logger.error(f"pg_dump falhou: {result.stderr.decode()}")
                return None

            backup_size = backup_file.stat().st_size
            self.logger.info(
                f"Backup criado: {backup_file} ({backup_size / 1024 / 1024:.2f} MB)"
            )

            # Comprimir se configurado
            if BackupConfig.COMPRESS:
                backup_file = self.compress_backup(backup_file)

            return backup_file

        except Exception as e:
            self.logger.error(f"Erro ao criar backup: {str(e)}")
            return None

    def compress_backup(self, backup_file: Path) -> Path:
        """Comprimir arquivo de backup"""
        self.logger.info(f"Comprimindo {backup_file}")

        compressed_file = backup_file.parent / f"{backup_file.name}.gz"

        try:
            with open(backup_file, "rb") as f_in:
                with gzip.open(
                    compressed_file, "wb", compresslevel=BackupConfig.COMPRESSION_LEVEL
                ) as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Remover arquivo original
            backup_file.unlink()

            original_size = backup_file.stat().st_size if backup_file.exists() else 0
            compressed_size = compressed_file.stat().st_size

            compression_ratio = (1 - compressed_size / (original_size or 1)) * 100
            self.logger.info(
                f"Compressão: {compressed_size / 1024 / 1024:.2f} MB (ratio: {compression_ratio:.1f}%)"
            )

            return compressed_file

        except Exception as e:
            self.logger.error(f"Erro ao comprimir: {str(e)}")
            return backup_file

    def calculate_checksum(self, backup_file: Path) -> str:
        """Calcular checksum SHA256 do backup"""
        sha256 = hashlib.sha256()

        with open(backup_file, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)

        return sha256.hexdigest()

    def verify_backup(self, backup_file: Path) -> bool:
        """Verificar integridade do backup"""
        if not BackupConfig.VERIFY_BACKUP:
            return True

        self.logger.info(f"Verificando integridade de {backup_file.name}")

        try:
            # Se for gz, tentar descomprimir e verificar
            if backup_file.suffix == ".gz":
                with gzip.open(backup_file, "rb") as f:
                    data = f.read()
                self.logger.info(
                    f"Arquivo gzip válido ({len(data) / 1024 / 1024:.2f} MB)"
                )
                return True

            # Se for SQL, verificar com pg_restore se houver dump formato
            self.logger.info("Checksum: " + self.calculate_checksum(backup_file))
            return True

        except Exception as e:
            self.logger.error(f"Falha na verificação: {str(e)}")
            return False

    def restore_backup(self, backup_file: Path, target_database: str) -> bool:
        """Restaurar backup em um banco de dados"""
        self.logger.info(f"Restaurando {backup_file.name} em {target_database}")

        try:
            conn_params = self.parse_connection_string()

            # Se for comprimido, descomprimir primeiro
            if backup_file.suffix == ".gz":
                temp_file = backup_file.parent / f"{backup_file.stem}.sql"
                with gzip.open(backup_file, "rb") as f_in:
                    with open(temp_file, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                sql_file = temp_file
            else:
                sql_file = backup_file

            env = os.environ.copy()
            env["PGPASSWORD"] = conn_params["password"]

            cmd = [
                "psql",
                "-U",
                conn_params["user"],
                "-h",
                conn_params["host"],
                "-p",
                conn_params["port"],
                "-d",
                target_database,
                "-f",
                str(sql_file),
            ]

            self.logger.info(f"Executando: {' '.join(cmd[:5])}...")

            result = subprocess.run(cmd, stderr=subprocess.PIPE, env=env, timeout=3600)

            # Limpar arquivo temporário
            if sql_file != backup_file and sql_file.exists():
                sql_file.unlink()

            if result.returncode != 0:
                self.logger.error(f"psql falhou: {result.stderr.decode()}")
                return False

            self.logger.info(f"Restore concluído com sucesso")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao restaurar: {str(e)}")
            return False


# ============================================================================
# Backup Storage
# ============================================================================


class BackupStorage:
    """Gerenciar armazenamento de backups (local, S3, GCS, Azure)"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def upload_to_s3(self, backup_file: Path) -> bool:
        """Upload para S3"""
        if not BackupConfig.S3_BUCKET:
            self.logger.warning("S3_BUCKET não configurado, pulando upload")
            return True

        try:
            import boto3

            s3 = boto3.client("s3", region_name=BackupConfig.AWS_REGION)

            key = f"{BackupConfig.S3_PREFIX}/{backup_file.name}"

            self.logger.info(
                f"Fazendo upload para S3: s3://{BackupConfig.S3_BUCKET}/{key}"
            )

            s3.upload_file(
                str(backup_file),
                BackupConfig.S3_BUCKET,
                key,
                ExtraArgs={
                    "Metadata": {
                        "created": datetime.now().isoformat(),
                        "original_size": str(backup_file.stat().st_size),
                    }
                },
            )

            self.logger.info(f"Upload S3 concluído")
            return True

        except ImportError:
            self.logger.error("boto3 não está instalado")
            return False
        except Exception as e:
            self.logger.error(f"Erro ao fazer upload para S3: {str(e)}")
            return False

    def upload_to_gcs(self, backup_file: Path) -> bool:
        """Upload para Google Cloud Storage"""
        if not BackupConfig.GCS_BUCKET:
            self.logger.warning("GCS_BUCKET não configurado, pulando upload")
            return True

        try:
            from google.cloud import storage

            client = storage.Client(project=BackupConfig.GCS_PROJECT_ID)
            bucket = client.bucket(BackupConfig.GCS_BUCKET)
            blob = bucket.blob(backup_file.name)

            self.logger.info(
                f"Fazendo upload para GCS: gs://{BackupConfig.GCS_BUCKET}/{backup_file.name}"
            )

            blob.upload_from_filename(str(backup_file))

            self.logger.info(f"Upload GCS concluído")
            return True

        except ImportError:
            self.logger.error("google-cloud-storage não está instalado")
            return False
        except Exception as e:
            self.logger.error(f"Erro ao fazer upload para GCS: {str(e)}")
            return False

    def cleanup_old_backups(self) -> None:
        """Limpar backups antigos baseado em retenção"""
        self.logger.info("Limpando backups antigos")

        try:
            # Listar backups locais
            backups = sorted(
                BackupConfig.BACKUP_DIR.glob("backup_*.sql*"),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )

            cutoff_date = datetime.now() - timedelta(days=BackupConfig.RETENTION_DAYS)

            for backup_file in backups:
                # Remover se for muito antigo OU se exceder o limite de contagem
                mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)

                if mtime < cutoff_date or len(backups) > BackupConfig.RETENTION_COUNT:
                    self.logger.info(f"Removendo backup antigo: {backup_file.name}")
                    backup_file.unlink()
                    backups.remove(backup_file)

        except Exception as e:
            self.logger.error(f"Erro ao limpar backups antigos: {str(e)}")


# ============================================================================
# Notifications
# ============================================================================


class BackupNotification:
    """Enviar notificações de backup"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def send_slack(
        self, status: str, message: str, backup_file: Optional[Path] = None
    ) -> bool:
        """Enviar notificação Slack"""
        if not BackupConfig.SLACK_WEBHOOK:
            return False

        try:
            import requests

            color = "good" if status == "success" else "danger"
            size_mb = backup_file.stat().st_size / 1024 / 1024 if backup_file else 0

            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"ClimateAI Backup {status.upper()}",
                        "text": message,
                        "fields": [
                            {
                                "title": "Timestamp",
                                "value": datetime.now().isoformat(),
                                "short": True,
                            }
                        ]
                        + (
                            [
                                {
                                    "title": "Arquivo",
                                    "value": backup_file.name,
                                    "short": True,
                                },
                                {
                                    "title": "Tamanho",
                                    "value": f"{size_mb:.2f} MB",
                                    "short": True,
                                },
                            ]
                            if backup_file
                            else []
                        ),
                    }
                ]
            }

            requests.post(BackupConfig.SLACK_WEBHOOK, json=payload, timeout=10)
            return True

        except Exception as e:
            self.logger.error(f"Erro ao enviar Slack: {str(e)}")
            return False


# ============================================================================
# Main Backup Orchestrator
# ============================================================================


class BackupOrchestrator:
    """Orquestrador principal de backups"""

    def __init__(self):
        self.backup_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger = setup_logging(self.backup_id)
        self.db_backup = DatabaseBackup(self.logger)
        self.storage = BackupStorage(self.logger)
        self.notification = BackupNotification(self.logger)

    def run_backup(self) -> bool:
        """Executar backup completo"""
        self.logger.info("=" * 80)
        self.logger.info("🔄 Iniciando Backup Completo")
        self.logger.info("=" * 80)

        try:
            # 1. Criar backup
            backup_file = self.db_backup.create_backup()
            if not backup_file:
                self.notification.send_slack(
                    "failure", "Falha ao criar backup do banco de dados"
                )
                return False

            # 2. Verificar integridade
            if not self.db_backup.verify_backup(backup_file):
                self.notification.send_slack(
                    "failure", "Falha na verificação de integridade do backup"
                )
                return False

            # 3. Upload para cloud storage
            self.storage.upload_to_s3(backup_file)
            self.storage.upload_to_gcs(backup_file)

            # 4. Limpar backups antigos
            self.storage.cleanup_old_backups()

            # 5. Notificar sucesso
            self.logger.info("✅ Backup concluído com sucesso")
            self.notification.send_slack(
                "success", "Backup completado com sucesso", backup_file
            )

            return True

        except Exception as e:
            self.logger.error(f"❌ Erro durante backup: {str(e)}")
            self.notification.send_slack("failure", f"Erro durante backup: {str(e)}")
            return False

    def restore_from_backup(self, backup_file: Path, target_database: str) -> bool:
        """Restaurar a partir de um backup"""
        self.logger.info("=" * 80)
        self.logger.info("🔄 Iniciando Restore")
        self.logger.info("=" * 80)

        try:
            return self.db_backup.restore_backup(backup_file, target_database)
        except Exception as e:
            self.logger.error(f"Erro durante restore: {str(e)}")
            return False


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sistema de Backup para ClimateAI")
    subparsers = parser.add_subparsers(dest="command", help="Comando")

    # Comando: backup
    backup_parser = subparsers.add_parser("backup", help="Criar novo backup")

    # Comando: restore
    restore_parser = subparsers.add_parser("restore", help="Restaurar de um backup")
    restore_parser.add_argument("backup_file", help="Caminho do arquivo de backup")
    restore_parser.add_argument(
        "--database",
        default="climateai_restored",
        help="Nome do banco de dados destino",
    )

    # Comando: list
    list_parser = subparsers.add_parser("list", help="Listar backups disponíveis")

    args = parser.parse_args()

    orchestrator = BackupOrchestrator()

    if args.command == "backup":
        success = orchestrator.run_backup()
        sys.exit(0 if success else 1)

    elif args.command == "restore":
        backup_path = Path(args.backup_file)
        if not backup_path.exists():
            print(f"Arquivo não encontrado: {backup_path}")
            sys.exit(1)

        success = orchestrator.restore_from_backup(backup_path, args.database)
        sys.exit(0 if success else 1)

    elif args.command == "list":
        BackupConfig.validate()
        backups = sorted(
            BackupConfig.BACKUP_DIR.glob("backup_*.sql*"),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        print("\n📋 Backups Disponíveis:\n")
        for backup_file in backups:
            size_mb = backup_file.stat().st_size / 1024 / 1024
            mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            print(f"  {backup_file.name:50} {size_mb:>10.2f} MB  {mtime}")

        print(f"\n  Total: {len(backups)} backups")

    else:
        parser.print_help()
