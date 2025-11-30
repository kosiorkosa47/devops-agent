# 🚀 Complete Deployment Guide - DevOps Agent with Claude API

This guide will help you deploy the full DevOps Agent application from scratch.

## 📋 Prerequisites

- ✅ Kubernetes cluster (v1.28+) running
- ✅ `kubectl` configured with admin access
- ✅ `helm` (v3.12+) installed
- ✅ Domain name with DNS access
- ✅ **Claude API Key** from Anthropic
- ✅ GitLab account (for CI/CD)
- ✅ 100GB+ available storage

## 🎯 What You'll Deploy

1. **Infrastructure Layer**: MinIO, PostgreSQL, Redis
2. **Monitoring Stack**: Prometheus, Grafana, Loki
3. **Security Layer**: Infisical secrets management
4. **Application Layer**: Python backend + Next.js frontend
5. **CI/CD**: GitLab pipelines

---

## Step 1: Base Infrastructure

```bash
# Create all namespaces and RBAC
kubectl apply -k kubernetes/base/

# Verify
kubectl get namespaces
kubectl get serviceaccounts -A
```

## Step 2: Deploy Data Layer

### PostgreSQL

```bash
# Deploy PostgreSQL
kubectl apply -f apps/database/postgresql.yaml

# Wait for it to be ready
kubectl wait --for=condition=ready pod -l app=postgresql -n data --timeout=5m

# Verify
kubectl get pods -n data -l app=postgresql
kubectl logs -n data -l app=postgresql --tail=50
```

### Redis

```bash
# Deploy Redis
kubectl apply -f apps/database/redis.yaml

# Wait for it to be ready
kubectl wait --for=condition=ready pod -l app=redis -n data --timeout=5m

# Verify
kubectl get pods -n data -l app=redis
```

## Step 3: Deploy Storage (MinIO)

```bash
# Deploy MinIO
kubectl apply -f kubernetes/base/minio-deployment.yaml

# Wait for MinIO
kubectl wait --for=condition=ready pod -l app=minio -n storage --timeout=5m

# Get MinIO password
kubectl get secret minio-credentials -n storage -o jsonpath='{.data.MINIO_ROOT_PASSWORD}' | base64 -d

# Port forward to access console (optional)
kubectl port-forward -n storage svc/minio 9001:9001

# Access: http://localhost:9001
# Username: minioadmin
# Password: (from above command)
```

## Step 4: Deploy Monitoring Stack

### Add Helm Repos

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

### Deploy Prometheus + Grafana

```bash
# Deploy Prometheus Stack
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  -f monitoring/prometheus/values.yaml \
  -n monitoring --create-namespace

# Wait for pods
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus -n monitoring --timeout=10m

# Get Grafana password
kubectl get secret prometheus-grafana -n monitoring -o jsonpath='{.data.admin-password}' | base64 -d

# Port forward to access Grafana (optional)
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# Access: http://localhost:3000
# Username: admin
# Password: (from above command)
```

### Deploy Loki

```bash
helm upgrade --install loki grafana/loki-stack \
  -f monitoring/loki/values.yaml \
  -n monitoring

kubectl wait --for=condition=ready pod -l app=loki -n monitoring --timeout=5m
```

### Apply Alert Rules

```bash
kubectl apply -f monitoring/prometheus/alerts.yaml
```

## Step 5: Deploy Secrets Management (Infisical)

```bash
# Deploy Infisical
kubectl apply -f security/infisical/deployment.yaml

# Wait for Infisical
kubectl wait --for=condition=ready pod -l app=infisical -n infisical --timeout=5m

# Deploy Infisical Operator
kubectl apply -f security/infisical/operator.yaml

# Get Infisical URL (if using ingress)
# Or port forward:
kubectl port-forward -n infisical svc/infisical 8080:80

# Access: http://localhost:8080
# Create account and setup project
```

## Step 6: Configure Secrets

### Option A: Using Infisical (Recommended)

