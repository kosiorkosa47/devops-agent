# Rollback Runbook - DevOps Agent

## Overview
Quick reference for rolling back deployments when issues are detected.

## When to Rollback

Rollback immediately if:
- Error rate > 5% for 5+ minutes
- P95 latency > 2 seconds for 5+ minutes
- Critical functionality broken
- Data loss detected
- Security vulnerability exploited
- SLO budget will be exhausted

## Quick Rollback (< 2 minutes)

### Method 1: Kubernetes Rollback (Fastest)

```bash
# Rollback specific deployment
kubectl rollout undo deployment/frontend -n production

# Rollback to specific revision
kubectl rollout history deployment/frontend -n production
kubectl rollout undo deployment/frontend --to-revision=3 -n production

# Verify rollback
kubectl rollout status deployment/frontend -n production --timeout=2m
```

### Method 2: GitLab CI Rollback

```bash
# 1. Go to GitLab CI/CD → Pipelines
# 2. Find the last successful production deployment
# 3. Click "Rollback" button (manual job)
# 4. Monitor in Grafana

# Or trigger via API
curl --request POST \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "https://gitlab.com/api/v4/projects/${PROJECT_ID}/jobs/${JOB_ID}/play"
```

### Method 3: Re-deploy Previous Version

```bash
# Find last working version
git log --oneline -10

# Checkout that version
git checkout v1.0.0

# Deploy
kubectl apply -k kubernetes/overlays/prod/
```

## Rollback Steps by Component

### Frontend (Next.js)

```bash
# Quick rollback
kubectl rollout undo deployment/frontend -n production

# Verify
curl -f https://yourdomain.com/health
kubectl logs -f deployment/frontend -n production --tail=20
```

### Backend Python

```bash
# Rollback
kubectl rollout undo deployment/backend-python -n production

# Verify API
curl -f https://yourdomain.com/api/health
```

### Backend Rust

```bash
# Rollback
kubectl rollout undo deployment/backend-rust -n production

# Verify
kubectl get pods -n production -l app=backend-rust
```

### Database Migration Rollback

**⚠️ CAUTION: Data loss risk**

```bash
# For PostgreSQL with migration tools
kubectl exec -it postgresql-0 -n data -- psql -U postgres -d dbname

# Run rollback migration
# Example with Alembic:
kubectl exec -it backend-python-pod -n production -- \
  alembic downgrade -1

# Example with Django:
kubectl exec -it backend-python-pod -n production -- \
  python manage.py migrate app_name 0042_previous_migration
```

## Post-Rollback Actions

### 1. Verify System Health

```bash
# Check all pods are running
kubectl get pods -n production

# Check error rate (should be < 0.1%)
# Open Grafana → Application Dashboard → Error Rate

# Check latency (P95 < 500ms)
# Open Grafana → Application Dashboard → Latency

# Verify monitoring
curl -s http://prometheus:9090/api/v1/query?query=up{namespace="production"}
```

### 2. Root Cause Analysis

```bash
# Collect logs from failed deployment
kubectl logs deployment/frontend -n production \
  --since=30m > /tmp/rollback-logs-frontend.txt

# Export Prometheus metrics around the incident
# Time range: 30 minutes before rollback to now

# Gather events
kubectl get events -n production \
  --sort-by='.lastTimestamp' | tail -50 > /tmp/rollback-events.txt
```

### 3. Create Incident Report

Create a post-mortem document including:
- What happened
- When it was detected
- Impact (users affected, duration)
- Root cause
- Why rollback was necessary
- Action items to prevent recurrence

Template location: `docs/incidents/template.md`

### 4. Communication

```bash
# Notify stakeholders
# - Update status page: "Resolved"
# - Post in Slack/Teams: "Issue resolved via rollback"
# - Create follow-up task for fix

# Example message:
# "🔄 Rollback completed at 14:30 UTC
#  - Production is stable
#  - Error rate: 0.02%
#  - All services healthy
#  - Post-mortem scheduled for tomorrow"
```

## Emergency Contacts

| Role | Contact | When to Escalate |
|------|---------|------------------|
| On-Call Engineer | Check Grafana OnCall | First responder |
| Lead Engineer | [Contact info] | Rollback doesn't resolve issue |
| CTO/VP Eng | [Contact info] | > 30 min downtime or data loss |

## Rollback Decision Tree

```
Is error rate > 5%?
├─ YES → Rollback immediately
└─ NO
   ├─ Is P95 latency > 2s?
   │  ├─ YES → Rollback immediately
   │  └─ NO
   │     ├─ Is critical feature broken?
   │     │  ├─ YES → Rollback immediately
   │     │  └─ NO
   │     │     ├─ Is SLO at risk?
   │     │     │  ├─ YES → Rollback within 10 min
   │     │     │  └─ NO → Monitor closely, prepare rollback
```

## Failed Rollback Recovery

If rollback fails or makes things worse:

```bash
# 1. Stop all traffic to affected services
kubectl scale deployment/frontend --replicas=0 -n production

# 2. Enable maintenance mode
kubectl apply -f kubernetes/maintenance-mode.yaml

# 3. Restore from backup (if database affected)
# See docs/runbooks/disaster-recovery.md

# 4. Re-deploy last known good version
git checkout <last-good-tag>
kubectl apply -k kubernetes/overlays/prod/ --force

# 5. Scale up gradually
kubectl scale deployment/frontend --replicas=1 -n production
# Verify health
kubectl scale deployment/frontend --replicas=3 -n production
```

## Prevention

After each rollback:

1. Add automated tests for the bug
2. Improve monitoring/alerting
3. Update deployment checklist
4. Consider canary deployment strategy
5. Document lessons learned

## Testing Rollback Procedures

**In staging environment, practice rollback quarterly:**

```bash
# 1. Deploy intentionally broken version to staging
# 2. Verify alerts fire
# 3. Execute rollback procedure
# 4. Measure time to recover (target: < 5 minutes)
# 5. Document any issues with procedure
```

## Related Documentation

- [Deployment Runbook](./deployment.md)
- [Incident Response](./incident-response.md)
- [Disaster Recovery](./disaster-recovery.md)
- [Monitoring Guide](./monitoring.md)

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2025-11-30 | 1.0 | ATLAS | Initial version |
