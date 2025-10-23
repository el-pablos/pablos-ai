"""
Unit tests for conversation memory.
"""

import pytest
from app.memory import Message, InMemoryBackend, ConversationMemory


class TestMessage:
    """Tests for Message class."""
    
    def test_message_creation(self):
        """Test creating a message."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
    
    def test_message_to_dict(self):
        """Test converting message to dictionary."""
        msg = Message(role="assistant", content="Hi there")
        msg_dict = msg.to_dict()
        assert msg_dict == {"role": "assistant", "content": "Hi there"}
    
    def test_message_from_dict(self):
        """Test creating message from dictionary."""
        msg_dict = {"role": "user", "content": "Test"}
        msg = Message.from_dict(msg_dict)
        assert msg.role == "user"
        assert msg.content == "Test"


class TestInMemoryBackend:
    """Tests for InMemoryBackend class."""
    
    def test_empty_history(self):
        """Test getting history for new user."""
        backend = InMemoryBackend()
        history = backend.get_history(user_id=123)
        assert history == []
    
    def test_add_and_get_message(self):
        """Test adding and retrieving messages."""
        backend = InMemoryBackend()
        backend.add_message(user_id=123, role="user", content="Hello")
        history = backend.get_history(user_id=123)
        assert len(history) == 1
        assert history[0].role == "user"
        assert history[0].content == "Hello"
    
    def test_multiple_messages(self):
        """Test adding multiple messages."""
        backend = InMemoryBackend()
        backend.add_message(user_id=123, role="user", content="Hi")
        backend.add_message(user_id=123, role="assistant", content="Hello")
        backend.add_message(user_id=123, role="user", content="How are you?")
        
        history = backend.get_history(user_id=123)
        assert len(history) == 3
        assert history[0].content == "Hi"
        assert history[1].content == "Hello"
        assert history[2].content == "How are you?"
    
    def test_max_messages_limit(self):
        """Test that max_messages parameter works."""
        backend = InMemoryBackend()
        for i in range(20):
            backend.add_message(user_id=123, role="user", content=f"Message {i}")
        
        history = backend.get_history(user_id=123, max_messages=5)
        assert len(history) == 5
        # Should get the last 5 messages
        assert history[-1].content == "Message 19"
    
    def test_per_user_isolation(self):
        """Test that messages are isolated per user."""
        backend = InMemoryBackend()
        backend.add_message(user_id=123, role="user", content="User 123")
        backend.add_message(user_id=456, role="user", content="User 456")
        
        history_123 = backend.get_history(user_id=123)
        history_456 = backend.get_history(user_id=456)
        
        assert len(history_123) == 1
        assert len(history_456) == 1
        assert history_123[0].content == "User 123"
        assert history_456[0].content == "User 456"
    
    def test_clear_history(self):
        """Test clearing user history."""
        backend = InMemoryBackend()
        backend.add_message(user_id=123, role="user", content="Hello")
        backend.clear_history(user_id=123)
        history = backend.get_history(user_id=123)
        assert history == []
    
    def test_message_limit_prevents_bloat(self):
        """Test that storage doesn't grow indefinitely."""
        backend = InMemoryBackend()
        # Add more than 50 messages (the internal limit)
        for i in range(100):
            backend.add_message(user_id=123, role="user", content=f"Message {i}")
        
        # Internal storage should be limited to 50
        assert len(backend.storage[123]) == 50
        # Should have the most recent messages
        assert backend.storage[123][-1].content == "Message 99"


class TestConversationMemory:
    """Tests for ConversationMemory class."""
    
    def test_memory_initialization_without_redis(self):
        """Test that memory initializes with in-memory backend when no Redis."""
        memory = ConversationMemory()
        assert isinstance(memory.backend, InMemoryBackend)
    
    def test_add_user_message(self):
        """Test adding user message."""
        memory = ConversationMemory()
        memory.add_user_message(user_id=123, content="Hello")
        history = memory.get_history(user_id=123)
        assert len(history) == 1
        assert history[0].role == "user"
        assert history[0].content == "Hello"
    
    def test_add_assistant_message(self):
        """Test adding assistant message."""
        memory = ConversationMemory()
        memory.add_assistant_message(user_id=123, content="Hi there")
        history = memory.get_history(user_id=123)
        assert len(history) == 1
        assert history[0].role == "assistant"
        assert history[0].content == "Hi there"
    
    def test_conversation_flow(self):
        """Test a full conversation flow."""
        memory = ConversationMemory()
        memory.add_user_message(user_id=123, content="Hello")
        memory.add_assistant_message(user_id=123, content="Hi there")
        memory.add_user_message(user_id=123, content="How are you?")
        memory.add_assistant_message(user_id=123, content="I'm good!")
        
        history = memory.get_history(user_id=123)
        assert len(history) == 4
        assert history[0].role == "user"
        assert history[1].role == "assistant"
        assert history[2].role == "user"
        assert history[3].role == "assistant"
    
    def test_format_history_for_prompt(self):
        """Test formatting history as prompt string."""
        memory = ConversationMemory()
        memory.add_user_message(user_id=123, content="Hello")
        memory.add_assistant_message(user_id=123, content="Hi there")
        
        formatted = memory.format_history_for_prompt(user_id=123)
        assert "User: Hello" in formatted
        assert "Pablos: Hi there" in formatted
    
    def test_format_empty_history(self):
        """Test formatting empty history."""
        memory = ConversationMemory()
        formatted = memory.format_history_for_prompt(user_id=123)
        assert formatted == ""
    
    def test_clear_history(self):
        """Test clearing conversation history."""
        memory = ConversationMemory()
        memory.add_user_message(user_id=123, content="Hello")
        memory.add_assistant_message(user_id=123, content="Hi")
        memory.clear_history(user_id=123)
        
        history = memory.get_history(user_id=123)
        assert history == []
    
    def test_max_messages_in_get_history(self):
        """Test limiting number of messages retrieved."""
        memory = ConversationMemory()
        for i in range(20):
            memory.add_user_message(user_id=123, content=f"Message {i}")
        
        history = memory.get_history(user_id=123, max_messages=5)
        assert len(history) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