1. Login to Infisical
2. Create project: "devops-agent"
3. Create environment: "production"
4. Add secrets:
   - `ANTHROPIC_API_KEY`: Your Claude API key
   - `SECRET_KEY`: Generate random 32-char string
   - `POSTGRES_PASSWORD`: (from PostgreSQL secret)

### Option B: Manual Kubernetes Secrets (Quick Start)

```bash
# Create backend secrets manually
kubectl create secret generic backend-secrets -n production \
  --from-literal=ANTHROPIC_API_KEY='sk-ant-your-api-key-here' \
  --from-literal=SECRET_KEY='generate-random-32-char-string-here' \
  --from-literal=POSTGRES_PASSWORD='your-postgres-password'

# Verify
kubectl get secret backend-secrets -n production
```

## Step 7: Deploy Applications

### Build Docker Images

#### Backend

```bash
cd apps/backend-python

# Build
docker build -t registry.gitlab.com/yourorg/devops-agent/backend-python:latest \
  -f ../../docker/Dockerfile.python .

# Push
docker push registry.gitlab.com/yourorg/devops-agent/backend-python:latest
```

#### Frontend

```bash
cd apps/frontend

# Build
docker build -t registry.gitlab.com/yourorg/devops-agent/frontend:latest \
  -f ../../docker/Dockerfile.nextjs .

# Push
docker push registry.gitlab.com/yourorg/devops-agent/frontend:latest
```

### Deploy Backend

```bash
# Update image registry in the manifest if needed
# Edit kubernetes/apps/backend-deployment.yaml

# Deploy
kubectl apply -f kubernetes/apps/backend-deployment.yaml

# Wait for backend
kubectl wait --for=condition=ready pod -l app=backend-python -n production --timeout=5m

# Check logs
kubectl logs -n production -l app=backend-python --tail=50

# Test backend health
kubectl port-forward -n production svc/backend-python 8000:80
curl http://localhost:8000/api/health
```

### Deploy Frontend

```bash
# Update API URL in the manifest
# Edit kubernetes/apps/frontend-deployment.yaml
# Set NEXT_PUBLIC_API_URL to your backend URL

# Deploy
kubectl apply -f kubernetes/apps/frontend-deployment.yaml

# Wait for frontend
kubectl wait --for=condition=ready pod -l app=frontend -n production --timeout=5m

# Check logs
kubectl logs -n production -l app=frontend --tail=50
```

## Step 8: Setup Ingress & TLS

### Deploy Nginx Ingress

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --set controller.service.type=LoadBalancer \
  -n ingress-nginx --create-namespace

# Get external IP
kubectl get svc -n ingress-nginx ingress-nginx-controller

# Update your DNS:
# yourdomain.com -> external IP
# api.yourdomain.com -> external IP
```

### Deploy Cert-Manager

```bash
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

### Update Ingress with Your Domain

```bash
# Edit kubernetes/apps/frontend-deployment.yaml
# Replace yourdomain.com with your actual domain

# Apply
kubectl apply -f kubernetes/apps/frontend-deployment.yaml

# Wait for certificate
kubectl get certificate -n production

# Should show "Ready: True" after 1-2 minutes
```

## Step 9: Verify Everything Works

### Check All Pods

```bash
kubectl get pods -A

# All pods should be Running or Completed
```

### Test Application

```bash
# Frontend (if using domain)
curl -I https://yourdomain.com

# Backend API
curl https://api.yourdomain.com/api/health

# Or with port-forward:
kubectl port-forward -n production svc/frontend 3000:80
kubectl port-forward -n production svc/backend-python 8000:80

# Open browser:
# http://localhost:3000 - Frontend
# http://localhost:8000/api/docs - Backend API docs
```

### Test Chat with Claude

1. Open https://yourdomain.com in browser
2. Type a message: "Hello, what can you help me with?"
3. You should get a response from Claude!

