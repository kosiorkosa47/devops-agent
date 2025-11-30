"""
Execution Engine - Central orchestrator for tool execution
Handles approval workflow, audit logging, and safe execution
"""
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from app.core.tools import ToolDefinitions
from app.core.executors.kubernetes import KubernetesExecutor
from app.core.redis import get_redis_client
from app.core.predictive_engine import predictive_engine
from app.core.security_engine import security_engine

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """Execution status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"


class ApprovalMode(str, Enum):
    """Approval mode for tool execution"""
    STRICT = "strict"  # Approve every operation (even safe ones)
    NORMAL = "normal"  # Approve dangerous only (default)
    AUTO = "auto"      # Auto-approve everything (dangerous!)


class ExecutionEngine:
    """
    Central execution engine for all tool operations
    Handles approval workflow, audit logging, and validation
    """
    
    def __init__(self, require_approval: bool = True):
        self.require_approval = require_approval
        self.kubernetes = KubernetesExecutor()
        self.validation_enabled = True
        
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        user_id: str,
        conversation_id: str,
        auto_approve: bool = False,
        approval_mode: str = "normal"
    ) -> Dict[str, Any]:
        """
        Execute a tool with approval workflow
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            user_id: User requesting execution
            conversation_id: Conversation context
            auto_approve: Skip approval for safe operations
            
        Returns:
            Execution result with status
        """
        try:
            # Get tool definition
            tool = ToolDefinitions.get_tool_by_name(tool_name)
            is_dangerous = ToolDefinitions.is_dangerous_operation(tool_name)
            
            # Create execution record
            execution_id = f"exec_{datetime.utcnow().timestamp()}"
            execution_record = {
                "id": execution_id,
                "tool_name": tool_name,
                "parameters": parameters,
                "user_id": user_id,
                "conversation_id": conversation_id,
                "is_dangerous": is_dangerous,
                "status": ExecutionStatus.PENDING,
                "created_at": datetime.utcnow().isoformat(),
                "approved_by": None,
                "executed_at": None,
                "result": None,
                "error": None
            }
            
            # Store in Redis for tracking
            await self._store_execution(execution_id, execution_record)
            
            # Check if approval required based on mode
            needs_approval = self._needs_approval(
                is_dangerous=is_dangerous,
                auto_approve=auto_approve,
                approval_mode=approval_mode
            )
            
            if needs_approval:
                logger.info(f"Execution {execution_id} requires approval: {tool_name}")
                return {
                    "status": "approval_required",
                    "execution_id": execution_id,
                    "tool_name": tool_name,
                    "parameters": parameters,
                    "is_dangerous": is_dangerous,
                    "message": f"⚠️ This operation requires approval: {tool_name}",
                    "description": tool["description"]
                }
            
            # Execute immediately
            return await self._execute_tool_internal(execution_id, execution_record)
            
        except Exception as e:
            logger.error(f"Execution error: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def approve_execution(
        self,
        execution_id: str,
        user_id: str,
        approved: bool
    ) -> Dict[str, Any]:
        """
        Approve or reject a pending execution
        
        Args:
            execution_id: ID of the execution to approve
            user_id: User approving
            approved: True to approve, False to reject
            
        Returns:
            Execution result if approved
        """
        try:
            # Get execution record
            execution_record = await self._get_execution(execution_id)
            if not execution_record:
                return {"error": "Execution not found"}
            
            if execution_record["status"] != ExecutionStatus.PENDING:
                return {"error": f"Execution is not pending (status: {execution_record['status']})"}
            
            if not approved:
                # Rejected
                execution_record["status"] = ExecutionStatus.REJECTED
                execution_record["approved_by"] = user_id
                execution_record["executed_at"] = datetime.utcnow().isoformat()
                await self._store_execution(execution_id, execution_record)
                
                logger.info(f"Execution {execution_id} rejected by {user_id}")
                return {
                    "status": "rejected",
                    "execution_id": execution_id,
                    "message": "Execution rejected by user"
                }
            
            # Approved - execute
            execution_record["status"] = ExecutionStatus.APPROVED
            execution_record["approved_by"] = user_id
            await self._store_execution(execution_id, execution_record)
            
            logger.info(f"Execution {execution_id} approved by {user_id}")
            return await self._execute_tool_internal(execution_id, execution_record)
            
        except Exception as e:
            logger.error(f"Approval error: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def _execute_tool_internal(
        self,
        execution_id: str,
        execution_record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Internal method to actually execute the tool
        """
        tool_name = execution_record["tool_name"]
        parameters = execution_record["parameters"]
        
        try:
            execution_record["status"] = ExecutionStatus.EXECUTING
            execution_record["executed_at"] = datetime.utcnow().isoformat()
            await self._store_execution(execution_id, execution_record)
            
            # Route to appropriate executor
            result = await self._route_execution(tool_name, parameters)
            
            # Validate result if enabled
            if self.validation_enabled:
                validation = await self._validate_result(tool_name, result)
                if not validation["valid"]:
                    logger.warning(f"Validation warning for {tool_name}: {validation.get('message')}")
                    result["validation_warning"] = validation.get("message")
            
            # Update record with result
            execution_record["status"] = ExecutionStatus.SUCCESS
            execution_record["result"] = result
            await self._store_execution(execution_id, execution_record)
            
            # Log to audit trail
            await self._audit_log(execution_record)
            
            logger.info(f"Execution {execution_id} completed successfully")
            
            return {
                "status": "success",
                "execution_id": execution_id,
                "tool_name": tool_name,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Tool execution error: {e}", exc_info=True)
            
            execution_record["status"] = ExecutionStatus.FAILED
            execution_record["error"] = str(e)
            await self._store_execution(execution_id, execution_record)
            await self._audit_log(execution_record)
            
            return {
                "status": "failed",
                "execution_id": execution_id,
                "error": str(e)
            }
    
    def _needs_approval(
        self,
        is_dangerous: bool,
        auto_approve: bool,
        approval_mode: str
    ) -> bool:
        """
        Determine if operation needs approval based on mode
        
        Modes:
        - STRICT: Approve every operation (even safe ones)
        - NORMAL: Approve dangerous only (default)
        - AUTO: Auto-approve everything (dangerous!)
        """
        if approval_mode == ApprovalMode.AUTO:
            # Auto-approve everything
            return False
        
        elif approval_mode == ApprovalMode.STRICT:
            # Require approval for everything (unless explicitly auto-approved)
            return not auto_approve
        
        else:  # NORMAL mode (default)
            # Approve dangerous operations only
            return is_dangerous and self.require_approval and not auto_approve
    
    async def _validate_result(self, tool_name: str, result: Any) -> Dict[str, Any]:
        """
        Validate tool execution result
        Returns: {"valid": bool, "message": str}
        """
        try:
            # Convert result to string for analysis
            result_str = str(result).lower()
            
            # Check for common error indicators
            error_indicators = ["error", "failed", "exception", "not found", "denied", "forbidden"]
            has_error = any(indicator in result_str for indicator in error_indicators)
            
            if has_error:
                return {
                    "valid": False,
                    "message": "Result contains error indicators. Verify operation succeeded.",
                    "suggestion": "Check logs and pod status to confirm"
                }
            
            # Check if result is empty (might indicate problem)
            if not result or (isinstance(result, (dict, list)) and len(result) == 0):
                return {
                    "valid": False,
                    "message": "Result is empty. Operation may not have produced expected output.",
                    "suggestion": "Verify the resource exists and parameters are correct"
                }
            
            # Result looks good
            return {
                "valid": True,
                "message": "Result validation passed"
            }
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return {
                "valid": True,  # Don't fail execution due to validation error
                "message": f"Could not validate result: {e}"
            }
    
    async def _route_execution(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Route execution to appropriate executor"""
        
        # Kubernetes tools (including new analysis and self-healing tools)
        if tool_name.startswith("kubectl_") or tool_name.startswith("analyze_") or tool_name.startswith("auto_"):
            method_name = tool_name
            method = getattr(self.kubernetes, method_name, None)
            if method:
                return await method(**parameters)
            else:
                raise ValueError(f"Kubernetes method not found: {method_name}")
        
        # Docker tools
        elif tool_name.startswith("docker_"):
            # TODO: Implement Docker executor
            return {"message": "Docker executor not yet implemented"}
        
        # Git tools
        elif tool_name.startswith("git_"):
            # TODO: Implement Git executor
            return {"message": "Git executor not yet implemented"}
        
        # Monitoring tools
        elif tool_name.startswith("prometheus_") or tool_name.startswith("check_"):
            # TODO: Implement monitoring executor
            return {"message": "Monitoring executor not yet implemented"}
        
        # Predictive tools
        elif tool_name.startswith("predict_") or tool_name.startswith("suggest_") or tool_name.startswith("identify_"):
            method_name = tool_name
            method = getattr(predictive_engine, method_name, None)
            if method:
                return method(**parameters)
            else:
                raise ValueError(f"Predictive method not found: {method_name}")
        
        # Security tools
        elif tool_name.startswith("scan_") or tool_name == "auto_fix_security_issue":
            method_name = tool_name
            method = getattr(security_engine, method_name, None)
            if method:
                return method(**parameters)
            else:
                raise ValueError(f"Security method not found: {method_name}")
        
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _store_execution(self, execution_id: str, record: Dict[str, Any]) -> None:
        """Store execution record in Redis"""
        try:
            redis = await get_redis_client()
            key = f"execution:{execution_id}"
            await redis.setex(key, 86400, json.dumps(record))  # 24h expiry
        except Exception as e:
            logger.error(f"Failed to store execution: {e}")
    
    async def _get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution record from Redis"""
        try:
            redis = await get_redis_client()
            key = f"execution:{execution_id}"
            data = await redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get execution: {e}")
            return None
    
    async def _audit_log(self, execution_record: Dict[str, Any]) -> None:
        """Log execution to audit trail"""
        try:
            redis = await get_redis_client()
            audit_key = f"audit:{execution_record['user_id']}:{datetime.utcnow().strftime('%Y%m%d')}"
            
            audit_entry = {
                "execution_id": execution_record["id"],
                "tool": execution_record["tool_name"],
                "status": execution_record["status"],
                "timestamp": execution_record["executed_at"],
                "is_dangerous": execution_record["is_dangerous"]
            }
            
            # Append to daily audit log (list)
            await redis.rpush(audit_key, json.dumps(audit_entry))
            await redis.expire(audit_key, 2592000)  # 30 days
            
        except Exception as e:
            logger.error(f"Failed to audit log: {e}")
    
    async def get_execution_history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get execution history for user"""
        try:
            redis = await get_redis_client()
            today = datetime.utcnow().strftime('%Y%m%d')
            audit_key = f"audit:{user_id}:{today}"
            
            # Get today's audit log
            entries = await redis.lrange(audit_key, 0, limit - 1)
            return [json.loads(entry) for entry in entries]
            
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return []
    
    async def get_pending_executions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all pending executions for user"""
        try:
            redis = await get_redis_client()
            pattern = "execution:*"
            pending = []
            
            # Scan for execution keys (in production, use a separate set)
            async for key in redis.scan_iter(match=pattern):
                data = await redis.get(key)
                if data:
                    record = json.loads(data)
                    if (record.get("user_id") == user_id and 
                        record.get("status") == ExecutionStatus.PENDING):
                        pending.append(record)
            
            return pending
            
        except Exception as e:
            logger.error(f"Failed to get pending: {e}")
            return []


# Global execution engine instance
execution_engine = ExecutionEngine(require_approval=True)
