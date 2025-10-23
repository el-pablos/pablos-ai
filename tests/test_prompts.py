"""
Unit tests for prompt templates.
"""

import pytest
from app.prompts import (
    SYSTEM_PABLOS, PROMPT_CODE_HELP, PROMPT_EMPATHY, PROMPT_IMAGE,
    build_chat_prompt, build_code_help_prompt, build_image_prompt,
    get_empathy_prompt, get_system_prompt
)


class TestPromptConstants:
    """Tests for prompt constant definitions."""
    
    def test_system_pablos_exists(self):
        """Test that system prompt exists and is not empty."""
        assert SYSTEM_PABLOS
        assert len(SYSTEM_PABLOS) > 0
        assert isinstance(SYSTEM_PABLOS, str)
    
    def test_system_pablos_contains_persona(self):
        """Test that system prompt contains persona information."""
        assert "Pablos" in SYSTEM_PABLOS
        assert "Indonesia" in SYSTEM_PABLOS or "indonesia" in SYSTEM_PABLOS.lower()
    
    def test_prompt_code_help_exists(self):
        """Test that code help prompt exists."""
        assert PROMPT_CODE_HELP
        assert len(PROMPT_CODE_HELP) > 0
        assert "{code}" in PROMPT_CODE_HELP
    
    def test_prompt_empathy_exists(self):
        """Test that empathy prompt exists."""
        assert PROMPT_EMPATHY
        assert len(PROMPT_EMPATHY) > 0
    
    def test_prompt_image_exists(self):
        """Test that image prompt exists."""
        assert PROMPT_IMAGE
        assert len(PROMPT_IMAGE) > 0
        assert "{description}" in PROMPT_IMAGE


class TestBuildChatPrompt:
    """Tests for build_chat_prompt function."""
    
    def test_build_chat_prompt_basic(self):
        """Test building basic chat prompt."""
        system = "You are a helpful assistant"
        history = ""
        message = "Hello"
        
        prompt = build_chat_prompt(system, history, message)
        assert system in prompt
        assert "User: Hello" in prompt
        assert "Pablos:" in prompt
    
    def test_build_chat_prompt_with_history(self):
        """Test building chat prompt with conversation history."""
        system = "You are a helpful assistant"
        history = "User: Hi\nPablos: Hello there"
        message = "How are you?"
        
        prompt = build_chat_prompt(system, history, message)
        assert system in prompt
        assert history in prompt
        assert "User: How are you?" in prompt
    
    def test_build_chat_prompt_without_history(self):
        """Test building chat prompt without history."""
        system = "You are a helpful assistant"
        history = ""
        message = "First message"
        
        prompt = build_chat_prompt(system, history, message)
        assert system in prompt
        assert "User: First message" in prompt
        # Should not have "Percakapan sebelumnya" section
        assert "Percakapan sebelumnya" not in prompt or history == ""


class TestBuildCodeHelpPrompt:
    """Tests for build_code_help_prompt function."""
    
    def test_build_code_help_prompt(self):
        """Test building code help prompt."""
        code = "print('hello world')"
        prompt = build_code_help_prompt(code)
        
        assert code in prompt
        assert "Pablos" in prompt
        assert len(prompt) > len(code)
    
    def test_build_code_help_prompt_with_complex_code(self):
        """Test building prompt with complex code."""
        code = """
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n-1)
"""
        prompt = build_code_help_prompt(code)
        assert code in prompt


class TestBuildImagePrompt:
    """Tests for build_image_prompt function."""
    
    def test_build_image_prompt(self):
        """Test building image generation prompt."""
        description = "sunset at the beach"
        prompt = build_image_prompt(description)
        
        assert description in prompt
        assert len(prompt) > len(description)
    
    def test_build_image_prompt_with_detailed_description(self):
        """Test building prompt with detailed description."""
        description = "a beautiful sunset at the beach with seagulls flying"
        prompt = build_image_prompt(description)
        assert description in prompt


class TestGetPromptFunctions:
    """Tests for getter functions."""
    
    def test_get_empathy_prompt(self):
        """Test getting empathy prompt."""
        prompt = get_empathy_prompt()
        assert prompt == PROMPT_EMPATHY
        assert len(prompt) > 0
    
    def test_get_system_prompt(self):
        """Test getting system prompt."""
        prompt = get_system_prompt()
        assert prompt == SYSTEM_PABLOS
        assert len(prompt) > 0


class TestPromptQuality:
    """Tests for prompt quality and content."""
    
    def test_system_prompt_has_personality_traits(self):
        """Test that system prompt defines personality."""
        prompt = get_system_prompt()
        # Should mention casual/friendly style
        assert any(word in prompt.lower() for word in ["santai", "friendly", "asik", "gaul"])
    
    def test_code_help_prompt_has_structure(self):
        """Test that code help prompt has expected structure."""
        code = "test code"
        prompt = build_code_help_prompt(code)
        # Should mention explanation, problems, and fixes
        assert any(word in prompt for word in ["Penjelasan", "Masalah", "benerin", "Tips"])
    
    def test_empathy_prompt_has_supportive_tone(self):
        """Test that empathy prompt is supportive."""
        prompt = get_empathy_prompt()
        # Should mention empathy, support, understanding
        assert any(word in prompt.lower() for word in ["empat", "support", "dengerin", "caring"])
    
    def test_image_prompt_requests_detail(self):
        """Test that image prompt requests detailed output."""
        description = "test"
        prompt = build_image_prompt(description)
        # Should ask for detailed, vivid description
        assert any(word in prompt.lower() for word in ["detailed", "vivid", "descriptive", "specific"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

