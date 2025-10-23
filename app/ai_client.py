"""
DO AI inference client wrapper for chat and image generation.
"""

import logging
import base64
import time
import requests
from typing import Optional, Union, List, Dict, Any
from io import BytesIO
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class EndpointConfig:
    """Configuration for a single API endpoint."""
    base_url: str
    access_key: str
    model_chat: str
    model_image: str
    name: str = "endpoint"

    # Cooldown tracking
    last_rate_limit_time: Optional[datetime] = None
    cooldown_until: Optional[datetime] = None

    def is_available(self) -> bool:
        """Check if endpoint is available (not in cooldown)."""
        if self.cooldown_until is None:
            return True
        return datetime.now() >= self.cooldown_until

    def mark_rate_limited(self, cooldown_seconds: int = 300):
        """Mark endpoint as rate limited with cooldown period."""
        self.last_rate_limit_time = datetime.now()
        self.cooldown_until = datetime.now() + timedelta(seconds=cooldown_seconds)
        logger.warning(f"Endpoint {self.name} marked as rate-limited. Cooldown until {self.cooldown_until}")

    def reset_cooldown(self):
        """Reset cooldown status."""
        self.cooldown_until = None
        logger.info(f"Endpoint {self.name} cooldown reset")


class DOAIClient:
    """Wrapper for DO AI inference API calls with multi-endpoint failover support."""

    # Fallback responses for when all API endpoints are rate limited
    FALLBACK_RESPONSES = [
        "Waduh bro, gue lagi kena rate limit dari API nih. Coba lagi nanti ya! 😅",
        "Maaf ya, API gue lagi dibatasin. Tunggu sebentar dulu ya bro! 🙏",
        "Eh sorry, quota API gue abis nih. Nanti gue bales lagi ya! 😊",
        "Wah, API limit exceeded bro. Sabar ya, nanti gue online lagi! 💪",
    ]

    def __init__(self, endpoints: List[EndpointConfig], max_tokens: int = 400,
                 enable_fallback: bool = True, endpoint_cooldown: int = 300):
        """
        Initialize DO AI client with multi-endpoint support.

        Args:
            endpoints: List of endpoint configurations (primary, secondary, etc.)
            max_tokens: Maximum tokens for chat responses
            enable_fallback: Whether to use fallback responses when all endpoints are rate limited
            endpoint_cooldown: Cooldown period in seconds for rate-limited endpoints (default: 5 minutes)
        """
        if not endpoints:
            raise ValueError("At least one endpoint configuration is required")

        self.endpoints = endpoints
        self.max_tokens = max_tokens
        self.enable_fallback = enable_fallback
        self.endpoint_cooldown = endpoint_cooldown
        self.fallback_counter = 0
        self.current_endpoint_index = 0

        # Create session pool for each endpoint
        self.sessions: Dict[str, requests.Session] = {}
        for endpoint in self.endpoints:
            session = requests.Session()
            session.headers.update({
                "Content-Type": "application/json",
                "Authorization": f"Bearer {endpoint.access_key}"
            })
            self.sessions[endpoint.name] = session

        logger.info(f"Initialized DOAIClient with {len(self.endpoints)} endpoint(s)")
        for i, endpoint in enumerate(self.endpoints):
            logger.info(f"  Endpoint {i+1} ({endpoint.name}): {endpoint.base_url} - Chat: {endpoint.model_chat}")
        if enable_fallback:
            logger.info("Fallback responses enabled for rate limit scenarios")

    def _get_next_available_endpoint(self) -> Optional[EndpointConfig]:
        """
        Get the next available endpoint that is not in cooldown.
        Tries endpoints in order, wrapping around if needed.

        Returns:
            Available endpoint or None if all are in cooldown
        """
        # First, try to find an available endpoint starting from current index
        for i in range(len(self.endpoints)):
            index = (self.current_endpoint_index + i) % len(self.endpoints)
            endpoint = self.endpoints[index]

            if endpoint.is_available():
                if i > 0:  # We switched endpoints
                    logger.info(f"Switching to endpoint {index + 1}: {endpoint.name} ({endpoint.base_url})")
                    self.current_endpoint_index = index
                return endpoint

        # All endpoints are in cooldown
        logger.warning("All endpoints are in cooldown period")
        return None

    def _try_endpoint_request(self, endpoint: EndpointConfig, url_path: str,
                              data: Dict[str, Any], max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        Try making a request to a specific endpoint with retry logic.

        Args:
            endpoint: Endpoint configuration to use
            url_path: URL path (e.g., '/chat/completions')
            data: Request payload
            max_retries: Maximum retry attempts for this endpoint

        Returns:
            Response JSON or None if failed
        """
        base_delay = 1.0
        session = self.sessions[endpoint.name]
        url = f"{endpoint.base_url}{url_path}"

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt + 1}/{max_retries} on {endpoint.name}")

                # Make the API request
                response = session.post(url, json=data, timeout=30)
                response.raise_for_status()

                # Success! Reset cooldown if it was set
                if endpoint.cooldown_until is not None:
                    endpoint.reset_cooldown()

                return response.json()

            except requests.exceptions.HTTPError as e:
                # Handle rate limiting (429)
                if e.response.status_code == 429:
                    retry_after = e.response.headers.get('Retry-After')
                    if retry_after:
                        try:
                            delay = float(retry_after)
                            logger.warning(f"Rate limited on {endpoint.name}. Retry-After: {delay}s")
                        except ValueError:
                            delay = base_delay * (2 ** attempt)
                            logger.warning(f"Rate limited on {endpoint.name}. Exponential backoff: {delay}s")
                    else:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Rate limited on {endpoint.name}. Exponential backoff: {delay}s")

                    # If this is not the last attempt, wait and retry
                    if attempt < max_retries - 1:
                        logger.info(f"Waiting {delay}s before retry...")
                        time.sleep(delay)
                        continue
                    else:
                        # Mark endpoint as rate limited
                        endpoint.mark_rate_limited(self.endpoint_cooldown)
                        logger.error(f"Endpoint {endpoint.name} rate limited after {max_retries} attempts")
                        return None
                else:
                    # Other HTTP errors
                    logger.error(f"HTTP {e.response.status_code} error on {endpoint.name}: {e}")
                    return None

            except requests.exceptions.RequestException as e:
                logger.error(f"Network error on {endpoint.name}: {e}")
                # Retry on network errors
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.info(f"Retrying after network error in {delay}s...")
                    time.sleep(delay)
                    continue
                return None

            except Exception as e:
                logger.error(f"Unexpected error on {endpoint.name}: {e}", exc_info=True)
                return None

        return None

    def generate_chat_response(self, prompt: str, temperature: float = 0.7) -> Optional[str]:
        """
        Generate a chat response using DO AI inference API with multi-endpoint failover.

        Args:
            prompt: The prompt to send to the model
            temperature: Sampling temperature (0.0 to 1.0)

        Returns:
            Generated response text or None if failed
        """
        logger.info(f"Generating chat response (prompt length: {len(prompt)} characters)")

        # Try each available endpoint
        endpoints_tried = 0
        for _ in range(len(self.endpoints)):
            endpoint = self._get_next_available_endpoint()

            if endpoint is None:
                logger.warning("No available endpoints (all in cooldown)")
                break

            endpoints_tried += 1
            logger.info(f"Trying endpoint: {endpoint.name} ({endpoint.base_url}) - Model: {endpoint.model_chat}")

            # Prepare the request data
            data = {
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": self.max_tokens,
                "temperature": temperature
            }

            # Add model parameter (some endpoints require it, some don't)
            if endpoint.model_chat:
                data["model"] = endpoint.model_chat

            # Try this endpoint with retries
            result_json = self._try_endpoint_request(endpoint, "/chat/completions", data, max_retries=3)

            if result_json:
                # Extract the generated text (OpenAI-compatible format)
                if "choices" in result_json and len(result_json["choices"]) > 0:
                    choice = result_json["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        result = choice["message"]["content"].strip()
                        logger.info(f"✅ Success on {endpoint.name}! Response length: {len(result)} characters")
                        return result
                    elif "text" in choice:
                        result = choice["text"].strip()
                        logger.info(f"✅ Success on {endpoint.name}! Response length: {len(result)} characters")
                        return result

                logger.error(f"Unexpected response format from {endpoint.name}: {result_json}")

            # This endpoint failed, try next one
            logger.warning(f"Endpoint {endpoint.name} failed, trying next endpoint...")
            self.current_endpoint_index = (self.current_endpoint_index + 1) % len(self.endpoints)

        # All endpoints failed
        logger.error(f"All {endpoints_tried} available endpoint(s) failed")

        # Use fallback response if enabled
        if self.enable_fallback:
            fallback = self._get_fallback_response()
            logger.warning(f"Using fallback response (all endpoints failed)")
            return fallback

        return None

    def generate_image(self, prompt: str) -> Optional[bytes]:
        """
        Generate an image using DO AI inference API with multi-endpoint failover.

        Args:
            prompt: The image generation prompt

        Returns:
            Image bytes or None if failed
        """
        logger.info(f"Generating image (prompt: {prompt[:100]}...)")

        # Try each available endpoint
        for _ in range(len(self.endpoints)):
            endpoint = self._get_next_available_endpoint()

            if endpoint is None:
                logger.warning("No available endpoints for image generation")
                break

            logger.info(f"Trying endpoint: {endpoint.name} - Model: {endpoint.model_image}")

            # Prepare the request data
            data = {
                "prompt": prompt,
                "n": 1,
                "response_format": "b64_json"
            }

            if endpoint.model_image:
                data["model"] = endpoint.model_image

            # Try this endpoint
            result_json = self._try_endpoint_request(endpoint, "/images/generations", data, max_retries=2)

            if result_json:
                # Extract image data (OpenAI-compatible format)
                if "data" in result_json and len(result_json["data"]) > 0:
                    image_item = result_json["data"][0]

                    # Check for base64 encoded image
                    if "b64_json" in image_item:
                        image_data = image_item["b64_json"]
                        if image_data.startswith('data:image'):
                            image_data = image_data.split(',', 1)[1]
                        image_bytes = base64.b64decode(image_data)
                        logger.info(f"✅ Image generated on {endpoint.name}! Size: {len(image_bytes)} bytes")
                        return image_bytes

                    # Check for URL
                    elif "url" in image_item:
                        session = self.sessions[endpoint.name]
                        img_response = session.get(image_item["url"], timeout=30)
                        img_response.raise_for_status()
                        image_bytes = img_response.content
                        logger.info(f"✅ Image downloaded from {endpoint.name}! Size: {len(image_bytes)} bytes")
                        return image_bytes

                logger.error(f"Could not extract image data from {endpoint.name}")

            # Try next endpoint
            logger.warning(f"Endpoint {endpoint.name} failed for image generation, trying next...")
            self.current_endpoint_index = (self.current_endpoint_index + 1) % len(self.endpoints)

        logger.error("All endpoints failed for image generation")
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
        """Close all HTTP sessions."""
        for name, session in self.sessions.items():
            if session:
                try:
                    session.close()
                    logger.info(f"Closed session for endpoint: {name}")
                except Exception as e:
                    logger.error(f"Error closing session for {name}: {e}")
        self.sessions.clear()


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


def create_ai_client(endpoints: Optional[List[EndpointConfig]] = None,
                     access_key: Optional[str] = None,
                     base_url: Optional[str] = None,
                     model_chat: Optional[str] = None,
                     model_image: Optional[str] = None,
                     max_tokens: int = 400,
                     use_mock: bool = False,
                     enable_fallback: bool = True,
                     endpoint_cooldown: int = 300) -> Union[DOAIClient, MockDOAIClient]:
    """
    Factory function to create AI client with multi-endpoint support.

    Args:
        endpoints: List of endpoint configurations (if provided, other params are ignored)
        access_key: Primary endpoint access key (legacy support)
        base_url: Primary endpoint base URL (legacy support)
        model_chat: Chat model name (legacy support)
        model_image: Image model name (legacy support)
        max_tokens: Maximum tokens for responses
        use_mock: Whether to use mock client for testing
        enable_fallback: Whether to enable fallback responses when rate limited
        endpoint_cooldown: Cooldown period in seconds for rate-limited endpoints

    Returns:
        AI client instance
    """
    if use_mock:
        return MockDOAIClient(access_key or "mock", model_chat or "mock", model_image or "mock", max_tokens)

    # If endpoints list is provided, use it directly
    if endpoints:
        return DOAIClient(endpoints, max_tokens, enable_fallback, endpoint_cooldown)

    # Legacy support: create single endpoint from individual parameters
    if not access_key or not model_chat or not model_image:
        raise ValueError("Either 'endpoints' or all of (access_key, model_chat, model_image) must be provided")

    endpoint = EndpointConfig(
        base_url=base_url or "https://inference.do-ai.run/v1",
        access_key=access_key,
        model_chat=model_chat,
        model_image=model_image,
        name="primary"
    )

    return DOAIClient([endpoint], max_tokens, enable_fallback, endpoint_cooldown)

