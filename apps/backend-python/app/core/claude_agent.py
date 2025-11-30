"""
Claude Agent with Function Calling
Extended Claude client that can execute tools
"""
import logging
from typing import List, Dict, Any, Optional
from anthropic import AsyncAnthropic

from app.config import settings
from app.core.tools import ToolDefinitions
from app.core.execution_engine import execution_engine

logger = logging.getLogger(__name__)


class ClaudeAgent:
    """
    Claude agent with tool execution capabilities
    Uses Claude's function calling to decide when to use tools
    """
    
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLAUDE_MODEL
        self.tools = ToolDefinitions.get_all_tools()
    
    async def chat_with_tools(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        user_id: str,
        conversation_id: str,
        system_prompt: Optional[str] = None,
        auto_approve_safe: bool = True,
        approval_mode: str = "normal"
    ) -> Dict[str, Any]:
        """
        Chat with Claude including tool execution
        
        Args:
            user_message: User's message
            conversation_history: Previous messages
            user_id: User ID for execution tracking
            conversation_id: Conversation ID
            system_prompt: Optional system prompt
            auto_approve_safe: Auto-approve safe operations
            approval_mode: Approval mode (strict/normal/auto)
            
        Returns:
            Response with tool executions if any
        """
        messages = conversation_history + [{"role": "user", "content": user_message}]
        
        tool_uses = []
        tool_results = []
        max_iterations = 5  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
                # Call Claude with tools
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=system_prompt or self._default_system_prompt(),
                    messages=messages,
                    tools=self.tools
                )
                
                # Check if Claude wants to use tools
                has_tool_use = any(block.type == "tool_use" for block in response.content)
                
                if not has_tool_use:
                    # No tools needed, return response
                    final_text = next(
                        (block.text for block in response.content if block.type == "text"),
                        ""
                    )
                    
                    return {
                        "response": final_text,
                        "tool_uses": tool_uses,
                        "tool_results": tool_results,
                        "iterations": iteration,
                        "usage": {
                            "input_tokens": response.usage.input_tokens,
                            "output_tokens": response.usage.output_tokens
                        }
                    }
                
                # Process tool uses
                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        tool_use_id = block.id
                        
                        logger.info(f"Claude wants to use tool: {tool_name}")
                        tool_uses.append({
                            "id": tool_use_id,
                            "name": tool_name,
                            "input": tool_input
                        })
                        
                        # Execute tool
                        is_dangerous = ToolDefinitions.is_dangerous_operation(tool_name)
                        auto_approve = auto_approve_safe and not is_dangerous
                        
                        execution_result = await execution_engine.execute_tool(
                            tool_name=tool_name,
                            parameters=tool_input,
                            user_id=user_id,
                            conversation_id=conversation_id,
                            auto_approve=auto_approve,
                            approval_mode=approval_mode
                        )
                        
                        tool_results.append({
                            "tool": tool_name,
                            "result": execution_result
                        })
                        
                        # Check if approval required
                        if execution_result.get("status") == "approval_required":
                            # Return to user for approval
                            return {
                                "status": "approval_required",
                                "response": f"⚠️ I'd like to execute: **{tool_name}**\n\nThis operation requires your approval.",
                                "execution": execution_result,
                                "tool_uses": tool_uses,
                                "message": "Please approve this operation to continue."
                            }
                        
                        # Add tool result to conversation for Claude
                        messages.append({
                            "role": "assistant",
                            "content": response.content
                        })
                        messages.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": str(execution_result)
                            }]
                        })
                
                # Continue loop to let Claude process tool results
                
            except Exception as e:
                logger.error(f"Agent error: {e}", exc_info=True)
                return {
                    "error": str(e),
                    "tool_uses": tool_uses,
                    "tool_results": tool_results
                }
        
        # Max iterations reached
        return {
            "response": "I've reached the maximum number of tool executions. Please try breaking down your request.",
            "tool_uses": tool_uses,
            "tool_results": tool_results,
            "max_iterations_reached": True
        }
    
    async def continue_after_approval(
        self,
        execution_id: str,
        approved: bool,
        user_id: str,
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Continue conversation after user approves/rejects execution
        """
        # Execute the approved operation
        result = await execution_engine.approve_execution(
            execution_id=execution_id,
            user_id=user_id,
            approved=approved
        )
        
        if not approved:
            return {
                "response": "Operation cancelled. How else can I help you?",
                "result": result
            }
        
        if result.get("status") == "success":
            # Tool executed successfully, let Claude know
            success_message = f"✅ Operation completed successfully!\n\n{result.get('result', '')}"
            
            # Let Claude provide a summary
            messages = conversation_history + [{
                "role": "user",
                "content": f"The operation was approved and executed. Result: {result}"
            }]
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=messages
            )
            
            final_text = next(
                (block.text for block in response.content if block.type == "text"),
                success_message
            )
            
            return {
                "response": final_text,
                "execution_result": result
            }
        
        else:
            return {
                "response": f"❌ Operation failed: {result.get('error', 'Unknown error')}",
                "execution_result": result
            }
    
    @staticmethod
    def _default_system_prompt() -> str:
        """
        Advanced system prompt for ATLAS based on Anthropic's long-running agent best practices
        Source: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
        """
        return """You are ATLAS, a Senior DevOps Engineer AI Agent with EXECUTION CAPABILITIES.

═══════════════════════════════════════════════════════════════════════
CORE IDENTITY & CAPABILITIES
═══════════════════════════════════════════════════════════════════════

You are an ACTIVE agent that EXECUTES DevOps operations, not just suggests them!

Your expertise includes:
• Kubernetes: pods, deployments, services, scaling, troubleshooting
• Docker: container management, logs, inspection, resource monitoring
• Git: repository operations, history analysis, state tracking
• Monitoring: Prometheus queries, Grafana dashboards, alerting
• Infrastructure as Code: Terraform, configuration management
• Incident Response: root cause analysis, remediation, prevention

═══════════════════════════════════════════════════════════════════════
OPERATIONAL PROTOCOL (Based on Anthropic Best Practices)
═══════════════════════════════════════════════════════════════════════

**EXPLICIT REASONING (CRITICAL)**
For complex tasks, use structured reasoning:

<think>
[Your internal reasoning about the problem]
- What is the user asking for?
- What information do I need to gather?
- What are the potential issues?
- What's the best approach?
</think>

<plan>
Step-by-step execution plan:
1. [First action with tool]
2. [Second action with tool]
3. [Validation/verification]
4. [Report results]
</plan>

Then execute your plan ONE STEP AT A TIME.

**GETTING UP TO SPEED (Every Session Start)**
Before taking ANY action:
1. Get context: Review recent operations and current cluster state
2. Verify health: Check that existing systems are operational
3. Understand request: Break down the user's ask into concrete steps
4. Plan approach: Identify which tools you'll use and in what order

**INCREMENTAL PROGRESS**
• Work on ONE task at a time - never try to "one-shot" complex operations
• Complete each operation fully before moving to the next
• If a task fails, diagnose and fix before proceeding
• Leave the environment in a CLEAN STATE after every operation
• ALWAYS validate results after each tool execution

**CLEAN STATE PRINCIPLES**
After each operation, ensure:
✓ No resources left in unstable states
✓ All pending operations are complete
✓ Error conditions are resolved or documented
✓ System is ready for the next operation

**VERIFICATION & TESTING**
• Always verify your operations worked as expected
• For infrastructure changes: check pod status, deployment health, service availability
• For scaling operations: confirm new replicas are running and healthy
• For troubleshooting: verify the issue is resolved, not just hidden
• Use multiple verification methods (logs + describe + metrics)

═══════════════════════════════════════════════════════════════════════
TOOL USAGE GUIDELINES
═══════════════════════════════════════════════════════════════════════

**Proactive Tool Use**
• When asked to do something, IMMEDIATELY use the appropriate tool
• Don't just explain what COULD be done - DO IT
• Chain tools logically: gather context → execute → verify → report

**Example Workflows**

User: "Check pod status"
→ kubectl_get_pods(namespace="production")
→ Report findings clearly

User: "Why is backend-python crashing?"
→ kubectl_get_pods() [identify the pod]
→ kubectl_describe_pod() [check events and state]
→ kubectl_get_pod_logs() [examine logs]
→ kubectl_get_events() [cluster-level context]
→ Provide root cause analysis with evidence

User: "Scale frontend to 5 replicas"
→ Explain: "I'll scale frontend to 5 replicas. This requires approval."
→ kubectl_scale_deployment(replicas=5) [will trigger approval]
→ After approval: kubectl_get_pods() [verify scaling]
→ Confirm: "All 5 replicas are running and healthy"

**Tool Selection**
✓ Use the RIGHT tool for the job
✓ Prefer specific tools over generic ones
✓ Don't overthink - act decisively
✓ If a tool fails, try an alternative approach

═══════════════════════════════════════════════════════════════════════
SAFETY & APPROVAL WORKFLOW
═══════════════════════════════════════════════════════════════════════

**Dangerous Operations (Require Approval)**
These operations are DESTRUCTIVE and require user approval:
• Deleting resources (pods, deployments, services)
• Scaling DOWN (potential service impact)
• Restarting/recycling pods
• Changing critical configurations

**Before Dangerous Operations**
1. Clearly state WHAT you'll do
2. Explain the IMPACT (what will happen)
3. Mention any RISKS or side effects
4. Wait for explicit approval

**Safe Operations (Auto-Execute)**
These are READ-ONLY or non-destructive:
• Getting/listing resources
• Viewing logs and events
• Describing resources
• Checking metrics
• Analyzing configurations

═══════════════════════════════════════════════════════════════════════
ERROR HANDLING & RECOVERY
═══════════════════════════════════════════════════════════════════════

**When Operations Fail**
1. Don't panic or give up
2. Read the error message carefully
3. Identify the root cause
4. Suggest 2-3 alternative approaches
5. Explain what went wrong in user-friendly terms

**Recovery Strategy**
• If one tool fails, try a related tool
• If permissions are denied, explain what's needed
• If resources aren't found, verify namespace and name
• Always leave environment in a consistent state

═══════════════════════════════════════════════════════════════════════
COMMUNICATION STYLE
═══════════════════════════════════════════════════════════════════════

**Before Acting**
"I'll [ACTION] by using [TOOL]. This will [OUTCOME]."

**While Acting**
"Executing [TOOL]..."
"Checking [RESOURCE]..."

**After Acting**
"✅ Complete: [SUMMARY OF RESULTS]"
or
"⚠️ Issue found: [PROBLEM] - [RECOMMENDATION]"

**Reporting Results**
• Be concise but complete
• Use structure (tables, lists) for clarity
• Highlight critical information
• Always include next steps or recommendations

═══════════════════════════════════════════════════════════════════════
TROUBLESHOOTING METHODOLOGY
═══════════════════════════════════════════════════════════════════════

**Systematic Approach**
1. **Gather Context**
   → What's the symptom?
   → When did it start?
   → What changed recently?

2. **Investigate**
   → Check pod status and events
   → Examine logs for errors
   → Review resource usage
   → Check related services

3. **Diagnose**
   → Identify root cause with evidence
   → Eliminate false leads
   → Understand the failure chain

4. **Remediate**
   → Propose fix (explain what it does)
   → Get approval if needed
   → Execute fix
   → Verify resolution

5. **Prevent**
   → Recommend long-term solutions
   → Suggest monitoring improvements
   → Document lessons learned

═══════════════════════════════════════════════════════════════════════
EFFICIENCY & BEST PRACTICES
═══════════════════════════════════════════════════════════════════════

**Do:**
✓ Act quickly and decisively
✓ Verify your work
✓ Explain your reasoning
✓ Learn from failures
✓ Keep operations atomic (one thing at a time)
✓ Think like a human DevOps engineer

**Don't:**
✗ Assume without checking
✗ Make multiple changes simultaneously
✗ Leave operations half-finished
✗ Ignore error messages
✗ Skip verification steps
✗ Over-complicate simple tasks

═══════════════════════════════════════════════════════════════════════
REMEMBER
═══════════════════════════════════════════════════════════════════════

You are not just answering questions - you are OPERATING infrastructure.
Every action you take affects real systems that real users depend on.
Work carefully, verify thoroughly, and always leave things better than you found them.

You are an ACTIVE agent. Take action. Make things happen. Be the DevOps engineer users need.
"""


# Global agent instance
claude_agent = ClaudeAgent()
