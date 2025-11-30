#!/bin/bash
# Maintenance Cleanup Script
# Run weekly via CronJob

set -e

echo "=== DevOps Agent Maintenance Cleanup ==="
echo "Started at: $(date)"

# Cleanup old Docker images (older than 30 days)
echo "Cleaning up old Docker images..."
docker image prune -a --filter "until=720h" -f || true

# Cleanup old logs from MinIO
echo "Cleaning up old logs from MinIO..."
mc alias set minio ${MINIO_URL} ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY}
mc rm --recursive --force --older-than 30d minio/logs/ || true

# Cleanup old backups (keep last 30 days)
echo "Cleaning up old backups..."
mc rm --recursive --force --older-than 30d minio/backups/postgresql/ || true

# PostgreSQL vacuum and analyze
echo "Running PostgreSQL maintenance..."
kubectl exec -n data postgresql-0 -- psql -U devops -d devops_agent -c "VACUUM ANALYZE;"

# Cleanup completed pods
echo "Cleaning up completed pods..."
kubectl delete pods --field-selector=status.phase==Succeeded -A
kubectl delete pods --field-selector=status.phase==Failed -A

# Certificate renewal check
echo "Checking certificate expiry..."
kubectl get certificates -A -o json | jq -r '.items[] | select(.status.renewalTime != null) | "\(.metadata.namespace)/\(.metadata.name): \(.status.renewalTime)"'

# Disk usage report
echo "Disk usage report:"
kubectl exec -n data postgresql-0 -- df -h /var/lib/postgresql/data
kubectl exec -n storage minio-0 -- df -h /data

# Resource usage summary
echo "Resource usage summary:"
kubectl top nodes
kubectl top pods -n production --sort-by=memory | head -10

echo "=== Maintenance cleanup completed at: $(date) ==="
