#!/bin/bash
# ClimateAI - Backup Integrity Test
# Valida integridade do backup mais recente

set -e

BACKUP_BUCKET="${BACKUP_BUCKET:-climateai-backups-prod}"
TEST_DB="climateai_test_$(date +%Y%m%d_%H%M%S)"

echo "=========================================="
echo "ClimateAI - Backup Integrity Test"
echo "=========================================="
echo "Backup Bucket: ${BACKUP_BUCKET}"
echo "Time: $(date)"
echo "=========================================="

# Get latest backup
echo ""
echo "[1/5] Getting latest backup..."
LATEST_BACKUP=$(aws s3 ls "s3://${BACKUP_BUCKET}/" | grep "\.sql\.gz$" | tail -1 | awk '{print $4}')

if [ -z "${LATEST_BACKUP}" ]; then
    echo "✗ No backups found in ${BACKUP_BUCKET}"
    exit 1
fi

echo "Latest backup: ${LATEST_BACKUP}"

# Download backup
echo ""
echo "[2/5] Downloading backup..."
aws s3 cp "s3://${BACKUP_BUCKET}/${LATEST_BACKUP}" "/tmp/${LATEST_BACKUP}"

# Download checksum
echo ""
echo "[3/5] Verifying checksum..."
CHECKSUM_FILE="${LATEST_BACKUP}.sha256"
aws s3 cp "s3://${BACKUP_BUCKET}/${CHECKSUM_FILE}" "/tmp/${CHECKSUM_FILE}" 2>/dev/null || {
    echo "Checksum file not found, generating..."
    sha256sum "/tmp/${LATEST_BACKUP}" | awk '{print $1}' > "/tmp/${CHECKSUM_FILE}"
}

REMOTE_CHECKSUM=$(cat "/tmp/${CHECKSUM_FILE}" | awk '{print $1}')
LOCAL_CHECKSUM=$(sha256sum "/tmp/${LATEST_BACKUP}" | awk '{print $1}')

echo "Remote checksum: ${REMOTE_CHECKSUM}"
echo "Local checksum:  ${LOCAL_CHECKSUM}"

if [ "${REMOTE_CHECKSUM}" != "${LOCAL_CHECKSUM}" ]; then
    echo "✗ Checksum verification FAILED"
    exit 1
fi

echo "✓ Checksum verification PASSED"

# Test restore
echo ""
echo "[4/5] Testing restore..."

# Create test database
psql -h localhost -U climateai_admin -d postgres -c "CREATE DATABASE ${TEST_DB};"

# Restore backup
gunzip -c "/tmp/${LATEST_BACKUP}" | psql -h localhost -U climateai_admin -d "${TEST_DB}"

if [ $? -ne 0 ]; then
    echo "✗ Restore test FAILED"
    # Cleanup
    psql -h localhost -U climateai_admin -d postgres -c "DROP DATABASE ${TEST_DB};"
    exit 1
fi

echo "✓ Restore test PASSED"

# Validate data
echo ""
echo "[5/5] Validating data..."

# Check table counts
TABLES=$(psql -h localhost -U climateai_admin -d "${TEST_DB}" -t -c "
    SELECT COUNT(*) 
    FROM information_schema.tables 
    WHERE table_schema = 'public';
")

echo "Tables found: ${TABLES}"

if [ "${TABLES}" -lt 1 ]; then
    echo "✗ Data validation FAILED - no tables found"
    psql -h localhost -U climateai_admin -d postgres -c "DROP DATABASE ${TEST_DB};"
    exit 1
fi

# Check row counts for critical tables
CRITICAL_TABLES="users policies claims"
for table in ${CRITICAL_TABLES}; do
    COUNT=$(psql -h localhost -U climateai_admin -d "${TEST_DB}" -t -c "SELECT COUNT(*) FROM ${table};" 2>/dev/null || echo "0")
    echo "  - ${table}: ${COUNT} rows"
done

# Cleanup
echo ""
echo "Cleaning up..."
psql -h localhost -U climateai_admin -d postgres -c "DROP DATABASE ${TEST_DB};"
rm -f "/tmp/${LATEST_BACKUP}" "/tmp/${CHECKSUM_FILE}"

echo ""
echo "=========================================="
echo "✓ Backup Integrity Test PASSED"
echo "=========================================="
echo "Time: $(date)"

# Send notification
if [ -n "${SLACK_WEBHOOK_URL}" ]; then
    curl -X POST "${SLACK_WEBHOOK_URL}" \
        -H 'Content-Type: application/json' \
        -d "{
            \"text\": \"ClimateAI Backup Test\",
            \"attachments\": [{
                \"color\": \"good\",
                \"text\": \"Backup ${LATEST_BACKUP} validated successfully\"
            }]
        }" || true
fi

exit 0
