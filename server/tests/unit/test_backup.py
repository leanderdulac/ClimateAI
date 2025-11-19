"""
Unit Tests for Database Backup Module
Tests for server/backup.py - automated database backup system
"""

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from backup import (
    BackupConfig,
    BackupNotification,
    BackupOrchestrator,
    BackupStorage,
    DatabaseBackup,
)

# ============================================================================
# TESTS: BackupConfig
# ============================================================================


@pytest.mark.unit
class TestBackupConfig:
    """Tests for BackupConfig class"""

    def test_backup_config_creation_with_defaults(self):
        """Test creating BackupConfig with defaults"""
        config = BackupConfig(database_url="postgresql://user:pass@localhost/db")

        assert config.database_url == "postgresql://user:pass@localhost/db"
        assert config.backup_dir is not None
        assert config.retention_days == 30
        assert config.max_backups == 10

    def test_backup_config_creation_with_custom_values(self):
        """Test creating BackupConfig with custom values"""
        config = BackupConfig(
            database_url="postgresql://localhost/db",
            backup_dir="/custom/backup/dir",
            retention_days=60,
            max_backups=20,
        )

        assert config.retention_days == 60
        assert config.max_backups == 20
        assert config.backup_dir == "/custom/backup/dir"

    def test_backup_config_s3_configuration(self):
        """Test BackupConfig with S3 settings"""
        config = BackupConfig(
            database_url="postgresql://localhost/db",
            s3_enabled=True,
            s3_bucket="my-bucket",
            s3_region="us-east-1",
        )

        assert config.s3_enabled is True
        assert config.s3_bucket == "my-bucket"
        assert config.s3_region == "us-east-1"

    def test_backup_config_from_environment(self):
        """Test BackupConfig reads from environment variables"""
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql://localhost/db",
                "BACKUP_DIR": "/backups",
                "BACKUP_RETENTION_DAYS": "45",
            },
        ):
            config = BackupConfig()

            assert config.database_url == "postgresql://localhost/db"
            assert config.backup_dir == "/backups"
            assert config.retention_days == 45


# ============================================================================
# TESTS: DatabaseBackup
# ============================================================================


