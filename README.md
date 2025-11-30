# 🤖 DevOps Agent - Self-Hosted AI Platform

> **ATLAS** - Enterprise-grade DevOps infrastructure for AI-powered applications

[![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=flat&logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![GitLab CI](https://img.shields.io/badge/GitLab_CI-FC6D26?style=flat&logo=gitlab&logoColor=white)](https://gitlab.com/)
[![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=flat&logo=prometheus&logoColor=white)](https://prometheus.io/)
[![Security](https://img.shields.io/badge/Security-Enterprise-green)](https://github.com/)

## 🎯 Project Overview

Self-hosted, production-ready DevOps infrastructure for AI-powered platform with:
- **99.9% SLA** target
- **Enterprise security** best practices
- **Full observability** stack
- **GitOps** workflows
- **Self-healing** capabilities

## 🏗️ Architecture

### Tech Stack
- **Frontend**: Next.js (React)
- **CMS**: Payload CMS (headless)
- **Backend**: Python (FastAPI) + Rust (Actix)
- **Database**: PostgreSQL (HA)
- **Cache**: Redis Cluster
- **Queue**: RabbitMQ
- **Storage**: MinIO (S3-compatible)

### Infrastructure
- **Orchestration**: Self-hosted Kubernetes
- **CI/CD**: GitLab CI/CD
- **Monitoring**: Prometheus + Grafana + Loki + Thanos
- **Secrets**: Infisical (self-hosted)
- **On-Call**: Grafana OnCall
- **Security**: Trivy, GitLeaks, Checkov, Pod Security Standards

## 📁 Repository Structure

```
devops-agent/
├── terraform/              # Infrastructure as Code
│   ├── modules/           # Reusable Terraform modules
│   └── environments/      # Environment-specific configs
├── kubernetes/            # Kubernetes manifests
│   ├── base/             # Base configurations
│   ├── overlays/         # Kustomize overlays per env
│   └── helm-charts/      # Custom Helm charts
├── monitoring/           # Observability stack
│   ├── prometheus/       # Prometheus config & rules
│   ├── grafana/         # Dashboards & alerts
│   ├── loki/            # Log aggregation
│   └── thanos/          # Long-term metrics storage
├── security/            # Security tooling
│   ├── trivy/          # Container scanning
│   ├── policies/       # Security policies
│   └── infisical/      # Secrets management
├── ci-cd/              # CI/CD pipelines
│   ├── pipelines/      # GitLab CI configs
│   └── templates/      # Reusable pipeline templates
├── scripts/            # Automation scripts
│   ├── backup/         # Backup automation
│   ├── maintenance/    # Maintenance tasks
│   └── deployment/     # Deployment helpers
├── docs/               # Documentation
│   ├── runbooks/       # Operational runbooks
│   ├── architecture/   # Architecture docs
│   └── onboarding/     # Developer onboarding
├── docker/             # Dockerfiles
├── ansible/            # Configuration management
├── atlas-progress.txt  # Progress tracking
└── devops-tasks.json   # Task management
```

## 🚀 Quick Start

### Prerequisites
- Kubernetes cluster (v1.28+)
- GitLab (self-hosted or GitLab.com)
- `kubectl` configured
- `helm` (v3.12+)
- `terraform` (v1.6+)

### Initial Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd devops-agent

# 2. Check progress
cat atlas-progress.txt

# 3. View tasks
cat devops-tasks.json | jq '.sprints[0].tasks'

# 4. Initialize Terraform
cd terraform/environments/dev
terraform init

# 5. Deploy base infrastructure
terraform plan
terraform apply

# 6. Setup Kubernetes base
kubectl apply -k kubernetes/base

# 7. Deploy monitoring stack
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  -f monitoring/prometheus/values.yaml

# 8. Deploy Infisical
kubectl apply -f security/infisical/
```

## 📊 Monitoring & Observability

### Access Dashboards
- **Grafana**: https://grafana.yourdomain.com
- **Prometheus**: https://prometheus.yourdomain.com
- **Infisical**: https://secrets.yourdomain.com

### Key Metrics
- **Availability**: 99.9% target
- **Latency**: P95 < 200ms, P99 < 500ms
- **Error Rate**: < 0.1%
- **Resource Usage**: CPU < 70%, Memory < 80%

## 🔐 Security

### Implemented Controls
✅ Pod Security Standards (restricted level)
✅ RBAC with least privilege
✅ Network Policies (default deny)
✅ Container image scanning (Trivy)
✅ Secrets management (Infisical)
✅ TLS everywhere
✅ Security scanning in CI/CD
✅ Audit logging

### Compliance
- GDPR considerations
- Security best practices (CIS Kubernetes Benchmark)
- Regular security audits

## 🛠️ Operations

### Deployment
```bash
# Deploy to dev
gitlab-ci-multi-runner exec docker deploy-dev

# Deploy to staging
gitlab-ci-multi-runner exec docker deploy-staging

# Deploy to production (requires approval)
# Use GitLab UI for production deployments
```

### Rollback
```bash
# Quick rollback
kubectl rollout undo deployment/<app-name> -n production

# Or use GitLab CI rollback job
```

### Monitoring
```bash
# Check cluster health
kubectl get pods -A
kubectl top nodes
kubectl top pods -A

# Check recent alerts
curl http://alertmanager:9093/api/v1/alerts
```

## 📚 Documentation

- [Architecture Overview](docs/architecture/overview.md)
- [Deployment Runbook](docs/runbooks/deployment.md)
- [Incident Response](docs/runbooks/incident-response.md)
- [Developer Onboarding](docs/onboarding/getting-started.md)

## 🎯 Current Sprint

**Sprint 1: Core Infrastructure Foundation**
- [ ] Terraform base setup
- [ ] Kubernetes base configuration
- [ ] GitLab CI pipeline
- [ ] MinIO S3 setup

See [devops-tasks.json](devops-tasks.json) for full roadmap.

## 📈 Progress

Track progress in [atlas-progress.txt](atlas-progress.txt)

## 🤝 Contributing

This is a single-user project, but best practices are followed:
1. All changes via GitLab CI
2. Infrastructure changes via Terraform
3. Security scanning on all commits
4. Full test coverage

## 📝 License

Private project - All rights reserved

## 🆘 Support

For issues or questions:
- Check [runbooks](docs/runbooks/)
- Review logs in Grafana
- Check Grafana OnCall for incidents

---

**Built with ❤️ by ATLAS DevOps Agent**
