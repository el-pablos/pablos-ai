"""
Gradient AI client wrapper for chat and image generation.
"""

import logging
import base64
from typing import Optional, Union
from io import BytesIO

logger = logging.getLogger(__name__)

try:
    from gradientai import Gradient
    GRADIENT_AVAILABLE = True
except ImportError:
    GRADIENT_AVAILABLE = False
    logger.error("gradientai package not available")


class GradientAIClient:
    """Wrapper for Gradient AI API calls."""
    
    def __init__(self, access_key: str, model_chat: str, model_image: str, max_tokens: int = 400):
        """
        Initialize Gradient AI client.
        
        Args:
            access_key: Gradient AI access key
            model_chat: Chat model name
            model_image: Image model name
            max_tokens: Maximum tokens for chat responses
        """
        if not GRADIENT_AVAILABLE:
            raise ImportError("gradientai package is required. Install with: pip install gradientai")
        
        self.access_key = access_key
        self.model_chat = model_chat
        self.model_image = model_image
        self.max_tokens = max_tokens
        self.gradient: Optional[Gradient] = None
        
        logger.info(f"Initialized GradientAIClient with chat model: {model_chat}, image model: {model_image}")
    
    def _ensure_connected(self):
        """Ensure Gradient client is connected."""
        if self.gradient is None:
            try:
                self.gradient = Gradient(access_token=self.access_key)
                logger.info("Connected to Gradient AI")
            except Exception as e:
                logger.error(f"Failed to connect to Gradient AI: {e}")
                raise
    
    def generate_chat_response(self, prompt: str, temperature: float = 0.7) -> Optional[str]:
        """
        Generate a chat response using Gradient AI.
        
        Args:
            prompt: The prompt to send to the model
            temperature: Sampling temperature (0.0 to 1.0)
            
        Returns:
            Generated response text or None if failed
        """
        try:
            self._ensure_connected()
            
            logger.info(f"Generating chat response with model: {self.model_chat}")
            logger.debug(f"Prompt length: {len(prompt)} characters")
            
            # Get the model
            model = self.gradient.get_base_model(base_model_slug=self.model_chat)
            
            # Generate completion
            response = model.complete(
                query=prompt,
                max_generated_token_count=self.max_tokens,
                temperature=temperature
            )
            
            # Extract the generated text
            if hasattr(response, 'generated_output'):
                result = response.generated_output.strip()
            elif hasattr(response, 'text'):
                result = response.text.strip()
            else:
                # Try to get the first choice if available
                result = str(response).strip()
            
            logger.info(f"Generated response length: {len(result)} characters")
            return result
            
        except Exception as e:
            logger.error(f"Error generating chat response: {e}", exc_info=True)
            return None
    
    def generate_image(self, prompt: str) -> Optional[bytes]:
        """
        Generate an image using Gradient AI.
        
        Args:
            prompt: The image generation prompt
            
        Returns:
            Image bytes or None if failed
        """
        try:
            self._ensure_connected()
            
            logger.info(f"Generating image with model: {self.model_image}")
            logger.debug(f"Image prompt: {prompt[:100]}...")
            
            # Get the image model
            model = self.gradient.get_image_model(image_model_slug=self.model_image)
            
            # Generate image
            response = model.generate(prompt=prompt)
            
            # Extract image data
            image_data = None
            
            # Try different response formats
            if hasattr(response, 'image_data'):
                image_data = response.image_data
            elif hasattr(response, 'data'):
                image_data = response.data
            elif hasattr(response, 'images') and len(response.images) > 0:
                image_data = response.images[0]
            
            if image_data:
                # Check if it's base64 encoded
                if isinstance(image_data, str):
                    # Remove data URL prefix if present
                    if image_data.startswith('data:image'):
                        image_data = image_data.split(',', 1)[1]
                    
                    # Decode base64
                    image_bytes = base64.b64decode(image_data)
                    logger.info(f"Generated image size: {len(image_bytes)} bytes")
                    return image_bytes
                elif isinstance(image_data, bytes):
                    logger.info(f"Generated image size: {len(image_data)} bytes")
                    return image_data
            
            logger.error("Could not extract image data from response")
            return None
            
        except Exception as e:
            logger.error(f"Error generating image: {e}", exc_info=True)
            return None
    
    def close(self):
        """Close the Gradient client connection."""
        if self.gradient:
            try:
                self.gradient.close()
                logger.info("Closed Gradient AI connection")
            except Exception as e:
                logger.error(f"Error closing Gradient connection: {e}")
            finally:
                self.gradient = None


class MockGradientAIClient:
    """Mock client for testing without actual API calls."""
    
    def __init__(self, access_key: str, model_chat: str, model_image: str, max_tokens: int = 400):
        """Initialize mock client."""
        self.access_key = access_key
        self.model_chat = model_chat
        self.model_image = model_image
        self.max_tokens = max_tokens
        logger.info("Initialized MockGradientAIClient (for testing)")
    
    def generate_chat_response(self, prompt: str, temperature: float = 0.7) -> Optional[str]:
        """Generate a mock chat response."""
        logger.info("Mock: Generating chat response")
        return "Halo bro! Ini response mock dari Pablos. Gue lagi dalam mode testing nih, jadi belum bisa ngobrol beneran. Tapi tenang, nanti kalau udah production gue bakal lebih asik! 😎"
    
    def generate_image(self, prompt: str) -> Optional[bytes]:
        """Generate a mock image (1x1 pixel PNG)."""
        logger.info("Mock: Generating image")
        # Return a minimal 1x1 transparent PNG
        return base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
        )
    
    def close(self):
        """Close mock client."""
        logger.info("Mock: Closed connection")


def create_ai_client(access_key: str, model_chat: str, model_image: str, 
                     max_tokens: int = 400, use_mock: bool = False) -> Union[GradientAIClient, MockGradientAIClient]:
    """
    Factory function to create AI client.
    
    Args:
        access_key: Gradient AI access key
        model_chat: Chat model name
        model_image: Image model name
        max_tokens: Maximum tokens for responses
        use_mock: Whether to use mock client for testing
        
    Returns:
        AI client instance
    """
    if use_mock:
        return MockGradientAIClient(access_key, model_chat, model_image, max_tokens)
    else:
        return GradientAIClient(access_key, model_chat, model_image, max_tokens)

