"""
DO AI inference client wrapper for chat and image generation.
"""

import logging
import base64
import time
import requests
from typing import Optional, Union
from io import BytesIO

logger = logging.getLogger(__name__)


class DOAIClient:
    """Wrapper for DO AI inference API calls."""

    # DO AI inference endpoint
    BASE_URL = "https://inference.do-ai.run/v1"

    # Fallback responses for when API is rate limited
    FALLBACK_RESPONSES = [
        "Waduh bro, gue lagi kena rate limit dari API nih. Coba lagi nanti ya! 😅",
        "Maaf ya, API gue lagi dibatasin. Tunggu sebentar dulu ya bro! 🙏",
        "Eh sorry, quota API gue abis nih. Nanti gue bales lagi ya! 😊",
        "Wah, API limit exceeded bro. Sabar ya, nanti gue online lagi! 💪",
    ]

    def __init__(self, access_key: str, model_chat: str, model_image: str, max_tokens: int = 400,
                 enable_fallback: bool = True):
        """
        Initialize DO AI client.

        Args:
            access_key: DO AI access key (Bearer token)
            model_chat: Chat model name
            model_image: Image model name
            max_tokens: Maximum tokens for chat responses
            enable_fallback: Whether to use fallback responses when rate limited
        """
        self.access_key = access_key
        self.model_chat = model_chat
        self.model_image = model_image
        self.max_tokens = max_tokens
        self.enable_fallback = enable_fallback
        self.fallback_counter = 0
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_key}"
        })

        logger.info(f"Initialized DOAIClient with chat model: {model_chat}, image model: {model_image}")
        if enable_fallback:
            logger.info("Fallback responses enabled for rate limit scenarios")

    def generate_chat_response(self, prompt: str, temperature: float = 0.7) -> Optional[str]:
        """
        Generate a chat response using DO AI inference API with retry logic.

        Args:
            prompt: The prompt to send to the model
            temperature: Sampling temperature (0.0 to 1.0)

        Returns:
            Generated response text or None if failed
        """
        max_retries = 3
        base_delay = 1.0  # Start with 1 second delay

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt + 1}/{max_retries} for chat response")
                else:
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

            except requests.exceptions.HTTPError as e:
                # Handle rate limiting (429) with exponential backoff
                if e.response.status_code == 429:
                    # Check for Retry-After header
                    retry_after = e.response.headers.get('Retry-After')
                    if retry_after:
                        try:
                            delay = float(retry_after)
                            logger.warning(f"Rate limited (429). Retry-After header: {delay}s")
                        except ValueError:
                            delay = base_delay * (2 ** attempt)
                            logger.warning(f"Rate limited (429). Using exponential backoff: {delay}s")
                    else:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Rate limited (429). Using exponential backoff: {delay}s")

                    # If this is not the last attempt, wait and retry
                    if attempt < max_retries - 1:
                        logger.info(f"Waiting {delay}s before retry...")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"Rate limit exceeded after {max_retries} attempts")
                        # Use fallback response if enabled
                        if self.enable_fallback:
                            fallback = self._get_fallback_response()
                            logger.warning(f"Using fallback response due to rate limit")
                            return fallback
                        return None
                else:
                    # Other HTTP errors
                    logger.error(f"HTTP {e.response.status_code} error: {e}", exc_info=True)
                    return None

            except requests.exceptions.RequestException as e:
                logger.error(f"Network error generating chat response: {e}", exc_info=True)
                # Retry on network errors
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.info(f"Retrying after network error in {delay}s...")
                    time.sleep(delay)
                    continue
                return None

            except Exception as e:
                logger.error(f"Error generating chat response: {e}", exc_info=True)
                return None

        return None

    def generate_image(self, prompt: str) -> Optional[bytes]:
        """
        Generate an image using DO AI inference API with retry logic.

        Args:
            prompt: The image generation prompt

        Returns:
            Image bytes or None if failed
        """
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt + 1}/{max_retries} for image generation")
                else:
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

            except requests.exceptions.HTTPError as e:
                # Handle rate limiting (429) with exponential backoff
                if e.response.status_code == 429:
                    retry_after = e.response.headers.get('Retry-After')
                    if retry_after:
                        try:
                            delay = float(retry_after)
                            logger.warning(f"Rate limited (429) for image. Retry-After: {delay}s")
                        except ValueError:
                            delay = base_delay * (2 ** attempt)
                            logger.warning(f"Rate limited (429) for image. Exponential backoff: {delay}s")
                    else:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Rate limited (429) for image. Exponential backoff: {delay}s")

                    if attempt < max_retries - 1:
                        logger.info(f"Waiting {delay}s before retry...")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"Rate limit exceeded for image after {max_retries} attempts")
                        return None
                else:
                    logger.error(f"HTTP {e.response.status_code} error generating image: {e}", exc_info=True)
                    return None

            except requests.exceptions.RequestException as e:
                logger.error(f"Network error generating image: {e}", exc_info=True)
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.info(f"Retrying after network error in {delay}s...")
                    time.sleep(delay)
                    continue
                return None

            except Exception as e:
                logger.error(f"Error generating image: {e}", exc_info=True)
                return None

        return None

    def _get_fallback_response(self) -> str:
        """
        Get a fallback response when API is rate limited.
        Rotates through different messages to avoid repetition.

        Returns:
            A friendly fallback message
        """
        response = self.FALLBACK_RESPONSES[self.fallback_counter % len(self.FALLBACK_RESPONSES)]
        self.fallback_counter += 1
        return response

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
                     max_tokens: int = 400, use_mock: bool = False,
                     enable_fallback: bool = True) -> Union[DOAIClient, MockDOAIClient]:
    """
    Factory function to create AI client.

    Args:
        access_key: DO AI access key (Bearer token)
        model_chat: Chat model name
        model_image: Image model name
        max_tokens: Maximum tokens for responses
        use_mock: Whether to use mock client for testing
        enable_fallback: Whether to enable fallback responses when rate limited

    Returns:
        AI client instance
    """
    if use_mock:
        return MockDOAIClient(access_key, model_chat, model_image, max_tokens)
    else:
        return DOAIClient(access_key, model_chat, model_image, max_tokens, enable_fallback)

