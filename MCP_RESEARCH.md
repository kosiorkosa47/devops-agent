# 🔍 MCP Research - DevOps Agent

## Model Context Protocol (MCP) Overview

MCP to otwarty standard od Anthropic do łączenia AI z zewnętrznymi narzędziami i danymi.

## 🎯 Wybrane MCP Servers dla DevOps Agent

### 1. **Kubernetes Management** ⭐ PRIORYTET

**Wybrano:** `containers/kubernetes-mcp-server` (Go-based, oficjalny)

**Dlaczego:**
- ✅ Native Go implementation (najszybszy)
- ✅ NIE wrapper na kubectl - bezpośredni dostęp do K8s API
- ✅ Brak external dependencies
- ✅ Multi-cluster support
- ✅ Cross-platform (Linux, macOS, Windows)
- ✅ Helm support wbudowany

**Możliwości:**
- Get/List/Create/Update/Delete dowolnego resource
- Pod operations (logs, exec, run, top)
- Namespaces & Projects
- Events viewing
- Helm charts (install, list, uninstall)
- Node stats & logs

**Instalacja:**
```bash
npm install @manusa/kubernetes-mcp-server
# lub
pip install kubernetes-mcp-server
# lub native binary
```

**Repo:** https://github.com/containers/kubernetes-mcp-server

---

### 2. **Terraform / IaC**

**Opcje:**
1. `pulumi/mcp-server` - oficjalny Pulumi MCP (🎖️)
2. `westonplatter/mcp-terraform-python` - Python Terraform MCP
3. `stakpak/mcp` - Rust, multi-tool (Terraform, K8s, GH Actions, Dockerfile)

**Wybrano:** Multiple approach
- Pulumi MCP dla nowoczesnego IaC
- stakpak/mcp dla edycji kodu Terraform

---

### 3. **Git / Version Control**

**Opcje:**
- `github` - Oficjalny GitHub MCP
- `gitlab` - GitLab operations
- `git` - Local git operations

**Wybrano:** Wszystkie 3 (różne use cases)

---

### 4. **CI/CD**

**Opcje:**
- `microsoft/azure-devops-mcp` - Azure DevOps (🎖️)
- `gitlab-ci` - GitLab CI operations

