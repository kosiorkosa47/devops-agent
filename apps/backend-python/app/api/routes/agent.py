"""
Agent API endpoints - Agentic execution with tools
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.core.claude_agent import claude_agent
from app.core.execution_engine import execution_engine
from app.core.redis import get_redis_client
from app.api.dependencies import get_current_user
import json

logger = logging.getLogger(__name__)

router = APIRouter()


class AgentRequest(BaseModel):
    """Agent chat request"""
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[str] = None
    auto_approve_safe: bool = True  # Auto-approve safe operations
    approval_mode: str = "normal"  # strict/normal/auto
    claude_model: Optional[str] = None  # Optional model override


class ApprovalRequest(BaseModel):
    """Execution approval request"""
    execution_id: str
    approved: bool


class AgentResponse(BaseModel):
    """Agent response"""
    response: str
    status: str
    conversation_id: str
    tool_uses: list = []
    tool_results: list = []
    execution: Optional[dict] = None


@router.post("/chat", response_model=AgentResponse)
async def agent_chat(
    request: AgentRequest,
    current_user: dict = Depends(get_current_user)
) -> AgentResponse:
    """
    Chat with ATLAS agent - can execute tools
    
    Args:
        request: Agent request
        current_user: Authenticated user
        
    Returns:
        Agent response with any tool executions
    """
    try:
        user_id = current_user.get("sub", "demo-user")
        conversation_id = request.conversation_id or f"conv_{user_id}_{int(__import__('time').time())}"
        redis = await get_redis_client()
        
        # Get conversation history from Redis
        conversation_history = []
        history_key = f"conversation:{conversation_id}"
        stored_history = await redis.get(history_key)
        
        if stored_history:
            conversation_history = json.loads(stored_history)
        
        # Chat with agent (including tool execution)
        result = await claude_agent.chat_with_tools(
            user_message=request.message,
            conversation_history=conversation_history,
            user_id=user_id,
            conversation_id=conversation_id,
            auto_approve_safe=request.auto_approve_safe,
            approval_mode=request.approval_mode,
            claude_model=request.claude_model
        )
        
        # Update conversation history
        conversation_history.append({
            "role": "user",
            "content": request.message
        })
        conversation_history.append({
            "role": "assistant",
            "content": result.get("response", "")
        })
        
        # Save conversation history to Redis (7 days expiry)
        await redis.setex(history_key, 604800, json.dumps(conversation_history))
        
        # Save/update conversation metadata
        from datetime import datetime
        meta_key = f"conversation_meta:{user_id}:{conversation_id}"
        existing_meta = await redis.get(meta_key)
        
        if existing_meta:
            metadata = json.loads(existing_meta)
            metadata["last_updated"] = datetime.utcnow().isoformat()
            metadata["message_count"] = len(conversation_history)
        else:
            # New conversation - generate title from first message
            title = request.message[:50] + ("..." if len(request.message) > 50 else "")
            metadata = {
                "conversation_id": conversation_id,
                "title": title,
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "message_count": len(conversation_history)
            }
        
        await redis.setex(meta_key, 604800, json.dumps(metadata))
        
        # Return response
        return AgentResponse(
            response=result.get("response", ""),
            status=result.get("status", "success"),
            conversation_id=conversation_id,
            tool_uses=result.get("tool_uses", []),
            tool_results=result.get("tool_results", []),
            execution=result.get("execution")
        )
        
    except Exception as e:
        logger.error(f"Agent chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@router.post("/approve")
async def approve_execution(
    request: ApprovalRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Approve or reject a pending execution
    
    Args:
        request: Approval request
        current_user: Authenticated user
        
    Returns:
        Execution result
    """
    try:
        user_id = current_user.get("sub", "demo-user")
        
        result = await execution_engine.approve_execution(
            execution_id=request.execution_id,
            user_id=user_id,
            approved=request.approved
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Approval error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions/pending")
async def get_pending_executions(
    current_user: dict = Depends(get_current_user)
):
    """Get all pending executions for current user"""
    try:
        user_id = current_user.get("sub", "demo-user")
        pending = await execution_engine.get_pending_executions(user_id)
        
        return {
            "pending": pending,
            "count": len(pending)
        }
        
    except Exception as e:
        logger.error(f"Get pending error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions/history")
async def get_execution_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get execution history for current user"""
    try:
        user_id = current_user.get("sub", "demo-user")
        history = await execution_engine.get_execution_history(user_id, limit)
        
        return {
            "history": history,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error(f"Get history error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def list_available_tools(
    current_user: dict = Depends(get_current_user)
):
    """List all available tools"""
    from app.core.tools import ToolDefinitions
    
    tools = ToolDefinitions.get_all_tools()
    
    return {
        "tools": [
            {
                "name": tool["name"],
                "description": tool["description"],
                "is_dangerous": ToolDefinitions.is_dangerous_operation(tool["name"])
            }
            for tool in tools
        ],
        "total": len(tools)
    }


@router.get("/conversations")
async def list_conversations(
    current_user: dict = Depends(get_current_user)
):
    """List all conversations for current user"""
    try:
        user_id = current_user.get("sub", "demo-user")
        redis = await get_redis_client()
        
        # Scan for conversation metadata keys
        conversations = []
        pattern = f"conversation_meta:{user_id}:*"
        
        async for key in redis.scan_iter(match=pattern):
            data = await redis.get(key)
            if data:
                conv_data = json.loads(data)
                conversations.append(conv_data)
        
        # Sort by last_updated (most recent first)
        conversations.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
        
        return {
            "conversations": conversations,
            "total": len(conversations)
        }
        
    except Exception as e:
        logger.error(f"List conversations error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific conversation with full history"""
    try:
        redis = await get_redis_client()
        
        # Get messages
        history_key = f"conversation:{conversation_id}"
        stored_history = await redis.get(history_key)
        
        if not stored_history:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = json.loads(stored_history)
        
        # Get metadata
        user_id = current_user.get("sub", "demo-user")
        meta_key = f"conversation_meta:{user_id}:{conversation_id}"
        meta_data = await redis.get(meta_key)
        
        metadata = json.loads(meta_data) if meta_data else {}
        
        return {
            "conversation_id": conversation_id,
            "messages": messages,
            "metadata": metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a conversation"""
    try:
        user_id = current_user.get("sub", "demo-user")
        redis = await get_redis_client()
        
        # Delete messages
        history_key = f"conversation:{conversation_id}"
        await redis.delete(history_key)
        
        # Delete metadata
        meta_key = f"conversation_meta:{user_id}:{conversation_id}"
        await redis.delete(meta_key)
        
        return {"message": "Conversation deleted successfully"}
        
    except Exception as e:
        logger.error(f"Delete conversation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/conversations/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    title: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Update conversation metadata (e.g., title)"""
    try:
        user_id = current_user.get("sub", "demo-user")
        redis = await get_redis_client()
        
        meta_key = f"conversation_meta:{user_id}:{conversation_id}"
        meta_data = await redis.get(meta_key)
        
        if not meta_data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        metadata = json.loads(meta_data)
        
        if title:
            metadata["title"] = title
        
        # Update metadata
        await redis.setex(meta_key, 604800, json.dumps(metadata))  # 7 days
        
        return metadata
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update conversation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
