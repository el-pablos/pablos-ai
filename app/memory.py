"""
Conversation memory management with Redis and in-memory fallback.
Stores per-user conversation history.
"""

import json
import logging
from typing import List, Dict, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Try to import Redis, but make it optional
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, will use in-memory storage")


class Message:
    """Represents a single message in conversation history."""
    
    def __init__(self, role: str, content: str):
        """
        Initialize a message.
        
        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        self.role = role
        self.content = content
    
    def to_dict(self) -> Dict[str, str]:
        """Convert message to dictionary."""
        return {"role": self.role, "content": self.content}
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'Message':
        """Create message from dictionary."""
        return cls(role=data["role"], content=data["content"])


class MemoryBackend(ABC):
    """Abstract base class for memory backends."""
    
    @abstractmethod
    def get_history(self, user_id: int, max_messages: int = 10) -> List[Message]:
        """Get conversation history for a user."""
        pass
    
    @abstractmethod
    def add_message(self, user_id: int, role: str, content: str) -> None:
        """Add a message to user's history."""
        pass
    
    @abstractmethod
    def clear_history(self, user_id: int) -> None:
        """Clear conversation history for a user."""
        pass


class InMemoryBackend(MemoryBackend):
    """In-memory storage backend for conversation history."""
    
    def __init__(self):
        """Initialize in-memory storage."""
        self.storage: Dict[int, List[Message]] = {}
        logger.info("Using in-memory storage for conversation history")
    
    def get_history(self, user_id: int, max_messages: int = 10) -> List[Message]:
        """
        Get conversation history for a user.
        
        Args:
            user_id: Telegram user ID
            max_messages: Maximum number of messages to return
            
        Returns:
            List of messages (most recent first)
        """
        if user_id not in self.storage:
            return []
        
        # Return last N messages
        return self.storage[user_id][-max_messages:]
    
    def add_message(self, user_id: int, role: str, content: str) -> None:
        """
        Add a message to user's history.
        
        Args:
            user_id: Telegram user ID
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        if user_id not in self.storage:
            self.storage[user_id] = []
        
        self.storage[user_id].append(Message(role, content))
        
        # Keep only last 50 messages to prevent memory bloat
        if len(self.storage[user_id]) > 50:
            self.storage[user_id] = self.storage[user_id][-50:]
    
    def clear_history(self, user_id: int) -> None:
        """
        Clear conversation history for a user.
        
        Args:
            user_id: Telegram user ID
        """
        if user_id in self.storage:
            del self.storage[user_id]
            logger.info(f"Cleared history for user {user_id}")


class RedisBackend(MemoryBackend):
    """Redis storage backend for conversation history."""
    
    def __init__(self, redis_client: 'redis.Redis'):
        """
        Initialize Redis backend.
        
        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
        self.key_prefix = "pablos:history:"
        logger.info("Using Redis storage for conversation history")
    
    def _get_key(self, user_id: int) -> str:
        """Get Redis key for user."""
        return f"{self.key_prefix}{user_id}"
    
    def get_history(self, user_id: int, max_messages: int = 10) -> List[Message]:
        """
        Get conversation history for a user.
        
        Args:
            user_id: Telegram user ID
            max_messages: Maximum number of messages to return
            
        Returns:
            List of messages (most recent first)
        """
        try:
            key = self._get_key(user_id)
            # Get last N messages from list
            messages_data = self.redis.lrange(key, -max_messages, -1)
            
            messages = []
            for msg_json in messages_data:
                try:
                    msg_dict = json.loads(msg_json)
                    messages.append(Message.from_dict(msg_dict))
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode message: {msg_json}")
            
            return messages
        except Exception as e:
            logger.error(f"Error getting history from Redis: {e}")
            return []
    
    def add_message(self, user_id: int, role: str, content: str) -> None:
        """
        Add a message to user's history.
        
        Args:
            user_id: Telegram user ID
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        try:
            key = self._get_key(user_id)
            message = Message(role, content)
            msg_json = json.dumps(message.to_dict())
            
            # Add to list
            self.redis.rpush(key, msg_json)
            
            # Keep only last 50 messages
            self.redis.ltrim(key, -50, -1)
            
            # Set expiry to 7 days
            self.redis.expire(key, 7 * 24 * 60 * 60)
        except Exception as e:
            logger.error(f"Error adding message to Redis: {e}")
    
    def clear_history(self, user_id: int) -> None:
        """
        Clear conversation history for a user.
        
        Args:
            user_id: Telegram user ID
        """
        try:
            key = self._get_key(user_id)
            self.redis.delete(key)
            logger.info(f"Cleared history for user {user_id}")
        except Exception as e:
            logger.error(f"Error clearing history from Redis: {e}")


class ConversationMemory:
    """Main conversation memory manager."""
    
    def __init__(self, redis_url: Optional[str] = None, 
                 redis_host: Optional[str] = None,
                 redis_port: Optional[int] = None,
                 redis_password: Optional[str] = None,
                 redis_username: Optional[str] = None):
        """
        Initialize conversation memory.
        
        Args:
            redis_url: Redis connection URL (optional)
            redis_host: Redis host (optional)
            redis_port: Redis port (optional)
            redis_password: Redis password (optional)
            redis_username: Redis username (optional)
        """
        self.backend: MemoryBackend
        
        # Try to connect to Redis if available
        if REDIS_AVAILABLE and (redis_url or redis_host):
            try:
                if redis_url:
                    redis_client = redis.from_url(redis_url, decode_responses=True)
                else:
                    redis_client = redis.Redis(
                        host=redis_host,
                        port=redis_port or 6379,
                        password=redis_password,
                        username=redis_username or 'default',
                        decode_responses=True
                    )
                
                # Test connection
                redis_client.ping()
                self.backend = RedisBackend(redis_client)
                logger.info("Successfully connected to Redis")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Falling back to in-memory storage")
                self.backend = InMemoryBackend()
        else:
            self.backend = InMemoryBackend()
    
    def get_history(self, user_id: int, max_messages: int = 10) -> List[Message]:
        """Get conversation history for a user."""
        return self.backend.get_history(user_id, max_messages)
    
    def add_user_message(self, user_id: int, content: str) -> None:
        """Add a user message to history."""
        self.backend.add_message(user_id, "user", content)
    
    def add_assistant_message(self, user_id: int, content: str) -> None:
        """Add an assistant message to history."""
        self.backend.add_message(user_id, "assistant", content)
    
    def clear_history(self, user_id: int) -> None:
        """Clear conversation history for a user."""
        self.backend.clear_history(user_id)
    
    def format_history_for_prompt(self, user_id: int, max_messages: int = 10) -> str:
        """
        Format conversation history as a string for prompt.
        
        Args:
            user_id: Telegram user ID
            max_messages: Maximum number of messages to include
            
        Returns:
            Formatted history string
        """
        history = self.get_history(user_id, max_messages)
        if not history:
            return ""
        
        formatted = []
        for msg in history:
            role_label = "User" if msg.role == "user" else "Pablos"
            formatted.append(f"{role_label}: {msg.content}")
        
        return "\n".join(formatted)