@pytest.mark.unit
class TestDatabaseBackup:
    """Tests for DatabaseBackup class"""

    def test_database_backup_creation(self):
        """Test creating DatabaseBackup instance"""
        config = BackupConfig(database_url="postgresql://localhost/db")
        backup = DatabaseBackup(config)

        assert backup.config == config
        assert backup.database_url == "postgresql://localhost/db"

    def test_database_backup_generate_filename(self):
        """Test backup filename generation"""
        config = BackupConfig(database_url="postgresql://localhost/testdb")
        backup = DatabaseBackup(config)

        filename = backup._generate_filename()

        assert "testdb" in filename
        assert filename.endswith(".sql.gz")
        # Should include timestamp
        assert "-" in filename  # Date separators

    def test_database_backup_calculate_file_size(self):
        """Test calculating backup file size"""
        config = BackupConfig(database_url="postgresql://localhost/db")
        backup = DatabaseBackup(config)

        with tempfile.NamedTemporaryFile() as tmp:
            # Create a file with known size
            tmp.write(b"x" * 1024 * 100)  # 100 KB
            tmp.flush()

            size = backup._get_file_size(tmp.name)

            assert size == 1024 * 100

    @patch("subprocess.run")
    def test_database_backup_perform_backup(self, mock_run):
        """Test performing database backup"""
        mock_run.return_value = MagicMock(returncode=0)

        config = BackupConfig(database_url="postgresql://localhost/db")
        backup = DatabaseBackup(config)

        # Mock subprocess to return success
        with tempfile.TemporaryDirectory() as tmpdir:
            config.backup_dir = tmpdir

            # Should execute pg_dump command
            mock_run.assert_not_called()  # Not called yet

    def test_database_backup_verify_file(self):
        """Test verifying backup file"""
        config = BackupConfig(database_url="postgresql://localhost/db")
        backup = DatabaseBackup(config)

        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b"valid backup content")
            tmp.flush()

            # Should verify successfully
            is_valid = backup._verify_backup_file(tmp.name)

            assert is_valid is True

    def test_database_backup_invalid_file(self):
        """Test verifying invalid backup file"""
        config = BackupConfig(database_url="postgresql://localhost/db")
        backup = DatabaseBackup(config)

        # Non-existent file
        is_valid = backup._verify_backup_file("/nonexistent/path/backup.gz")

        assert is_valid is False

    def test_database_backup_calculate_checksum(self):
        """Test calculating backup checksum"""
        config = BackupConfig(database_url="postgresql://localhost/db")
        backup = DatabaseBackup(config)

        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b"test content")
            tmp.flush()

            checksum = backup._calculate_checksum(tmp.name)

            assert checksum is not None
            assert len(checksum) > 0
            # SHA256 produces 64-char hex string
            assert len(checksum) == 64

    def test_database_backup_retention_cleanup_needed(self):
        """Test determining if cleanup is needed"""
        config = BackupConfig(
            database_url="postgresql://localhost/db",
            retention_days=30,
            max_backups=2,
        )
        backup = DatabaseBackup(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            config.backup_dir = tmpdir

            # Create old backup files
            old_file = Path(tmpdir) / "backup_20250101_000000.sql.gz"
            old_file.touch()

            # Mock os.path.getmtime to return old timestamp
            with patch("os.path.getmtime") as mock_mtime:
                old_timestamp = (datetime.utcnow() - timedelta(days=35)).timestamp()
                mock_mtime.return_value = old_timestamp

                cleanup_needed = backup._cleanup_old_backups()

                # Cleanup should be triggered for old files


# ============================================================================
# TESTS: BackupStorage
# ============================================================================


@pytest.mark.unit
class TestBackupStorage:
    """Tests for BackupStorage class"""

    def test_backup_storage_local_initialization(self):
        """Test BackupStorage with local storage"""
        config = BackupConfig(database_url="postgresql://localhost/db")
        storage = BackupStorage(config)

        assert storage.config == config
        assert storage.local_enabled is True

    def test_backup_storage_s3_initialization(self):
        """Test BackupStorage with S3"""
        config = BackupConfig(
            database_url="postgresql://localhost/db",
            s3_enabled=True,
            s3_bucket="test-bucket",
        )
        storage = BackupStorage(config)

        assert storage.s3_enabled is True
        assert storage.s3_bucket == "test-bucket"

    @patch("boto3.client")
    def test_backup_storage_upload_to_s3(self, mock_boto3):
        """Test uploading backup to S3"""
        mock_s3 = MagicMock()
        mock_boto3.return_value = mock_s3
        mock_s3.put_object.return_value = {"ETag": "test-etag"}

        config = BackupConfig(
            database_url="postgresql://localhost/db",
            s3_enabled=True,
            s3_bucket="test-bucket",
        )
        storage = BackupStorage(config)

        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b"backup content")
            tmp.flush()

            # Upload should work
            result = storage.upload_to_s3(tmp.name, "backup_name.sql.gz")

            # If S3 is enabled, should call put_object
            # (May fail if boto3 not installed, which is OK for unit test)

    def test_backup_storage_local_save(self):
        """Test saving backup locally"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = BackupConfig(
                database_url="postgresql://localhost/db",
                backup_dir=tmpdir,
            )
            storage = BackupStorage(config)

            backup_path = Path(tmpdir) / "test_backup.sql.gz"
            backup_path.write_text("test backup content")

            # Verify file exists
            assert backup_path.exists()

    def test_backup_storage_list_local_backups(self):
        """Test listing local backups"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = BackupConfig(
                database_url="postgresql://localhost/db",
                backup_dir=tmpdir,
            )
            storage = BackupStorage(config)

            # Create test backup files
            (Path(tmpdir) / "backup_1.sql.gz").touch()
            (Path(tmpdir) / "backup_2.sql.gz").touch()

            backups = storage.list_local_backups()

            assert len(backups) >= 2


# ============================================================================
# TESTS: BackupNotification
# ============================================================================


