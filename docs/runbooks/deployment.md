# Deployment Runbook - DevOps Agent

## Overview
This runbook covers standard deployment procedures for the DevOps Agent platform.

## Prerequisites
- Access to Kubernetes cluster
- `kubectl` configured
- GitLab CI/CD credentials
- Infisical access for secrets

## Standard Deployment Process

### 1. Pre-Deployment Checks

```bash
# Verify cluster health
kubectl get nodes
kubectl get pods -A | grep -v Running

# Check resource availability
kubectl top nodes
kubectl describe nodes | grep -A 5 "Allocated resources"

# Verify monitoring is operational
curl -s http://prometheus:9090/-/healthy
curl -s http://alertmanager:9093/-/healthy

# Check for active critical alerts
kubectl get prometheusrules -A
```

### 2. Deploy to Development

```bash
# Automatic via GitLab CI on develop branch
git checkout develop
git pull origin develop
git push origin develop

# Or manually
kubectl set image deployment/frontend \
  frontend=registry.gitlab.com/yourorg/devops-agent/frontend:${TAG} \
  -n dev

kubectl rollout status deployment/frontend -n dev --timeout=5m
```

### 3. Deploy to Staging

```bash
# Via GitLab CI (manual trigger on main branch)
# 1. Merge develop to main
# 2. Go to GitLab CI/CD → Pipelines
# 3. Click "play" icon on deploy:staging job

# Or manually
kubectl set image deployment/frontend \
  frontend=registry.gitlab.com/yourorg/devops-agent/frontend:${TAG} \
  -n staging

kubectl rollout status deployment/frontend -n staging --timeout=5m
```

### 4. Smoke Tests

```bash
# Test health endpoints
curl -f https://staging.yourdomain.com/health
curl -f https://staging.yourdomain.com/api/health

# Check application logs
kubectl logs -f deployment/frontend -n staging --tail=50

# Verify metrics are being collected
curl -s http://prometheus:9090/api/v1/query?query=up{namespace="staging"}
```

### 5. Deploy to Production

**⚠️ CRITICAL: Production deployments require manual approval**

```bash
# 1. Create a git tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# 2. Go to GitLab CI/CD → Pipelines
# 3. Find pipeline for the tag
# 4. Review changes and logs
# 5. Click "play" icon on deploy:production job

# 6. Monitor rollout
kubectl rollout status deployment/frontend -n production --timeout=10m
kubectl rollout status deployment/backend-python -n production --timeout=10m
kubectl rollout status deployment/backend-rust -n production --timeout=10m
```

### 6. Post-Deployment Verification

```bash
# Health checks
curl -f https://yourdomain.com/health
curl -f https://yourdomain.com/api/health

# Check error rates in Grafana
# Navigate to: Grafana → Kubernetes Overview → Error Rate panel

# Verify SLO compliance
# Navigate to: Grafana → SLO Dashboard

# Check application logs for errors
kubectl logs -f deployment/frontend -n production --tail=100 | grep -i error

# Monitor metrics for anomalies
watch -n 5 'kubectl top pods -n production'
```

### 7. Communication

```bash
# Notify stakeholders (if applicable)
# - Post in Slack/Teams channel
# - Update status page
# - Send deployment summary email

# Example message:
# "✅ Production deployment v1.0.0 completed successfully
#  - Frontend: 3 pods healthy
#  - Backend: 5 pods healthy
#  - Error rate: < 0.01%
#  - P95 latency: 150ms"
```

## Blue-Green Deployment (Advanced)

For zero-downtime deployments:

```bash
# 1. Deploy new version with different label
kubectl apply -f kubernetes/overlays/prod/deployment-v2.yaml

# 2. Wait for new pods to be ready
kubectl wait --for=condition=ready pod -l version=v2 -n production --timeout=5m

# 3. Switch service to new version
kubectl patch service frontend -n production \
  -p '{"spec":{"selector":{"version":"v2"}}}'

# 4. Monitor for issues (5-10 minutes)
watch -n 10 'kubectl get pods -n production -l version=v2'

# 5. If successful, scale down old version
kubectl scale deployment frontend-v1 --replicas=0 -n production

# 6. If issues detected, rollback immediately
kubectl patch service frontend -n production \
  -p '{"spec":{"selector":{"version":"v1"}}}'
```

## Canary Deployment

For gradual rollouts:

```bash
# 1. Deploy canary with 10% traffic
kubectl apply -f kubernetes/overlays/prod/canary.yaml

# 2. Monitor canary metrics
# Check error rate, latency, and resource usage for 30 minutes

# 3. If metrics are good, increase to 50%
kubectl scale deployment frontend-canary --replicas=5 -n production

# 4. If still good, complete rollout
kubectl apply -f kubernetes/overlays/prod/deployment.yaml
kubectl delete -f kubernetes/overlays/prod/canary.yaml
```

## Troubleshooting

### Deployment Stuck

```bash
# Check pod events
kubectl describe pod <pod-name> -n production

# Check replica set
kubectl get rs -n production
kubectl describe rs <replicaset-name> -n production

# Check image pull
kubectl get events -n production --sort-by='.lastTimestamp' | grep Pull
```

### Pod CrashLooping

```bash
# Check logs
kubectl logs <pod-name> -n production --previous

# Check resource limits
kubectl describe pod <pod-name> -n production | grep -A 10 "Limits"

# Check liveness/readiness probes
kubectl describe pod <pod-name> -n production | grep -A 10 "Liveness"
```

### High Error Rate After Deployment

```bash
# Immediate rollback
kubectl rollout undo deployment/frontend -n production

# Or use GitLab rollback job
# Go to CI/CD → Pipelines → Click "Rollback" button
```

## Rollback Procedures

See [rollback.md](./rollback.md) for detailed rollback procedures.

## Security Checklist

Before production deployment:

- [ ] All secrets managed via Infisical
- [ ] Container images scanned with Trivy (no HIGH/CRITICAL vulnerabilities)
- [ ] Network policies applied
- [ ] Pod Security Standards enforced (restricted)
- [ ] Resource limits defined
- [ ] Health checks configured
- [ ] Monitoring and alerting active
- [ ] Backup verified within last 24 hours

## Maintenance Window

For deployments requiring downtime:

1. Schedule maintenance window (notify 72 hours in advance)
2. Enable maintenance mode page
3. Perform deployment
4. Run verification tests
5. Disable maintenance mode
6. Monitor for 30 minutes post-deployment

## Contact Information

- **On-Call Engineer**: Check Grafana OnCall schedule
- **Escalation**: [Your escalation procedure]
- **Documentation**: https://docs.yourdomain.com

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2025-11-30 | 1.0 | ATLAS | Initial version |
