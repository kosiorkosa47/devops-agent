# 🤖 ATLAS Agentic Features - Execution Engine

## 🎯 Overview

ATLAS is now a **TRUE AGENTIC SYSTEM** - it doesn't just suggest, it **EXECUTES**!

### What Changed?

**Before (Chat Mode):**
```
User: "Check pod status"
ATLAS: "You can check pod status with: kubectl get pods -n production"
User: *copies and runs command manually*
```

**Now (Agent Mode):**
```
User: "Check pod status"
ATLAS: "I'll check that for you!" 
      *Executes kubectl_get_pods*
      "Here are your pods: ..."
User: *gets results immediately*
```

---

## 🔧 Available Tools (20+ Operations)

### Kubernetes Operations

#### Safe Operations (Auto-executed)
- ✅ `kubectl_get_pods` - List pods in namespace
- ✅ `kubectl_get_pod_logs` - Get pod logs
- ✅ `kubectl_describe_pod` - Detailed pod info
- ✅ `kubectl_get_deployments` - List deployments
- ✅ `kubectl_get_events` - View K8s events
- ✅ `kubectl_top_pods` - Resource usage

#### Dangerous Operations (Require Approval)
- ⚠️ `kubectl_scale_deployment` - Scale replicas
- ⚠️ `kubectl_delete_pod` - Delete pod

### Docker Operations (Coming Soon)
- `docker_ps` - List containers
- `docker_logs` - Container logs
- `docker_inspect` - Container details

### Git Operations (Coming Soon)
- `git_status` - Repository status
- `git_log` - Commit history
- `git_diff` - Show changes

### Monitoring (Coming Soon)
- `prometheus_query` - Execute PromQL
- `check_pod_health` - Health status
- `analyze_error_logs` - Error analysis

---

## 🎬 How It Works

### 1. Tool Execution Flow

```
User Request
    ↓
Claude decides which tool to use
    ↓
Is operation dangerous?
    ├─ NO → Execute immediately
    └─ YES → Request approval
        ↓
    User approves?
        ├─ YES → Execute
        └─ NO → Cancel
    ↓
Return results to Claude
    ↓
Claude provides summary
```

### 2. Approval Workflow

**Safe Operations** (Auto-approved by default):
- Read operations (get, list, describe)
- Log viewing
- Status checks

**Dangerous Operations** (Always require approval):
- Delete operations
- Scale operations
- Apply/Deploy operations
- Any write operation

### 3. Audit Trail

Every execution is logged:
```json
{
  "execution_id": "exec_1234567890",
  "tool": "kubectl_delete_pod",
  "user": "user@domain.com",
  "approved_by": "user@domain.com",
  "status": "success",
  "timestamp": "2025-11-30T14:52:00Z",
  "parameters": {
    "namespace": "production",
    "pod": "backend-xyz"
  }
}
```

---

## 🚀 Usage Examples

### Example 1: Check Pod Status

```
User: "Show me all pods in production namespace"

ATLAS: "I'll check that for you!"
       *Executes: kubectl_get_pods(namespace="production")*
       
       "Here are your production pods:
       
       | Name | Status | Restarts | Age |
       |------|--------|----------|-----|
       | backend-python-abc | Running | 0 | 2d |
       | frontend-xyz | Running | 1 | 1d |
       | redis-123 | Running | 0 | 5d |"
```

### Example 2: Troubleshoot Crash

```
User: "Why is backend-python crashing?"

ATLAS: "Let me investigate!"
       *Executes: kubectl_describe_pod*
       *Executes: kubectl_get_pod_logs*
       *Executes: kubectl_get_events*
       
       "I found the issue! Your backend pod is crashing due to:
       - OOMKilled (out of memory)
       - Memory limit: 512Mi
       - Actual usage: 600Mi
       
       Recommendation: Increase memory limit to 1Gi"
```

### Example 3: Scale Deployment

```
User: "Scale backend to 5 replicas"

ATLAS: "I can do that, but this requires approval."
       
       ⚠️ APPROVAL REQUIRED:
       Tool: kubectl_scale_deployment
       Namespace: production
       Deployment: backend-python
       Current replicas: 3
       New replicas: 5
       
       [Approve] [Reject]

User: *clicks Approve*

ATLAS: "✅ Scaled backend-python to 5 replicas successfully!
       All 5 pods are now running and healthy."
```

---

## ⚙️ Configuration

### Backend (.env)

```bash
# Agent Execution
AGENT_REQUIRE_APPROVAL=true      # Require approval for dangerous ops
AGENT_AUTO_APPROVE_SAFE=true     # Auto-approve safe operations

# Kubernetes
KUBECONFIG=/path/to/kubeconfig   # K8s config (optional, uses in-cluster if available)
```

### Frontend

