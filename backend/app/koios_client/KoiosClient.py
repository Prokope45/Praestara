"""AI Service client for communicating with the Koios RAG API.

Handles JWT token management, encryption, and API communication.
"""

import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.koios_client.KoiosEncryption import KoiosEncryption
from app.core.config import settings

logger = logging.getLogger(__name__)


class KoiosClient:
    """Client for communicating with the AI (Koios RAG) service.

    Handles:
    - JWT token acquisition and caching
    - Request/response encryption
    - Automatic token refresh on expiration
    """

    _instance: "KoiosClient | None" = None
    _lock: threading.Lock = threading.Lock()
    _token: str | None = None
    _token_expiry: datetime | None = None

    def __new__(cls) -> "KoiosClient":
        """Singleton pattern to ensure single instance across the application."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._token = None
                    cls._instance._token_expiry = None
        return cls._instance

    @property
    def base_url(self) -> str:
        """Get the base URL for the AI API."""
        if not settings.AI_API_URL:
            raise ValueError("AI_API_URL is not configured")
        return str(settings.AI_API_URL).rstrip("/")

    @property
    def is_configured(self) -> bool:
        """Check if the AI service is properly configured."""
        return bool(settings.AI_API_URL and settings.AI_ENCRYPTION_KEY)

    def _get_token(self, user_id: str) -> str:
        """Obtain a JWT token from the AI service.

        Args:
            user_id: The user identifier to include in the token request.

        Returns:
            JWT token string.

        Raises:
            HTTPError: If the token request fails.
        """
        url = f"{self.base_url}/token"
        headers = {"X-User-ID": user_id}

        with httpx.Client(timeout=settings.AI_TIMEOUT_SECONDS) as client:
            response = client.post(url, headers=headers)
            response.raise_for_status()
            data = response.json()

        token = data.get("access_token")
        if not token:
            raise ValueError("No access_token in response")

        self._token = str(token)
        # Set a buffer for token expiry (refresh 5 minutes before actual expiry)
        self._token_expiry = datetime.now(timezone.utc) + timedelta(
            minutes=55  # Assume 1-hour tokens, refresh early
        )

        logger.info("Successfully obtained AI service token for user %s", user_id)
        return str(token)

    def _get_valid_token(self, user_id: str) -> str:
        """Get a valid JWT token, refreshing if necessary.

        Args:
            user_id: The user identifier.

        Returns:
            Valid JWT token string.
        """
        now = datetime.now(timezone.utc)

        # Check if we have a valid cached token
        if self._token and self._token_expiry and self._token_expiry > now:
            return str(self._token)

        # Need to fetch a new token
        return self._get_token(user_id)

    def _encrypt_user_id(self, user_id: str) -> str:
        """Encrypt the user ID for the X-User-ID header.

        Args:
            user_id: The user identifier to encrypt.

        Returns:
            Encrypted user ID string.
        """
        if settings.AI_ENABLE_ENCRYPTION:
            return KoiosEncryption.encrypt(user_id)
        return user_id

    def _build_query_request(self, query: str, temperature: float = 0.5) -> dict[str, Any]:
        """Build a query request payload.

        Args:
            query: The user's query text.
            temperature: Model temperature for generation.

        Returns:
            Request payload dictionary.
        """
        request_data = {
            "query": query,
            "temperature": temperature,
            "enable_internet_search": False,
        }

        if settings.AI_ENABLE_ENCRYPTION:
            return {"encrypted_data": KoiosEncryption.encrypt(request_data)}

        return request_data

    def _build_analyze_request(self, prompt: str, details: list[dict[str, Any]], model: str | None = None, temperature: float | None = 0.5) -> dict[str, Any]:
        """Build an analysis request payload.

        Args:
            prompt: The general prompt for the AI.
            details: List of details/metrics.
            model: Optional model to use.
            temperature: Model temperature.

        Returns:
            Request payload dictionary.
        """
        request_data: dict[str, Any] = {
            "prompt": prompt,
            "details": details,
        }
        if model is not None:
            request_data["model"] = model
        if temperature is not None:
            request_data["temperature"] = temperature

        if settings.AI_ENABLE_ENCRYPTION:
            return {"encrypted_data": KoiosEncryption.encrypt(request_data)}

        return request_data

    def _decrypt_response(self, response_data: dict[str, Any]) -> dict[str, Any]:
        """Decrypt the response from the AI service if needed.

        Args:
            response_data: Raw response data from the API.

        Returns:
            Decrypted response dictionary.
        """
        if settings.AI_ENABLE_ENCRYPTION and "encrypted_data" in response_data:
            decrypted = KoiosEncryption.decrypt(response_data["encrypted_data"])
            if isinstance(decrypted, dict):
                return decrypted
            raise ValueError("Expected decrypted response to be a dictionary")

        return response_data

    def process_query(
        self,
        user_id: str,
        query: str,
        temperature: float = 0.5,
        retry_count: int = 1,
    ) -> str:
        """Process a query through the AI service.

        Args:
            user_id: The user's identifier.
            query: The query text to process.
            temperature: Model temperature for generation.
            retry_count: Number of retries on token expiration.

        Returns:
            The generated response text.

        Raises:
            HTTPError: If the API request fails.
            ValueError: If the response is invalid.
        """
        if not self.is_configured:
            raise ValueError("AI service is not properly configured")

        # Encrypt user ID for header
        encrypted_user_id = self._encrypt_user_id(user_id)

        # Get valid token
        token = self._get_valid_token(encrypted_user_id)

        # Build request
        request_body = self._build_query_request(query, temperature)

        # Make request
        url = f"{self.base_url}/query"
        headers = {
            "Authorization": f"Bearer {token}",
            "X-User-ID": encrypted_user_id,
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=settings.AI_TIMEOUT_SECONDS) as client:
                response = client.post(url, json=request_body, headers=headers)

                # Handle token expiration
                if response.status_code == 401 and retry_count > 0:
                    logger.info("Token expired, refreshing...")
                    self._token = None
                    self._token_expiry = None
                    return self.process_query(user_id, query, temperature, retry_count - 1)

                response.raise_for_status()

        except httpx.HTTPError as e:
            logger.error("AI service request failed: %s", e)
            raise

        # Parse and decrypt response
        response_data = response.json()
        decrypted_response = self._decrypt_response(response_data)

        generation = decrypted_response.get("generation")
        if not generation:
            raise ValueError("No generation in AI service response")

        return str(generation)

    def process_analysis(
        self,
        user_id: str,
        prompt: str,
        details: list[dict[str, Any]],
        model: str | None = None,
        temperature: float | None = 0.5,
        retry_count: int = 1,
    ) -> str:
        """Process an analysis query through the AI service.

        Args:
            user_id: The user's identifier.
            prompt: The general prompt for the AI.
            details: List of details/metrics.
            model: Optional model to use.
            temperature: Model temperature.
            retry_count: Number of retries on token expiration.

        Returns:
            The generated answer text.

        Raises:
            HTTPError: If the API request fails.
            ValueError: If the response is invalid.
        """
        if not self.is_configured:
            raise ValueError("AI service is not properly configured")

        # Encrypt user ID for header
        encrypted_user_id = self._encrypt_user_id(user_id)

        # Get valid token
        token = self._get_valid_token(encrypted_user_id)

        # Build request
        request_body = self._build_analyze_request(prompt, details, model, temperature)

        # Make request
        url = f"{self.base_url}/analyze"
        headers = {
            "Authorization": f"Bearer {token}",
            "X-User-ID": encrypted_user_id,
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=settings.AI_TIMEOUT_SECONDS) as client:
                response = client.post(url, json=request_body, headers=headers)

                # Handle token expiration
                if response.status_code == 401 and retry_count > 0:
                    logger.info("Token expired, refreshing...")
                    self._token = None
                    self._token_expiry = None
                    return self.process_analysis(
                        user_id, prompt, details, model, temperature, retry_count - 1
                    )

                response.raise_for_status()

        except httpx.HTTPError as e:
            logger.error("AI service analyze request failed: %s", e)
            raise

        # Parse and decrypt response
        response_data = response.json()
        decrypted_response = self._decrypt_response(response_data)

        answer = decrypted_response.get("answer") or decrypted_response.get("generation")
        if not answer:
            raise ValueError("No answer or generation in AI service response")

        return str(answer)

    def get_history(self, user_id: str, retry_count: int = 1) -> list[dict[str, str]]:
        """Get the chat history for a user from the AI service.

        Args:
            user_id: The user's identifier.
            retry_count: Number of retries on token expiration.

        Returns:
            List of chat messages with 'role' and 'content' keys.

        Raises:
            HTTPError: If the API request fails.
            ValueError: If the response is invalid.
        """
        if not self.is_configured:
            raise ValueError("AI service is not properly configured")

        # Encrypt user ID for header
        encrypted_user_id = self._encrypt_user_id(user_id)

        # Get valid token
        token = self._get_valid_token(encrypted_user_id)

        # Make request
        url = f"{self.base_url}/history"
        headers = {
            "Authorization": f"Bearer {token}",
            "X-User-ID": encrypted_user_id,
        }

        try:
            with httpx.Client(timeout=settings.AI_TIMEOUT_SECONDS) as client:
                response = client.get(url, headers=headers)

                # Handle token expiration
                if response.status_code == 401 and retry_count > 0:
                    logger.info("Token expired, refreshing...")
                    self._token = None
                    self._token_expiry = None
                    return self.get_history(user_id, retry_count - 1)

                response.raise_for_status()

        except httpx.HTTPError as e:
            logger.error("AI service history request failed: %s", e)
            raise

        # Parse and decrypt response
        response_data = response.json()
        decrypted_response = self._decrypt_response(response_data)

        history = decrypted_response.get("history", [])
        if not isinstance(history, list):
            raise ValueError("Expected history to be a list")

        return history

    def clear_history(self, user_id: str, retry_count: int = 1) -> int:
        """Clear the chat history for a user from the AI service.

        Args:
            user_id: The user's identifier.
            retry_count: Number of retries on token expiration.

        Returns:
            Number of messages deleted.

        Raises:
            HTTPError: If the API request fails.
            ValueError: If the response is invalid.
        """
        if not self.is_configured:
            raise ValueError("AI service is not properly configured")

        # Encrypt user ID for header
        encrypted_user_id = self._encrypt_user_id(user_id)

        # Get valid token
        token = self._get_valid_token(encrypted_user_id)

        # Make request
        url = f"{self.base_url}/history"
        headers = {
            "Authorization": f"Bearer {token}",
            "X-User-ID": encrypted_user_id,
        }

        try:
            with httpx.Client(timeout=settings.AI_TIMEOUT_SECONDS) as client:
                response = client.delete(url, headers=headers)

                # Handle token expiration
                if response.status_code == 401 and retry_count > 0:
                    logger.info("Token expired, refreshing...")
                    self._token = None
                    self._token_expiry = None
                    return self.clear_history(user_id, retry_count - 1)

                response.raise_for_status()

        except httpx.HTTPError as e:
            logger.error("AI service clear history request failed: %s", e)
            raise

        # Parse and decrypt response
        response_data = response.json()
        decrypted_response = self._decrypt_response(response_data)

        messages_deleted = decrypted_response.get("messages_deleted", 0)
        return int(messages_deleted)

    def rephrase_trajectory_goal(self, user_id: str, goal: str) -> str:
        """Rephrase a trajectory goal into morning and evening yes/no questions.
        
        Args:
            user_id: The user's identifier.
            goal: The original goal text.
            
        Returns:
            A JSON string containing the rephrased questions.
        """
        prompt = (
            "You are a helpful assistant. Rephrase the following goal into two "
            "short, actionable yes/no questions. One for a morning check-in (e.g. 'Will you...', 'Do you plan to...') "
            "and one for an evening check-in (e.g. 'Did you...', 'Were you...'). "
            "Respond ONLY with a valid JSON object in the following format: "
            '{"morning_question": "...", "evening_question": "..."}'
        )
        details = [
            {"key": "goal", "value": goal, "description": "The goal to rephrase"}
        ]
        return self.process_analysis(user_id=user_id, prompt=prompt, details=details, temperature=0.3)

    def brainstorm_trajectory(self, user_id: str, message: str) -> str:
        """Help the user brainstorm trajectory goals.
        
        Args:
            user_id: The user's identifier.
            message: The user's message.
            
        Returns:
            The AI's response.
        """
        prompt = (
            "You are Praestara. Help the user brainstorm actionable, yes/no trajectory goals "
            "to work on over the next week. Keep it brief, non-moralizing, and supportive."
        )
        details = [
            {"key": "user_message", "value": message, "description": "User's request or idea"}
        ]
        return self.process_analysis(user_id=user_id, prompt=prompt, details=details, temperature=0.7)

    def clear_token(self) -> None:
        """Clear the cached token (useful for testing or forced refresh)."""
        self._token = None
        self._token_expiry = None


# Singleton instance for easy import
ai_client = KoiosClient()
