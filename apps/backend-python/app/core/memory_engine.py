"""
Long-Term Memory Engine
Agent's persistent memory system across all conversations
"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)


class MemoryEngine:
    """
    Long-term memory system for the agent
    Extracts, stores, and retrieves important information across conversations
    """
    
    def __init__(self):
        self.memory_ttl = 2592000  # 30 days
        
    async def extract_and_store_memory(
        self,
        user_id: str,
        conversation_id: str,
        user_message: str,
        assistant_response: str,
        tool_uses: List[Dict] = None
    ) -> None:
        """
        Extract important information from conversation and store in long-term memory
        
        Args:
            user_id: User identifier
            conversation_id: Current conversation ID
            user_message: User's message
            assistant_response: Assistant's response
            tool_uses: Tools used in this interaction
        """
        try:
            redis = await get_redis_client()
            
            # Extract memories from conversation
            memories = self._extract_memories(
                user_message, 
                assistant_response, 
                tool_uses or []
            )
            
            # Store each memory
            for memory in memories:
                memory_entry = {
                    "content": memory,
                    "conversation_id": conversation_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_message": user_message[:200],  # Store snippet for context
                    "type": self._classify_memory_type(memory)
                }
                
                # Add to user's memory list
                memory_key = f"memory:{user_id}"
                await redis.rpush(memory_key, json.dumps(memory_entry))
                await redis.expire(memory_key, self.memory_ttl)
            
            logger.info(f"Stored {len(memories)} memories for user {user_id}")
            
        except Exception as e:
            logger.error(f"Memory storage error: {e}", exc_info=True)
    
    def _extract_memories(
        self,
        user_message: str,
        assistant_response: str,
        tool_uses: List[Dict]
    ) -> List[str]:
        """Extract memorable facts from conversation"""
        memories = []
        
        # Extract user preferences
        if any(word in user_message.lower() for word in ['prefer', 'like', 'want', 'need', 'use']):
            memories.append(f"User preference: {user_message}")
        
        # Extract project/system information
        if any(word in user_message.lower() for word in ['project', 'system', 'application', 'service']):
            memories.append(f"Project context: {user_message}")
        
        # Extract tool usage patterns
        if tool_uses:
            tools_used = [tool.get('name', '') for tool in tool_uses]
            if tools_used:
                memories.append(f"Used tools: {', '.join(tools_used)}")
        
        # Extract technical details
        if any(word in user_message.lower() for word in ['install', 'configure', 'setup', 'deploy']):
            memories.append(f"Technical action: {user_message}")
        
        # Extract problems/issues user encountered
        if any(word in user_message.lower() for word in ['error', 'problem', 'issue', 'bug', 'not working']):
            memories.append(f"User encountered issue: {user_message}")
        
        # Extract successful solutions
        if any(word in assistant_response.lower() for word in ['successfully', 'completed', 'installed', 'fixed']):
            memories.append(f"Successful solution: {assistant_response[:200]}")
        
        return memories
    
    def _classify_memory_type(self, memory: str) -> str:
        """Classify memory into categories"""
        memory_lower = memory.lower()
        
        if 'prefer' in memory_lower or 'like' in memory_lower:
            return 'preference'
        elif 'project' in memory_lower or 'system' in memory_lower:
            return 'project_context'
        elif 'used tools' in memory_lower:
            return 'tool_usage'
        elif 'error' in memory_lower or 'issue' in memory_lower:
            return 'problem'
        elif 'success' in memory_lower or 'completed' in memory_lower:
            return 'solution'
        else:
            return 'general'
    
    async def get_relevant_memories(
        self,
        user_id: str,
        current_message: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories for current context
        
        Args:
            user_id: User identifier
            current_message: Current user message
            limit: Maximum number of memories to retrieve
            
        Returns:
            List of relevant memories
        """
        try:
            redis = await get_redis_client()
            memory_key = f"memory:{user_id}"
            
            # Get all memories
            all_memories = await redis.lrange(memory_key, 0, -1)
            
            if not all_memories:
                return []
            
            # Parse and score memories by relevance
            scored_memories = []
            current_words = set(current_message.lower().split())
            
            for memory_json in all_memories:
                memory = json.loads(memory_json)
                
                # Calculate relevance score
                memory_words = set(memory['content'].lower().split())
                common_words = current_words & memory_words
                relevance_score = len(common_words)
                
                # Boost recent memories
                try:
                    timestamp = datetime.fromisoformat(memory['timestamp'])
                    age_hours = (datetime.utcnow() - timestamp).total_seconds() / 3600
                    recency_boost = max(0, 10 - (age_hours / 24))  # Boost recent memories
                    relevance_score += recency_boost
                except:
                    pass
                
                scored_memories.append((relevance_score, memory))
            
            # Sort by relevance and return top N
            scored_memories.sort(reverse=True, key=lambda x: x[0])
            relevant_memories = [mem for score, mem in scored_memories[:limit] if score > 0]
            
            logger.info(f"Retrieved {len(relevant_memories)} relevant memories for user {user_id}")
            return relevant_memories
            
        except Exception as e:
            logger.error(f"Memory retrieval error: {e}", exc_info=True)
            return []
    
    async def build_memory_context(
        self,
        user_id: str,
        current_message: str
    ) -> str:
        """
        Build context string from relevant memories to inject into system prompt
        
        Args:
            user_id: User identifier
            current_message: Current user message
            
        Returns:
            Formatted memory context string
        """
        memories = await self.get_relevant_memories(user_id, current_message, limit=10)
        
        if not memories:
            return ""
        
        context_parts = ["## Long-term Memory", "Things I remember about you and our previous interactions:\n"]
        
        # Group by type
        by_type = {}
        for memory in memories:
            mem_type = memory.get('type', 'general')
            if mem_type not in by_type:
                by_type[mem_type] = []
            by_type[mem_type].append(memory)
        
        # Format memories
        type_labels = {
            'preference': '**Your Preferences:**',
            'project_context': '**Project Context:**',
            'tool_usage': '**Tools You Used:**',
            'problem': '**Issues You Encountered:**',
            'solution': '**Solutions That Worked:**',
            'general': '**Other Context:**'
        }
        
        for mem_type, label in type_labels.items():
            if mem_type in by_type:
                context_parts.append(f"\n{label}")
                for memory in by_type[mem_type][:3]:  # Max 3 per category
                    content = memory['content']
                    # Remove prefix if present
                    for prefix in ['User preference: ', 'Project context: ', 'Used tools: ', 
                                  'Technical action: ', 'User encountered issue: ', 'Successful solution: ']:
                        if content.startswith(prefix):
                            content = content[len(prefix):]
                    context_parts.append(f"- {content}")
        
        return "\n".join(context_parts)
    
    async def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics about user's memories"""
        try:
            redis = await get_redis_client()
            memory_key = f"memory:{user_id}"
            
            all_memories = await redis.lrange(memory_key, 0, -1)
            
            if not all_memories:
                return {
                    "total_memories": 0,
                    "by_type": {},
                    "oldest_memory": None,
                    "newest_memory": None
                }
            
            # Count by type
            by_type = {}
            timestamps = []
            
            for memory_json in all_memories:
                memory = json.loads(memory_json)
                mem_type = memory.get('type', 'general')
                by_type[mem_type] = by_type.get(mem_type, 0) + 1
                
                try:
                    timestamps.append(datetime.fromisoformat(memory['timestamp']))
                except:
                    pass
            
            return {
                "total_memories": len(all_memories),
                "by_type": by_type,
                "oldest_memory": min(timestamps).isoformat() if timestamps else None,
                "newest_memory": max(timestamps).isoformat() if timestamps else None
            }
            
        except Exception as e:
            logger.error(f"Memory stats error: {e}", exc_info=True)
            return {"error": str(e)}


# Global instance
memory_engine = MemoryEngine()
