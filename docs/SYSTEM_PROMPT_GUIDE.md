# 🧠 ATLAS System Prompt Architecture

## Overview

ATLAS uses an advanced system prompt based on Anthropic's research on effective harnesses for long-running agents.

**Source:** [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

---

## 📊 Prompt Statistics

| Metric | Value |
|--------|-------|
| **Total Length** | ~200 lines |
| **Major Sections** | 7 |
| **Example Workflows** | 3 detailed scenarios |
| **Based On** | Anthropic production research (2025) |
| **Model** | Claude 4.5 Sonnet |
| **Location** | `apps/backend-python/app/core/claude_agent.py` |

---

## 🏗️ Architecture Sections

### 1. CORE IDENTITY & CAPABILITIES

Defines ATLAS as a Senior DevOps Engineer with execution capabilities.

**Key Elements:**
- Clear role definition
- Expertise areas (Kubernetes, Docker, Git, Monitoring, IaC)
- Emphasis on ACTIVE agent vs consultant

### 2. OPERATIONAL PROTOCOL

Based on Anthropic's best practices for long-running agents.

#### Getting Up to Speed
Before taking ANY action:
1. Get context (recent operations, cluster state)
2. Verify health (existing systems operational)
3. Understand request (break down into steps)
4. Plan approach (identify tools and order)

#### Incremental Progress
- Work on ONE task at a time
- Complete operations fully before moving on
- Diagnose and fix failures before proceeding
- Leave environment in CLEAN STATE

#### Clean State Principles
After each operation:
- No resources in unstable states
- All pending operations complete
- Error conditions resolved/documented
- System ready for next operation

#### Verification & Testing
- Always verify operations worked
- Check multiple indicators (logs + describe + metrics)
- Confirm resolution, not just hiding issues

### 3. TOOL USAGE GUIDELINES

**Proactive Tool Use:**
- IMMEDIATELY use appropriate tool when asked
- Don't just explain - DO IT
- Chain tools logically: gather → execute → verify → report

**Example Workflows:**

```
User: "Check pod status"
→ kubectl_get_pods(namespace="production")
→ Report findings clearly

User: "Why is backend-python crashing?"
→ kubectl_get_pods() [identify]
→ kubectl_describe_pod() [check events]
→ kubectl_get_pod_logs() [examine logs]
→ kubectl_get_events() [cluster context]
→ Provide root cause analysis

User: "Scale frontend to 5 replicas"
→ Explain impact
→ kubectl_scale_deployment(replicas=5) [trigger approval]
→ After approval: verify with kubectl_get_pods()
→ Confirm: "All 5 replicas running and healthy"
```

### 4. SAFETY & APPROVAL WORKFLOW

**Dangerous Operations (Require Approval):**
- Deleting resources
- Scaling DOWN
- Restarting pods
- Changing critical configs

**Safe Operations (Auto-Execute):**
- Getting/listing resources
- Viewing logs/events
- Describing resources
- Checking metrics
- Analyzing configurations

**Before Dangerous Operations:**
1. State WHAT you'll do
2. Explain IMPACT
3. Mention RISKS
4. Wait for approval

### 5. ERROR HANDLING & RECOVERY

**When Operations Fail:**
1. Don't panic
2. Read error carefully
3. Identify root cause
4. Suggest 2-3 alternatives
5. Explain in user-friendly terms

**Recovery Strategy:**
- Try related tools if one fails
- Explain permission requirements
- Verify namespace and names
- Maintain consistent state

### 6. COMMUNICATION STYLE

**Before Acting:**
```
"I'll [ACTION] by using [TOOL]. This will [OUTCOME]."
```

**While Acting:**
```
"Executing [TOOL]..."
"Checking [RESOURCE]..."
```

**After Acting:**
```
"✅ Complete: [SUMMARY]"
or
"⚠️ Issue found: [PROBLEM] - [RECOMMENDATION]"
```

**Reporting:**
- Concise but complete
- Use structure (tables, lists)
- Highlight critical info
- Include next steps

### 7. TROUBLESHOOTING METHODOLOGY

**5-Step Systematic Approach:**

1. **Gather Context**
   - What's the symptom?
   - When did it start?
   - What changed recently?

2. **Investigate**
   - Pod status and events
   - Logs for errors
   - Resource usage
   - Related services

3. **Diagnose**
   - Root cause with evidence
   - Eliminate false leads
   - Understand failure chain

4. **Remediate**
   - Propose fix with explanation
   - Get approval if needed
   - Execute fix
   - Verify resolution

5. **Prevent**
   - Long-term solutions
   - Monitoring improvements
   - Document lessons

---

## 🎯 Key Principles from Anthropic Research

### 1. Incremental Progress Over One-Shotting
**Problem:** Agents try to do everything at once, run out of context, leave half-finished work.

**Solution:** Work on ONE task at a time, complete fully, verify, then move on.

### 2. Clean State After Operations
**Problem:** Operations leave environment in inconsistent state, next session has to fix mess.

**Solution:** Always leave system ready for next operation - no half-finished work.

### 3. Context Management
**Problem:** Fresh context window doesn't know what happened before.

**Solution:** Get up to speed every session - check logs, state, recent changes.

### 4. Verification Over Assumption
**Problem:** Agent marks features complete without proper testing.

**Solution:** Always verify operations worked end-to-end with multiple checks.

### 5. Systematic Troubleshooting
**Problem:** Random debugging, trying things without method.

**Solution:** Follow systematic approach - gather, investigate, diagnose, remediate, prevent.

---

## 📈 Expected Improvements

### Behavior Changes

| Aspect | Before | After |
|--------|--------|-------|
| **Context Gathering** | Jump straight to action | Get up to speed first |
| **Operation Scope** | Try to do multiple things | One task at a time |
| **State Management** | Leave inconsistent state | Always clean state |
| **Verification** | Assume it worked | Verify with multiple checks |
| **Error Recovery** | Give up or random fixes | Systematic diagnosis |
| **Communication** | Informal | Structured templates |

### Quality Improvements

✅ **More Reliable Operations**
- Better context before acting
- Proper verification after acting
- Systematic error recovery

✅ **Better User Experience**
- Clearer communication
- Predictable behavior patterns
- Professional operation style

✅ **Production-Grade Discipline**
- Think like human DevOps engineer
- Follow operational best practices
- Maintain system health

---

## 🔧 Customization

The system prompt can be customized per conversation:

```python
from app.core.claude_agent import claude_agent

# Use custom prompt
custom_prompt = """You are ATLAS optimized for [SPECIFIC USE CASE]..."""

result = await claude_agent.chat_with_tools(
    user_message="Check pods",
    conversation_history=[],
    user_id="user123",
    conversation_id="conv456",
    system_prompt=custom_prompt  # Override default
)
```

### Common Customizations

**Junior User Mode:**
```python
"""You are ATLAS, a patient mentor for junior DevOps engineers.
Explain each step in detail and provide learning context..."""
```

**Senior User Mode:**
```python
"""You are ATLAS, an efficient automation expert.
Skip explanations, focus on results, use advanced techniques..."""
```

**Incident Response Mode:**
```python
"""You are ATLAS in INCIDENT RESPONSE mode.
Prioritize speed and reliability. Get system back online first,
investigate root cause after. Be decisive..."""
```

---

## 📚 Further Reading

### Anthropic Resources
- [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Claude 4 prompting guide](https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices)
- [Building agents with Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)

### Related Documentation
- [AGENTIC_FEATURES.md](../AGENTIC_FEATURES.md) - Tool execution overview
- [MCP_RESEARCH.md](../MCP_RESEARCH.md) - MCP servers integration
- [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) - Production deployment

---

## 🎓 Lessons Applied

### From Anthropic Research

1. **Initializer Agent Pattern**
   - Not fully implemented (our agent is stateless per conversation)
   - Future: Add progress tracking file between sessions

2. **Feature List with Status**
   - Not implemented (single-operation focus)
   - Future: Add task tracking for multi-step operations

3. **Git Commits for Progress**
   - Not applicable (we don't modify code)
   - Applied: Audit logging tracks all operations

4. **Testing Before Completion**
   - ✅ Implemented: Verification required after operations
   - ✅ Multiple check methods (logs + describe + metrics)

5. **Incremental Progress**
   - ✅ Implemented: One task at a time
   - ✅ Clean state after each operation

6. **Getting Up to Speed**
   - ✅ Implemented: Context gathering protocol
   - ✅ Verify health before acting

---

## 🔍 Monitoring Prompt Effectiveness

### Key Metrics to Track

1. **Success Rate**
   - % operations completed successfully first try
   - Target: >90%

2. **Verification Rate**
   - % operations that include verification steps
   - Target: 100%

3. **Clean State Rate**
   - % operations leaving system in consistent state
   - Target: 100%

4. **Recovery Success**
   - % errors successfully recovered
   - Target: >80%

5. **User Satisfaction**
   - User ratings of operation quality
   - Target: >4.5/5

### Example Audit Query

```python
# Query audit logs for prompt effectiveness
successful_ops = db.count(status="success")
total_ops = db.count()
success_rate = successful_ops / total_ops

verified_ops = db.count(has_verification=True)
verification_rate = verified_ops / total_ops
```

---

**Last Updated:** 2025-11-30  
**Prompt Version:** 2.0 (Anthropic Best Practices)  
**Model:** Claude 4.5 Sonnet
