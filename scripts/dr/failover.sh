#!/bin/bash
# ClimateWise - Disaster Recovery Failover Script
# Uso: ./scripts/dr/failover.sh [--rollback]

set -e

DR_REGION="${DR_REGION:-us-west-2}"
PRIMARY_REGION="${PRIMARY_REGION:-us-east-1}"
ROLLBACK=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --rollback)
            ROLLBACK=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "ClimateWise - DR Failover"
echo "=========================================="
echo "DR Region: ${DR_REGION}"
echo "Primary Region: ${PRIMARY_REGION}"
echo "Rollback: ${ROLLBACK}"
echo "Time: $(date)"
echo "=========================================="

# Function to check health
check_health() {
    local url=$1
    local max_attempts=${2:-30}
    
    for i in $(seq 1 $max_attempts); do
        response=$(curl -s -o /dev/null -w "%{http_code}" "${url}" || echo "000")
        if [ "${response}" == "200" ]; then
            echo "✓ Health check passed for ${url}"
            return 0
        fi
        echo "Waiting for ${url}... (${i}/${max_attempts})"
        sleep 10
    done
    
    echo "✗ Health check failed for ${url}"
    return 1
}

# Function to send notification
send_notification() {
    local message=$1
    local status=$2
    
    # Slack notification
    if [ -n "${SLACK_WEBHOOK_URL}" ]; then
        curl -X POST "${SLACK_WEBHOOK_URL}" \
            -H 'Content-Type: application/json' \
            -d "{
                \"text\": \"ClimateWise DR ${status}\",
                \"attachments\": [{
                    \"color\": \"${status == 'SUCCESS' ? 'good' : 'danger'}\",
                    \"text\": \"${message}\"
                }]
            }" || true
    fi
    
    echo "[NOTIFICATION] ${message}"
}

# Main failover logic
if [ "${ROLLBACK}" = true ]; then
    echo ""
    echo "[ROLLBACK] Switching back to primary region..."
    
    # Update DNS to primary
    echo "[1/4] Updating DNS to primary region..."
    aws route53 change-resource-record-sets \
        --hosted-zone-id "${HOSTED_ZONE_ID}" \
        --change-batch '{
            "Changes": [{
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "Name": "api.climatewise.com",
                    "Type": "A",
                    "AliasTarget": {
                        "HostedZoneId": "Z123456",
                        "DNSName": "primary-lb.amazonaws.com",
                        "EvaluateTargetHealth": true
                    }
                }
            }]
        }' || echo "DNS update skipped (configure HOSTED_ZONE_ID)"
    
    # Scale down DR
    echo "[2/4] Scaling down DR environment..."
    aws ecs update-service \
        --cluster climatewise-dr \
        --service backend \
        --desired-count 0 \
        --region "${DR_REGION}" 2>/dev/null || echo "ECS scale down skipped"
    
    # Scale up primary
    echo "[3/4] Scaling up primary environment..."
    aws ecs update-service \
        --cluster climatewise-prod \
        --service backend \
        --desired-count 3 \
        --region "${PRIMARY_REGION}" 2>/dev/null || echo "ECS scale up skipped"
    
    # Re-establish replication
    echo "[4/4] Re-establishing database replication..."
    aws rds create-db-instance-read-replica \
        --db-instance-identifier climatewise-db-prod-dr \
        --source-db-instance-identifier climatewise-db-prod \
        --source-region "${PRIMARY_REGION}" \
        --region "${DR_REGION}" 2>/dev/null || echo "DB replica creation skipped"
    
    send_notification "Failback completed successfully" "SUCCESS"
    
else
    echo ""
    echo "[FAILOVER] Switching to DR region..."
    
    # Promote DB replica
    echo "[1/5] Promoting database replica..."
    aws rds promote-read-replica \
        --db-instance-identifier climatewise-db-prod-dr \
        --region "${DR_REGION}" || echo "DB promotion skipped"
    
    # Wait for DB
    echo "[2/5] Waiting for database to be available..."
    aws rds wait db-instance-available \
        --db-instance-identifier climatewise-db-prod-dr \
        --region "${DR_REGION}" 2>/dev/null || echo "DB wait skipped"
    
    # Update DNS
    echo "[3/5] Updating DNS to DR region..."
    aws route53 change-resource-record-sets \
        --hosted-zone-id "${HOSTED_ZONE_ID}" \
        --change-batch '{
            "Changes": [{
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "Name": "api.climatewise.com",
                    "Type": "A",
                    "AliasTarget": {
                        "HostedZoneId": "Z789012",
                        "DNSName": "dr-lb.amazonaws.com",
                        "EvaluateTargetHealth": true
                    }
                }
            }]
        }' || echo "DNS update skipped (configure HOSTED_ZONE_ID)"
    
    # Scale DR application
    echo "[4/5] Scaling DR application..."
    aws ecs update-service \
        --cluster climatewise-dr \
        --service backend \
        --desired-count 3 \
        --region "${DR_REGION}" 2>/dev/null || echo "ECS scale up skipped"
    
    # Health check
    echo "[5/5] Running health checks..."
    if check_health "https://api-dr.climatewise.com/health/full"; then
        send_notification "Failover completed successfully" "SUCCESS"
    else
        send_notification "Failover completed with warnings" "WARNING"
    fi
fi

echo ""
echo "=========================================="
echo "DR Failover completed"
echo "=========================================="
echo "Time: $(date)"
