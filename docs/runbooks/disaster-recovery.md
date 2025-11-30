# 🚨 Disaster Recovery Runbook

## Overview

This runbook covers disaster recovery procedures for the DevOps Agent platform.

**RTO (Recovery Time Objective):** < 4 hours  
**RPO (Recovery Point Objective):** < 6 hours (automated backups every 6 hours)

---

## 🔄 Backup Strategy

### Automated Backups

1. **Velero - Kubernetes Resources**
   - Schedule: Daily at 2 AM (full), Hourly (critical namespaces)
   - Retention: 30 days (daily), 7 days (hourly)
   - Location: MinIO bucket `velero-backups`

2. **PostgreSQL Database**
   - Schedule: Every 6 hours
   - Retention: 30 days
   - Location: MinIO bucket `backups/postgresql/`

3. **MinIO Data**
   - Replication to external storage (configure separately)
   - Cross-region backup recommended

4. **Git Repository**
   - All configurations in Git (GitOps)
   - Automatic versioning

---

## 📋 Pre-Disaster Checklist

Ensure these are configured BEFORE disaster:

- [ ] Velero installed and configured
- [ ] PostgreSQL backup CronJob running
- [ ] MinIO backup to external storage configured
- [ ] Access to kubeconfig file (stored securely offline)
- [ ] Access to MinIO credentials
- [ ] This runbook accessible offline
- [ ] Team contacts list updated

---

## 🚨 Disaster Scenarios

### Scenario 1: Complete Cluster Loss

**Symptoms:**
- Entire Kubernetes cluster is down
- All nodes unreachable
- No pods running

**Recovery Steps:**

#### 1. Provision New Cluster
```bash
# Install new Kubernetes cluster
# (Specific to your setup - kubeadm, k3s, etc.)

# Verify cluster is running
kubectl get nodes
```

#### 2. Restore Core Infrastructure
```bash
# Install Velero
helm repo add vmware-tanzu https://vmware-tanzu.github.io/helm-charts
helm install velero vmware-tanzu/velero \
  --namespace velero --create-namespace \
  -f kubernetes/backup/velero-values.yaml

# Wait for Velero to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=velero -n velero --timeout=5m
```

#### 3. Restore from Latest Backup
```bash
# List available backups
velero backup get

# Restore latest backup
velero restore create --from-backup daily-backup-YYYYMMDD

# Monitor restore
velero restore describe <restore-name>
velero restore logs <restore-name>
```

#### 4. Verify Services
```bash
# Check all namespaces
kubectl get pods -A

# Verify critical services
kubectl get pods -n production
kubectl get pods -n data

# Check ingress
kubectl get ingress -A
```

#### 5. Restore PostgreSQL Data
```bash
# If PostgreSQL data was not in Velero backup
# Download latest backup from MinIO
mc cp minio/backups/postgresql/postgresql_backup_LATEST.sql.gz /tmp/

# Restore to PostgreSQL
gunzip < /tmp/postgresql_backup_LATEST.sql.gz | \
  kubectl exec -i postgresql-0 -n data -- psql -U devops -d devops_agent

# Verify data
kubectl exec -it postgresql-0 -n data -- psql -U devops -d devops_agent -c "SELECT COUNT(*) FROM <table>;"
```

#### 6. Verify Application
```bash
# Test frontend
curl -I https://yourdomain.com

# Test backend API
curl https://api.yourdomain.com/api/health

# Test database connectivity
kubectl exec -it deployment/backend-python -n production -- python -c "from app.core.database import engine; print('DB OK')"
```

**Expected Recovery Time:** 2-4 hours

---

### Scenario 2: Database Corruption/Loss

**Symptoms:**
- PostgreSQL not starting
- Data corruption errors
- Tables missing

**Recovery Steps:**

#### 1. Stop Applications
```bash
# Scale down applications to prevent writes
kubectl scale deployment --all --replicas=0 -n production
```

#### 2. Restore Database
```bash
# Get latest backup
mc ls minio/backups/postgresql/ | tail -1

# Download
mc cp minio/backups/postgresql/postgresql_backup_YYYYMMDD_HHMMSS.sql.gz /tmp/

# Drop and recreate database
kubectl exec -it postgresql-0 -n data -- psql -U postgres -c "DROP DATABASE IF EXISTS devops_agent;"
kubectl exec -it postgresql-0 -n data -- psql -U postgres -c "CREATE DATABASE devops_agent OWNER devops;"

# Restore
gunzip < /tmp/postgresql_backup_YYYYMMDD_HHMMSS.sql.gz | \
  kubectl exec -i postgresql-0 -n data -- psql -U devops -d devops_agent
```