**Wybrano:** GitLab CI MCP (dopasowane do naszego stack'u)

---

### 5. **Docker / Containers**

**Opcje:**
- `docker` - Docker operations
- `portainer/portainer-mcp` - Portainer integration (🎖️)

**Wybrano:** Docker MCP bezpośrednio

---

### 6. **Monitoring & Observability**

**Opcje:**
- `prometheus-mcp` - Prometheus queries
- `grafana-mcp` - Grafana dashboards

**Wybrano:** Oba (mamy już Prometheus + Grafana)

---

### 7. **Security & Secrets**

**Opcje:**
- `vault-mcp` - HashiCorp Vault
- `aws-secrets-manager` - AWS Secrets

**Wybrano:** Custom integration z Infisical (już mamy)

---

## 🏗️ Architektura Implementacji

### Backend (Python)

```python
# MCP Client Manager
app/core/mcp/
├── __init__.py
├── client.py           # MCP client base
├── kubernetes.py       # K8s operations
├── terraform.py        # Terraform operations
├── git.py             # Git operations
├── docker.py          # Docker operations
└── monitoring.py      # Prometheus/Grafana
```

### Claude Integration

```python
# Claude z function calling
tools = [
    {
        "name": "kubectl_get_pods",
        "description": "Get list of pods in namespace",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"},
                "context": {"type": "string"}
            }
        }
    },
    # ... more tools
]
```

### Approval System

```python
# Execution approval workflow
1. Claude suggests action
2. Backend validates
3. If safe → auto-execute
4. If dangerous → ask for approval
5. User approves → execute
6. Log everything
```

---

## 🔧 MCP Servers Configuration

### kubernetes-mcp-server

```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "npx",
      "args": [
        "@manusa/kubernetes-mcp-server"
      ],
      "env": {
        "KUBECONFIG": "/path/to/kubeconfig",
        "READ_ONLY": "false"
      }
    }
  }
}
```

### Pulumi MCP

```json
{
  "mcpServers": {
    "pulumi": {
      "command": "npx",
      "args": [
        "@pulumi/mcp-server"
      ],
      "env": {
        "PULUMI_ACCESS_TOKEN": "your-token"
      }
    }
  }
}
```

---

## 🎯 Implementacja - Fazy

### Faza 1: Core MCP Integration (TERAZ)
- ✅ MCP client w Python
- ✅ Kubernetes MCP server integration
- ✅ Claude function calling
- ✅ Basic execution engine

### Faza 2: Safety & Approval
- Approval system z UI
- Dangerous operations detection
- Toggle dla auto-execution
- Audit logging

### Faza 3: Extended Tools
- Terraform MCP
- Git operations
- Docker commands
- Monitoring queries

### Faza 4: Advanced Features
- Multi-step workflows
- Rollback capabilities
- Scheduled operations
- Cost estimation

---

## 🛡️ Security Considerations

### Safe Operations (Auto-execute)
- `kubectl get`
- `kubectl describe`
- `kubectl logs`
- `helm list`
- Git clone/pull
- Read-only operations

### Dangerous Operations (Approval required)
- `kubectl delete`
- `kubectl apply`
- `helm install/uninstall`
- Terraform apply/destroy
- Git push
- Any write operation

### Audit Log
```json
{
  "timestamp": "2025-11-30T14:50:00Z",
  "user": "user@domain.com",
  "operation": "kubectl_delete_pod",
  "parameters": {
    "namespace": "production",
    "pod": "backend-xyz"
  },
  "approved_by": "user@domain.com",
  "status": "success",
  "output": "pod deleted"
}
```

---

## 📦 Dependencies to Add

```toml
[tool.poetry.dependencies]
mcp = "^1.0.0"  # MCP SDK
kubernetes = "^28.1.0"  # K8s client
```

```json
// package.json for MCP servers
{
  "dependencies": {
    "@manusa/kubernetes-mcp-server": "latest",
    "@pulumi/mcp-server": "latest"
  }
}
```

---

## 🚀 Expected Capabilities

Po implementacji agent będzie mógł:

### Kubernetes
- ✅ List/Get/Create/Update/Delete resources
- ✅ Pod logs i exec
- ✅ Deploy applications
- ✅ Scale deployments
- ✅ Helm operations
- ✅ Resource usage monitoring

### Infrastructure
- ✅ Terraform plan/apply
- ✅ Infrastructure changes
- ✅ State management

### CI/CD
- ✅ Trigger pipelines
- ✅ Check build status
- ✅ Deploy to environments

### Git
- ✅ Clone repositories
- ✅ Create branches
- ✅ Commit changes
- ✅ Create PRs

### Monitoring
- ✅ Query Prometheus metrics
- ✅ Check Grafana dashboards
- ✅ Analyze logs
- ✅ Detect anomalies

---

## 🎨 User Experience

```
User: "Deploy backend to staging"

Agent: 
📋 Plan:
1. Check current deployment status
2. Build new Docker image
3. Push to registry
4. Update K8s deployment
5. Wait for rollout
6. Verify health checks

⚠️ This will modify staging environment.
Approve? [Yes] [No]

[User clicks Yes]

Agent:
✅ 1/5 Checking deployment... OK
✅ 2/5 Building image... OK
✅ 3/5 Pushing to registry... OK
⚠️ 4/5 Updating deployment... REQUIRES APPROVAL
    Will update: staging/backend-python
    New image: registry/backend:abc123
    
[User clicks Approve]

✅ 4/5 Deployment updated
✅ 5/5 Health checks passed
🎉 Deployment completed successfully!
```

---

**Status:** Research completed ✅  
**Next:** Implementation rozpoczęta
