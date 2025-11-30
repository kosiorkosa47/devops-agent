# Quick Start Guide - DevOps Agent

## 🚀 Get Started in 30 Minutes

This guide will help you deploy the complete DevOps Agent infrastructure.

## Prerequisites

Ensure you have:
- ✅ Kubernetes cluster (v1.28+) running
- ✅ `kubectl` configured with admin access
- ✅ `helm` (v3.12+) installed
- ✅ Domain name with DNS access
- ✅ GitLab account (for CI/CD)
- ✅ 100GB+ available storage

## Step 1: Clone Repository

```bash
git clone <your-repo-url>
cd devops-agent
```

## Step 2: Configure Domain Names

Edit these files and replace `yourdomain.com`:

```bash
# Update domain names
find . -type f -name "*.yaml" -exec sed -i 's/yourdomain.com/your-actual-domain.com/g' {} +
find . -type f -name "*.md" -exec sed -i 's/yourdomain.com/your-actual-domain.com/g' {} +
```

## Step 3: Deploy Base Infrastructure

```bash
# Create namespaces and RBAC
kubectl apply -k kubernetes/base/

# Verify namespaces
kubectl get namespaces
```

## Step 4: Deploy Storage (MinIO)

```bash
# Deploy MinIO
kubectl apply -f kubernetes/base/minio-deployment.yaml

# Wait for MinIO to be ready
kubectl wait --for=condition=ready pod -l app=minio -n storage --timeout=5m

# Get MinIO credentials
kubectl get secret minio-credentials -n storage -o jsonpath='{.data.MINIO_ROOT_PASSWORD}' | base64 -d
```

## Step 5: Deploy Monitoring Stack

```bash
# Add Helm repos
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Deploy Prometheus + Grafana
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  -f monitoring/prometheus/values.yaml \
  -n monitoring --create-namespace

# Deploy Loki
helm upgrade --install loki grafana/loki-stack \
  -f monitoring/loki/values.yaml \
  -n monitoring

# Wait for deployments
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus -n monitoring --timeout=5m

# Get Grafana password
kubectl get secret prometheus-grafana -n monitoring -o jsonpath='{.data.admin-password}' | base64 -d
```

## Step 6: Deploy Secrets Management (Infisical)

```bash
# First, ensure PostgreSQL is running (deploy if needed)
# kubectl apply -f kubernetes/base/postgresql.yaml

# Deploy Infisical
kubectl apply -f security/infisical/deployment.yaml

# Deploy Infisical Operator
kubectl apply -f security/infisical/operator.yaml

# Wait for Infisical
kubectl wait --for=condition=ready pod -l app=infisical -n infisical --timeout=5m
```

## Step 7: Setup GitLab CI/CD

```bash
# 1. Register GitLab Runner in your cluster
helm repo add gitlab https://charts.gitlab.io
helm upgrade --install gitlab-runner gitlab/gitlab-runner \
  --set gitlabUrl=https://gitlab.com \
  --set runnerRegistrationToken=${YOUR_GITLAB_TOKEN} \
  -n gitlab-runner --create-namespace

# 2. Add CI/CD variables in GitLab:
# - KUBE_URL: Your Kubernetes API URL
# - KUBE_TOKEN: Service account token
# - CI_REGISTRY_PASSWORD: Docker registry password
```

## Step 8: Deploy Ingress Controller

```bash
# Deploy Nginx Ingress
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --set controller.service.type=LoadBalancer \
  -n ingress-nginx --create-namespace

# Get external IP
kubectl get svc -n ingress-nginx ingress-nginx-controller
```

## Step 9: Deploy Cert-Manager (TLS)

```bash
# Deploy cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create Let's Encrypt issuer
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@domain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

## Step 10: Verify Installation

```bash
# Check all pods are running
kubectl get pods -A

# Check services
kubectl get svc -A

# Access Grafana
echo "Grafana: https://grafana.yourdomain.com"
echo "Username: admin"
kubectl get secret prometheus-grafana -n monitoring -o jsonpath='{.data.admin-password}' | base64 -d

# Access MinIO
echo "MinIO Console: https://minio.yourdomain.com"

# Access Infisical
echo "Infisical: https://secrets.yourdomain.com"
```

## Step 11: Deploy Your Application

```bash
# Create application secrets in Infisical first
# Then deploy using GitLab CI or kubectl

# Example: Deploy frontend
kubectl apply -f apps/frontend/k8s/deployment.yaml
```

## 🎯 What's Next?

1. **Configure Monitoring**: 
   - Import dashboards from `monitoring/grafana/dashboards/`
   - Review alert rules in Grafana

2. **Setup Secrets**:
   - Login to Infisical
   - Create project for your app
   - Add secrets (API keys, database passwords, etc.)

3. **Deploy Applications**:
   - Push code to GitLab
   - CI/CD pipeline will automatically build and deploy

4. **Configure Backups**:
   - Setup Velero for cluster backups
   - Configure PostgreSQL automated backups
   - Test restore procedures

## 🔧 Common Issues

### Pods in Pending State
```bash
# Check events
kubectl describe pod <pod-name> -n <namespace>

# Common causes:
# - Insufficient resources
# - Missing persistent volumes
# - Image pull errors
```

### Can't Access Services
```bash
# Check ingress
kubectl get ingress -A

# Check DNS
nslookup grafana.yourdomain.com

# Check certificates
kubectl get certificate -A
```

### Monitoring Not Working
```bash
# Check Prometheus targets
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Open: http://localhost:9090/targets

# Check ServiceMonitors
kubectl get servicemonitor -A
```

## 📚 Additional Resources

- [Full Documentation](./architecture/overview.md)
- [Deployment Runbook](./runbooks/deployment.md)
- [Troubleshooting Guide](./runbooks/troubleshooting.md)
- [Security Best Practices](./security/guidelines.md)

## 🆘 Getting Help

- Check logs: `kubectl logs <pod-name> -n <namespace>`
- Review alerts: Grafana → Alerting
- Check status: `cat atlas-progress.txt`
- Review tasks: `cat devops-tasks.json`

## ✅ Success Checklist

- [ ] All namespaces created
- [ ] MinIO accessible and buckets created
- [ ] Prometheus collecting metrics
- [ ] Grafana dashboards visible
- [ ] Loki aggregating logs
- [ ] Infisical accessible
- [ ] GitLab Runner registered
- [ ] Ingress controller working
- [ ] TLS certificates issued
- [ ] Test application deployed
- [ ] Monitoring alerts configured
- [ ] Backups configured

Congratulations! Your DevOps Agent infrastructure is ready! 🎉
