"""
DO AI inference client wrapper for chat and image generation.
"""

import logging
import base64
import requests
from typing import Optional, Union
from io import BytesIO

logger = logging.getLogger(__name__)


class DOAIClient:
    """Wrapper for DO AI inference API calls."""

    # DO AI inference endpoint
    BASE_URL = "https://inference.do-ai.run/v1"

    def __init__(self, access_key: str, model_chat: str, model_image: str, max_tokens: int = 400):
        """
        Initialize DO AI client.

        Args:
            access_key: DO AI access key (Bearer token)
            model_chat: Chat model name
            model_image: Image model name
            max_tokens: Maximum tokens for chat responses
        """
        self.access_key = access_key
        self.model_chat = model_chat
        self.model_image = model_image
        self.max_tokens = max_tokens
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_key}"
        })

        logger.info(f"Initialized DOAIClient with chat model: {model_chat}, image model: {model_image}")

    def generate_chat_response(self, prompt: str, temperature: float = 0.7) -> Optional[str]:
        """
        Generate a chat response using DO AI inference API.

        Args:
            prompt: The prompt to send to the model
            temperature: Sampling temperature (0.0 to 1.0)

        Returns:
            Generated response text or None if failed
        """
        try:
            logger.info(f"Generating chat response with model: {self.model_chat}")
            logger.debug(f"Prompt length: {len(prompt)} characters")

            # Prepare the request
            url = f"{self.BASE_URL}/chat/completions"
            data = {
                "model": self.model_chat,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": self.max_tokens,
                "temperature": temperature
            }

            # Make the API request
            response = self.session.post(url, json=data, timeout=30)
            response.raise_for_status()

            # Parse the response
            result_json = response.json()

            # Extract the generated text (OpenAI-compatible format)
            if "choices" in result_json and len(result_json["choices"]) > 0:
                choice = result_json["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    result = choice["message"]["content"].strip()
                    logger.info(f"Generated response length: {len(result)} characters")
                    return result
                elif "text" in choice:
                    result = choice["text"].strip()
                    logger.info(f"Generated response length: {len(result)} characters")
                    return result

            logger.error(f"Unexpected response format: {result_json}")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error generating chat response: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error generating chat response: {e}", exc_info=True)
            return None

    def generate_image(self, prompt: str) -> Optional[bytes]:
        """
        Generate an image using DO AI inference API.

        Args:
            prompt: The image generation prompt

        Returns:
            Image bytes or None if failed
        """
        try:
            logger.info(f"Generating image with model: {self.model_image}")
            logger.debug(f"Image prompt: {prompt[:100]}...")

            # Prepare the request (using OpenAI-compatible images endpoint)
            url = f"{self.BASE_URL}/images/generations"
            data = {
                "model": self.model_image,
                "prompt": prompt,
                "n": 1,
                "response_format": "b64_json"
            }

            # Make the API request
            response = self.session.post(url, json=data, timeout=60)
            response.raise_for_status()

            # Parse the response
            result_json = response.json()

            # Extract image data (OpenAI-compatible format)
            if "data" in result_json and len(result_json["data"]) > 0:
                image_item = result_json["data"][0]

                # Check for base64 encoded image
                if "b64_json" in image_item:
                    image_data = image_item["b64_json"]
                    # Remove data URL prefix if present
                    if image_data.startswith('data:image'):
                        image_data = image_data.split(',', 1)[1]

                    # Decode base64
                    image_bytes = base64.b64decode(image_data)
                    logger.info(f"Generated image size: {len(image_bytes)} bytes")
                    return image_bytes

                # Check for URL (download the image)
                elif "url" in image_item:
                    image_url = image_item["url"]
                    img_response = self.session.get(image_url, timeout=30)
                    img_response.raise_for_status()
                    image_bytes = img_response.content
                    logger.info(f"Downloaded image size: {len(image_bytes)} bytes")
                    return image_bytes

            logger.error(f"Could not extract image data from response: {result_json}")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error generating image: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error generating image: {e}", exc_info=True)
            return None

    def close(self):
        """Close the HTTP session."""
        if self.session:
            try:
                self.session.close()
                logger.info("Closed DO AI client session")
            except Exception as e:
                logger.error(f"Error closing session: {e}")
            finally:
                self.session = None


class MockDOAIClient:
    """Mock client for testing without actual API calls."""

    def __init__(self, access_key: str, model_chat: str, model_image: str, max_tokens: int = 400):
        """Initialize mock client."""
        self.access_key = access_key
        self.model_chat = model_chat
        self.model_image = model_image
        self.max_tokens = max_tokens
        logger.info("Initialized MockDOAIClient (for testing)")

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
                     max_tokens: int = 400, use_mock: bool = False) -> Union[DOAIClient, MockDOAIClient]:
    """
    Factory function to create AI client.

    Args:
        access_key: DO AI access key (Bearer token)
        model_chat: Chat model name
        model_image: Image model name
        max_tokens: Maximum tokens for responses
        use_mock: Whether to use mock client for testing

    Returns:
        AI client instance
    """
    if use_mock:
        return MockDOAIClient(access_key, model_chat, model_image, max_tokens)
    else:
        return DOAIClient(access_key, model_chat, model_image, max_tokens)

