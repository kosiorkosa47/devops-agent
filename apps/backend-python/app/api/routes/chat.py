"""
Chat API endpoints
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.claude import claude_client
from app.core.redis import get_redis_client
from app.api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


class Message(BaseModel):
    """Chat message model"""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=10000)


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[str] = None
    system_prompt: Optional[str] = None
    stream: bool = False


class ChatResponse(BaseModel):
    """Chat response model"""
    id: str
    message: str
    conversation_id: str
    model: str
    usage: dict


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
) -> ChatResponse:
    """
    Send a message to Claude and get a response
    
    Args:
        request: Chat request with message and optional context
        current_user: Authenticated user
        
    Returns:
        Claude's response
    """
    try:
        # Get conversation history from Redis if conversation_id provided
        conversation_history = []
        if request.conversation_id:
            redis = await get_redis_client()
            history_key = f"conversation:{request.conversation_id}"
            stored_history = await redis.get(history_key)
            if stored_history:
                import json
                conversation_history = json.loads(stored_history)
        
        # Call Claude API
        response = await claude_client.chat_with_context(
            user_message=request.message,
            conversation_history=conversation_history,
            system_prompt=request.system_prompt
        )
        
        # Update conversation history
        conversation_history.append({
            "role": "user",
            "content": request.message
        })
        conversation_history.append({
            "role": "assistant",
            "content": response["content"]
        })
        
        # Store in Redis (expires after 24 hours)
        if request.conversation_id:
            import json
            await redis.setex(
                history_key,
                86400,  # 24 hours
                json.dumps(conversation_history)
            )
        
        conversation_id = request.conversation_id or response["id"]
        
        logger.info(f"Chat completed for user {current_user.get('sub')}. Conversation: {conversation_id}")
        
        return ChatResponse(
            id=response["id"],
            message=response["content"],
            conversation_id=conversation_id,
            model=response["model"],
            usage=response["usage"]
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Stream chat response from Claude
    
    Args:
        request: Chat request
        current_user: Authenticated user
        
    Returns:
        Streaming response
    """
    async def generate():
        try:
            conversation_history = []
            if request.conversation_id:
                redis = await get_redis_client()
                history_key = f"conversation:{request.conversation_id}"
                stored_history = await redis.get(history_key)
                if stored_history:
                    import json
                    conversation_history = json.loads(stored_history)
            
            conversation_history.append({
                "role": "user",
                "content": request.message
            })
            
            full_response = ""
            async for chunk in claude_client._stream_chat(
                model=claude_client.model,
                messages=conversation_history,
                max_tokens=claude_client.max_tokens,
                temperature=claude_client.temperature
            ):
                full_response += chunk
                yield f"data: {chunk}\n\n"
            
            # Store conversation
            conversation_history.append({
                "role": "assistant",
                "content": full_response
            })
            
            if request.conversation_id:
                import json
                await redis.setex(
                    history_key,
                    86400,
                    json.dumps(conversation_history)
                )
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield f"data: ERROR: {str(e)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a conversation from history"""
    try:
        redis = await get_redis_client()
        history_key = f"conversation:{conversation_id}"
        await redis.delete(history_key)
        
        return {"message": "Conversation deleted successfully"}
        
    except Exception as e:
        logger.error(f"Delete conversation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete conversation")
