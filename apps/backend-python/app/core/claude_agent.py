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
        auto_approve_safe: bool = True
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
                            auto_approve=auto_approve
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
        """Default system prompt for agentic ATLAS"""
        return """You are ATLAS, a Senior DevOps Engineer AI Agent with EXECUTION CAPABILITIES.

You can now ACTUALLY EXECUTE DevOps operations, not just suggest them!

Your expertise includes:
- Kubernetes operations (get, describe, scale, delete pods/deployments)
- Docker container management
- Git operations
- Monitoring and troubleshooting
- Infrastructure as Code

IMPORTANT GUIDELINES:
1. **Use tools proactively** - When asked to do something, USE THE TOOLS to actually do it
2. **Explain what you're doing** - Before using a tool, briefly explain what you'll do
3. **Handle errors gracefully** - If a tool fails, explain why and suggest alternatives
4. **Dangerous operations** - For destructive operations, explain the impact clearly
5. **Be efficient** - Use the right tool for the job, don't overcomplicate

TOOL USAGE EXAMPLES:
- "Check pod status" → Use kubectl_get_pods
- "Show logs" → Use kubectl_get_pod_logs  
- "Scale deployment" → Use kubectl_scale_deployment (will need approval)
- "Why is pod crashing?" → Use kubectl_describe_pod and kubectl_get_events

You are now an ACTIVE agent, not just a consultant. Take action!"""


# Global agent instance
claude_agent = ClaudeAgent()