#### 3. Verify and Restart
```bash
# Verify data
kubectl exec -it postgresql-0 -n data -- psql -U devops -d devops_agent -c "\dt"

# Scale applications back up
kubectl scale deployment backend-python --replicas=3 -n production
kubectl scale deployment frontend --replicas=2 -n production
```

**Expected Recovery Time:** 30 minutes - 1 hour

---

### Scenario 3: Namespace Deleted Accidentally

**Symptoms:**
- Entire namespace missing
- All pods in namespace gone

**Recovery Steps:**

```bash
# Restore specific namespace from backup
velero restore create --from-backup daily-backup-LATEST \
  --include-namespaces production

# Monitor restore
watch kubectl get pods -n production
```

**Expected Recovery Time:** 10-30 minutes

---

### Scenario 4: Single Service Failure

**Symptoms:**
- One deployment/pod not working
- Other services operational

**Recovery Steps:**

```bash
# Try restart first
kubectl rollout restart deployment/<name> -n <namespace>

# If that doesn't work, restore from backup
velero restore create --from-backup daily-backup-LATEST \
  --include-resources deployments,services \
  --selector app=<app-name>
```

**Expected Recovery Time:** 5-15 minutes

---

## 🔍 Verification Checklist

After any recovery, verify:

- [ ] All pods are Running
  ```bash
  kubectl get pods -A | grep -v Running
  ```

- [ ] All services have endpoints
  ```bash
  kubectl get endpoints -A
  ```

- [ ] Ingress is working
  ```bash
  curl -I https://yourdomain.com
  ```

- [ ] Database is accessible
  ```bash
  kubectl exec -it postgresql-0 -n data -- psql -U devops -d devops_agent -c "SELECT 1;"
  ```

- [ ] Application is functional
  ```bash
  # Test main workflows
  # - User can login
  # - Chat works
  # - Agent can execute commands
  ```

- [ ] Monitoring is operational
  ```bash
  kubectl get pods -n monitoring
  curl http://prometheus:9090/-/healthy
  ```

- [ ] Backups are running
  ```bash
  kubectl get cronjobs -n data
  velero schedule get
  ```

---

## 📊 Testing DR Procedures

**Test quarterly!**

### DR Test Procedure

1. **Schedule Test Window** (non-production hours)

2. **Create Test Namespace**
   ```bash
   kubectl create namespace dr-test
   kubectl apply -f kubernetes/apps/ -n dr-test
   ```

3. **Test Backup**
   ```bash
   velero backup create dr-test-backup --include-namespaces dr-test
   velero backup describe dr-test-backup
   ```

4. **Delete Test Namespace**
   ```bash
   kubectl delete namespace dr-test
   ```

5. **Test Restore**
   ```bash
   velero restore create --from-backup dr-test-backup
   kubectl wait --for=condition=ready pod --all -n dr-test --timeout=5m
   ```

6. **Verify Application**
   ```bash
   kubectl get all -n dr-test
   # Test application functionality
   ```

7. **Cleanup**
   ```bash
   kubectl delete namespace dr-test
   velero backup delete dr-test-backup
   ```

8. **Document Results**
   - Actual RTO achieved
   - Any issues encountered
   - Action items for improvement

---

## 🚨 Emergency Contacts

| Role | Contact | When to Escalate |
|------|---------|------------------|
| On-Call Engineer | Check Grafana OnCall | First responder |
| Lead Engineer | [Contact] | > 1 hour downtime |
| CTO/VP Engineering | [Contact] | > 4 hours or data loss |
| Infra Provider | [Contact] | Infrastructure issues |

---

## 📚 Related Documentation

- [Backup Configuration](../kubernetes/backup/)
- [Velero Documentation](https://velero.io/docs/)
- [Deployment Runbook](./deployment.md)
- [Rollback Runbook](./rollback.md)

---

## 📝 Incident Log Template

After each DR event, document:

```markdown
## DR Incident: [Date]

**Type:** [Scenario number/description]
**Start Time:** [Time]
**End Time:** [Time]
**Total Downtime:** [Duration]

**Root Cause:**
[Description]

**Actions Taken:**
1. [Step 1]
2. [Step 2]
...

**RTO Achieved:** [Actual time]
**RPO Achieved:** [Data loss timeframe]

**Lessons Learned:**
- [Learning 1]
- [Learning 2]

**Action Items:**
- [ ] [Action 1]
- [ ] [Action 2]
```

---

**Last Updated:** 2025-11-30  
**Next Review:** Quarterly  
**Version:** 1.0