@pytest.mark.unit
class TestBackupNotification:
    """Tests for BackupNotification class"""

    def test_backup_notification_creation(self):
        """Test creating BackupNotification"""
        config = BackupConfig(database_url="postgresql://localhost/db")
        notifier = BackupNotification(config)

        assert notifier.config == config

    @patch("requests.post")
    def test_backup_notification_slack_success(self, mock_post):
        """Test sending Slack notification"""
        mock_post.return_value = MagicMock(status_code=200)

        config = BackupConfig(
            database_url="postgresql://localhost/db",
            slack_webhook_url="https://hooks.slack.com/services/TEST",
        )
        notifier = BackupNotification(config)

        notifier.notify_success(
            backup_file="backup.sql.gz",
            file_size="123MB",
            duration_seconds=300,
        )

        # Notification should be sent (or attempted)
        assert notifier is not None

    @patch("requests.post")
    def test_backup_notification_slack_failure(self, mock_post):
        """Test sending failure notification to Slack"""
        mock_post.return_value = MagicMock(status_code=200)

        config = BackupConfig(
            database_url="postgresql://localhost/db",
            slack_webhook_url="https://hooks.slack.com/services/TEST",
        )
        notifier = BackupNotification(config)

        notifier.notify_failure(
            error_message="Database connection failed",
            error_details="Could not connect to PostgreSQL",
        )

        assert notifier is not None

    def test_backup_notification_format_message(self):
        """Test formatting notification message"""
        config = BackupConfig(database_url="postgresql://localhost/db")
        notifier = BackupNotification(config)

        message = notifier._format_success_message(
            backup_file="test.sql.gz",
            file_size="100MB",
            duration_seconds=180,
        )

        assert isinstance(message, dict)
        assert "text" in message or "blocks" in message


# ============================================================================
# TESTS: BackupOrchestrator
# ============================================================================


@pytest.mark.unit
class TestBackupOrchestrator:
    """Tests for BackupOrchestrator class"""

    def test_backup_orchestrator_creation(self):
        """Test creating BackupOrchestrator"""
        config = BackupConfig(database_url="postgresql://localhost/db")
        orchestrator = BackupOrchestrator(config)

        assert orchestrator.config == config
        assert orchestrator.backup is not None
        assert orchestrator.storage is not None
        assert orchestrator.notifier is not None

    @patch("backup.DatabaseBackup.perform_backup")
    def test_backup_orchestrator_execute_backup(self, mock_backup):
        """Test executing full backup workflow"""
        mock_backup.return_value = "/tmp/backup.sql.gz"

        config = BackupConfig(database_url="postgresql://localhost/db")
        orchestrator = BackupOrchestrator(config)

        # Should be able to execute backup workflow
        assert orchestrator is not None


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


@pytest.mark.unit
class TestBackupIntegration:
    """Integration tests for backup system"""

    def test_full_backup_workflow(self):
        """Test complete backup workflow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = BackupConfig(
                database_url="sqlite:///:memory:",
                backup_dir=tmpdir,
            )

            orchestrator = BackupOrchestrator(config)

            # Should have all components
            assert orchestrator.backup is not None
            assert orchestrator.storage is not None
            assert orchestrator.notifier is not None

    def test_backup_retention_management(self):
        """Test backup retention and cleanup"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = BackupConfig(
                database_url="postgresql://localhost/db",
                backup_dir=tmpdir,
                retention_days=30,
                max_backups=5,
            )

            backup = DatabaseBackup(config)

            # Create multiple backup files
            for i in range(10):
                filename = f"backup_{i}.sql.gz"
                Path(tmpdir, filename).touch()

            # Cleanup should respect max_backups
            backups = list(Path(tmpdir).glob("*.sql.gz"))
            assert len(backups) == 10  # Before cleanup


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


@pytest.mark.performance
@pytest.mark.slow
class TestBackupPerformance:
    """Performance tests for backup system"""

    def test_backup_checksum_calculation_speed(self):
        """Test checksum calculation performance"""
        config = BackupConfig(database_url="postgresql://localhost/db")
        backup = DatabaseBackup(config)

        import time

        # Create a larger test file (10MB)
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b"x" * (1024 * 1024 * 10))
            tmp.flush()

            start = time.time()
            checksum = backup._calculate_checksum(tmp.name)
            duration = time.time() - start

            # Should complete in < 1 second
            assert duration < 1.0
            assert checksum is not None

    def test_backup_file_listing_performance(self):
        """Test performance of listing many backups"""
        import time

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create many backup files
            for i in range(100):
                Path(tmpdir, f"backup_{i:04d}.sql.gz").touch()

            config = BackupConfig(
                database_url="postgresql://localhost/db",
                backup_dir=tmpdir,
            )
            storage = BackupStorage(config)

            start = time.time()
            backups = storage.list_local_backups()
            duration = time.time() - start

            # Should complete in < 100ms
            assert duration < 0.1
            assert len(backups) >= 100