Toggle between modes:
- **Agent Mode** (🔧) - Full execution capabilities
- **Chat Only Mode** (💬) - Just conversations, no execution

Toggle in-UI:
- **Auto-approve safe operations** - Checkbox in header

---

## 🛡️ Security Features

### 1. Operation Classification
Every tool is classified as:
- **Safe** - Read-only operations
- **Dangerous** - Write/delete operations

### 2. Approval System
- Dangerous operations always require explicit approval
- User sees exactly what will be executed
- Can be disabled per-request

### 3. Audit Logging
- All executions logged to Redis
- 30-day retention
- Includes: user, tool, params, result, timestamp

### 4. Execution Tracking
- Every execution has unique ID
- Can view pending executions
- Can view execution history

### 5. RBAC Integration
- Respects Kubernetes RBAC
- Uses service account permissions
- Cannot execute if not authorized

---

## 📊 API Endpoints

### Agent Chat
```http
POST /api/agent/chat
Content-Type: application/json

{
  "message": "Check pod status",
  "conversation_id": "conv_123",
  "auto_approve_safe": true
}
```

### Approve Execution
```http
POST /api/agent/approve
Content-Type: application/json

{
  "execution_id": "exec_1234567890",
  "approved": true
}
```

### Get Pending Executions
```http
GET /api/agent/executions/pending
```

### Get Execution History
```http
GET /api/agent/executions/history?limit=50
```

### List Available Tools
```http
GET /api/agent/tools
```

---

## 🔌 Adding New Tools

### 1. Define Tool in `app/core/tools.py`

```python
{
    "name": "my_new_tool",
    "description": "Does something useful",
    "input_schema": {
        "type": "object",
        "properties": {
            "param1": {"type": "string"},
            "param2": {"type": "integer"}
        },
        "required": ["param1"]
    }
}
```

### 2. Implement Executor

```python
# app/core/executors/my_executor.py
class MyExecutor:
    async def my_new_tool(self, param1: str, param2: int = 10):
        # Implementation
        return {"result": "success"}
```

### 3. Route in Execution Engine

```python
# app/core/execution_engine.py
async def _route_execution(self, tool_name, parameters):
    if tool_name.startswith("my_"):
        return await self.my_executor.execute(tool_name, parameters)
```

### 4. Test!

```bash
curl -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Use my new tool with param1=test"}'
```

---

## 🎯 Roadmap

### Phase 1: Core (✅ COMPLETE)
- [x] Tool definitions
- [x] Execution engine
- [x] Approval workflow
- [x] Kubernetes executor
- [x] Audit logging
- [x] Frontend UI

### Phase 2: Extended Tools (In Progress)
- [ ] Docker operations
- [ ] Git operations
- [ ] Monitoring queries
- [ ] Helm operations
- [ ] Terraform operations

### Phase 3: Advanced Features
- [ ] Multi-step workflows
- [ ] Scheduled operations
- [ ] Rollback capabilities
- [ ] Cost estimation
- [ ] AI-powered recommendations

### Phase 4: Enterprise Features
- [ ] SSO/OIDC integration
- [ ] Fine-grained RBAC
- [ ] Compliance reporting
- [ ] Multi-cluster support
- [ ] Slack/Teams integration

---

## 💡 Best Practices

### For Users

1. **Start with safe operations** - Get comfortable with the agent
2. **Review approvals carefully** - Always check what will be executed
3. **Use auto-approve for safe ops** - Speeds up workflow
4. **Check execution history** - Monitor what was done
5. **Provide context** - More context = better tool selection

### For Developers

1. **Classify operations correctly** - Safe vs dangerous
2. **Validate inputs** - Check parameters before execution
3. **Handle errors gracefully** - Return useful error messages
4. **Log everything** - Audit trail is critical
5. **Test approval workflow** - Ensure dangerous ops require approval

---

## 🐛 Troubleshooting

### Agent not executing tools

**Check:**
1. Backend is running
2. Kubernetes config is valid
3. Service account has permissions
4. Tool is implemented in executor

**Debug:**
```bash
# Check backend logs
docker logs backend-python

# Test tool directly
curl http://localhost:8000/api/agent/tools
```

### Approval not working

**Check:**
1. Redis is running (stores execution state)
2. Execution ID is correct
3. User has permission to approve

### Kubernetes operations failing

**Check:**
1. KUBECONFIG is set correctly
2. Service account has RBAC permissions
3. Cluster is reachable
4. Namespace exists

---

## 📚 Additional Resources

- [MCP Research](./MCP_RESEARCH.md) - MCP servers integration
- [Deployment Guide](./DEPLOYMENT_GUIDE.md) - How to deploy
- [API Documentation](http://localhost:8000/api/docs) - Interactive API docs

---

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Last Updated:** 2025-11-30

**Now you have a TRUE AI DevOps Engineer that can execute operations for you!** 🚀