If you get an error:
- Check backend logs: `kubectl logs -n production -l app=backend-python`
- Verify Claude API key is set correctly
- Check backend health: `curl https://api.yourdomain.com/api/health/detailed`

## Step 10: Setup GitLab CI/CD (Optional)

### Register GitLab Runner

```bash
helm repo add gitlab https://charts.gitlab.io

helm upgrade --install gitlab-runner gitlab/gitlab-runner \
  --set gitlabUrl=https://gitlab.com \
  --set runnerRegistrationToken=YOUR_TOKEN \
  --set rbac.create=true \
  -n gitlab-runner --create-namespace
```

### Add GitLab CI/CD Variables

In your GitLab project → Settings → CI/CD → Variables, add:

- `KUBE_URL`: Your Kubernetes API URL
- `KUBE_TOKEN`: Service account token
- `CI_REGISTRY_USER`: Docker registry username
- `CI_REGISTRY_PASSWORD`: Docker registry password
- `ANTHROPIC_API_KEY`: Your Claude API key

### Push to GitLab

```bash
git remote add origin https://gitlab.com/yourorg/devops-agent.git
git push -u origin master

# GitLab CI will automatically build and deploy!
```

---

## 🎉 You're Done!

Your application is now live:

- **Frontend**: https://yourdomain.com
- **Backend API**: https://api.yourdomain.com
- **Grafana**: https://grafana.yourdomain.com (admin / <password>)
- **MinIO**: https://minio.yourdomain.com (minioadmin / <password>)

## 🔧 Quick Commands

```bash
# View all resources
kubectl get all -n production

# Restart backend
kubectl rollout restart deployment/backend-python -n production

# Restart frontend
kubectl rollout restart deployment/frontend -n production

# View logs
kubectl logs -f -n production -l app=backend-python
kubectl logs -f -n production -l app=frontend

# Scale up
kubectl scale deployment/backend-python --replicas=5 -n production

# Check health
kubectl exec -it -n production deployment/backend-python -- curl localhost:8000/api/health
```

## 🐛 Troubleshooting

### Backend not starting

```bash
# Check logs
kubectl logs -n production -l app=backend-python --tail=100

# Common issues:
# - Missing ANTHROPIC_API_KEY
# - Database connection failed
# - Redis connection failed

# Check secrets
kubectl get secret backend-secrets -n production -o yaml

# Test database connection
kubectl exec -it -n data postgresql-0 -- psql -U devops -d devops_agent -c "SELECT 1;"
```

### Frontend can't connect to backend

```bash
# Check NEXT_PUBLIC_API_URL is correct
kubectl get deployment frontend -n production -o yaml | grep NEXT_PUBLIC_API_URL

# Update if needed
kubectl set env deployment/frontend -n production \
  NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### Claude API not working

```bash
# Verify API key is set
kubectl exec -it -n production deployment/backend-python -- env | grep ANTHROPIC

# Test Claude API manually
kubectl exec -it -n production deployment/backend-python -- python3 -c "
import anthropic
client = anthropic.Anthropic(api_key='YOUR_KEY')
message = client.messages.create(
    model='claude-3-5-sonnet-20241022',
    max_tokens=100,
    messages=[{'role': 'user', 'content': 'Hello!'}]
)
print(message.content)
"
```

### Monitoring not working

```bash
# Check Prometheus targets
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Open: http://localhost:9090/targets

# Check Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# Open: http://localhost:3000
```

---

## 📚 Next Steps

1. **Setup automated backups**: See `docs/runbooks/backup.md`
2. **Configure alerts**: See `monitoring/prometheus/alerts.yaml`
3. **Add more features**: Extend backend API
4. **Optimize costs**: Review resource limits
5. **Security hardening**: Enable Pod Security Policies

## 🆘 Support

- Check logs: `kubectl logs -n <namespace> <pod-name>`
- Review runbooks: `docs/runbooks/`
- Check health: `/api/health/detailed`
- Monitor in Grafana

---

**Congratulations! Your AI-powered DevOps Agent is live! 🎉**
