"""
Utility functions for the Telegram bot.
Includes message chunking, rate limiting, and caching.
"""

import time
import hashlib
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Telegram message limit
TELEGRAM_MAX_MESSAGE_LENGTH = 4096


class RateLimiter:
    """Simple per-user rate limiter using in-memory storage."""
    
    def __init__(self, cooldown_seconds: int = 2):
        """
        Initialize rate limiter.
        
        Args:
            cooldown_seconds: Minimum seconds between requests per user
        """
        self.cooldown_seconds = cooldown_seconds
        self.last_request: Dict[int, float] = {}
    
    def check_rate_limit(self, user_id: int) -> tuple[bool, float]:
        """
        Check if user is rate limited.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Tuple of (is_allowed, seconds_remaining)
        """
        current_time = time.time()
        last_time = self.last_request.get(user_id, 0)
        time_passed = current_time - last_time
        
        if time_passed >= self.cooldown_seconds:
            self.last_request[user_id] = current_time
            return True, 0.0
        else:
            remaining = self.cooldown_seconds - time_passed
            return False, remaining
    
    def reset_user(self, user_id: int) -> None:
        """Reset rate limit for a specific user."""
        if user_id in self.last_request:
            del self.last_request[user_id]


class SimpleCache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize cache.
        
        Args:
            ttl_seconds: Time to live for cached items in seconds
        """
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, tuple[Any, float]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                logger.debug(f"Cache hit for key: {key[:50]}...")
                return value
            else:
                # Expired, remove it
                del self.cache[key]
                logger.debug(f"Cache expired for key: {key[:50]}...")
        return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self.cache[key] = (value, time.time())
        logger.debug(f"Cache set for key: {key[:50]}...")
    
    def clear(self) -> None:
        """Clear all cached items."""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def cleanup_expired(self) -> int:
        """
        Remove expired items from cache.
        
        Returns:
            Number of items removed
        """
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp >= self.ttl_seconds
        ]
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache items")
        return len(expired_keys)


def chunk_message(text: str, max_length: int = TELEGRAM_MAX_MESSAGE_LENGTH) -> List[str]:
    """
    Split a long message into chunks that fit Telegram's message limit.
    Tries to split at newlines or spaces to avoid breaking words.

    Args:
        text: The text to split
        max_length: Maximum length per chunk (default: Telegram's limit)

    Returns:
        List of text chunks
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""

    # Split by paragraphs first
    paragraphs = text.split('\n\n')

    for paragraph in paragraphs:
        # If paragraph itself is too long, split by lines
        if len(paragraph) > max_length:
            lines = paragraph.split('\n')
            for line in lines:
                # If line is still too long, split by words
                if len(line) > max_length:
                    words = line.split(' ')
                    for word in words:
                        # If a single word is longer than max_length, force split it
                        if len(word) > max_length:
                            # First, append current chunk if any
                            if current_chunk:
                                chunks.append(current_chunk)
                                current_chunk = ""
                            # Split the long word into chunks
                            for i in range(0, len(word), max_length):
                                chunks.append(word[i:i + max_length])
                        elif len(current_chunk) + len(word) + 1 <= max_length:
                            current_chunk += (' ' if current_chunk else '') + word
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = word
                else:
                    if len(current_chunk) + len(line) + 1 <= max_length:
                        current_chunk += ('\n' if current_chunk else '') + line
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = line
        else:
            if len(current_chunk) + len(paragraph) + 2 <= max_length:
                current_chunk += ('\n\n' if current_chunk else '') + paragraph
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def hash_prompt(prompt: str) -> str:
    """
    Create a hash of a prompt for caching purposes.
    
    Args:
        prompt: The prompt text
        
    Returns:
        SHA256 hash of the prompt
    """
    return hashlib.sha256(prompt.encode('utf-8')).hexdigest()


def detect_code_block(text: str) -> Optional[str]:
    """
    Detect if message contains a code block (markdown format).
    
    Args:
        text: Message text
        
    Returns:
        Extracted code or None if no code block found
    """
    # Check for markdown code blocks (```...```)
    if '```' in text:
        parts = text.split('```')
        if len(parts) >= 3:
            # Get the code between first pair of ```
            code = parts[1]
            # Remove language identifier if present (e.g., ```python)
            lines = code.split('\n')
            if lines and lines[0].strip() and not ' ' in lines[0].strip():
                code = '\n'.join(lines[1:])
            return code.strip()
    
    # Check for inline code blocks (single backticks with multiple lines)
    if '`' in text and text.count('`') >= 2:
        parts = text.split('`')
        if len(parts) >= 3:
            code = parts[1]
            if '\n' in code or len(code) > 50:  # Likely code if multiline or long
                return code.strip()
    
    return None


def is_explain_request(text: str) -> bool:
    """
    Check if message is a code explanation request.
    
    Args:
        text: Message text
        
    Returns:
        True if message starts with 'explain:' prefix
    """
    return text.lower().strip().startswith('explain:')


def extract_explain_content(text: str) -> str:
    """
    Extract content after 'explain:' prefix.
    
    Args:
        text: Message text
        
    Returns:
        Content after the prefix
    """
    if is_explain_request(text):
        return text[8:].strip()  # Remove 'explain:' prefix
    return text


def format_timestamp() -> str:
    """
    Get current timestamp in readable format.
    
    Returns:
        Formatted timestamp string
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def sanitize_user_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize user input to prevent abuse.
    
    Args:
        text: User input text
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    return text.strip()

