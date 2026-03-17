"""Encryption utility for the AI Service API.

Uses AES-256-GCM for authenticated encryption.
"""

import base64
import json
import os
import logging
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings

logger = logging.getLogger(__name__)


class KoiosEncryption:
    """Utility class for encrypting and decrypting data for AI service communication."""

    @staticmethod
    def _get_aes_gcm() -> AESGCM:
        """Initialize AESGCM with the configured encryption key."""
        key_hex = settings.AI_ENCRYPTION_KEY
        if not key_hex:
            logger.error("AI_ENCRYPTION_KEY is not set.")
            raise ValueError("AI_ENCRYPTION_KEY not set in environment.")

        try:
            key = bytes.fromhex(key_hex)
        except ValueError:
            logger.error("AI_ENCRYPTION_KEY is not a valid hex string.")
            raise ValueError("AI_ENCRYPTION_KEY must be a valid hex string.")

        if len(key) != 32:
            logger.error("AI_ENCRYPTION_KEY must be 32 bytes (64 hex characters).")
            raise ValueError("AI_ENCRYPTION_KEY must be 32 bytes.")

        return AESGCM(key)

    @classmethod
    def encrypt(cls, data: dict[str, Any] | str) -> str:
        """Encrypt a dictionary or string into a base64-encoded string.

        The output format is: base64(nonce + ciphertext + tag)

        Args:
            data: Dictionary or string to encrypt.

        Returns:
            Base64-encoded encrypted string.
        """
        aesgcm = cls._get_aes_gcm()
        nonce = os.urandom(12)  # GCM recommended nonce size

        if isinstance(data, str):
            data_json = data.encode("utf-8")
        else:
            data_json = json.dumps(data).encode("utf-8")

        # AESGCM.encrypt returns ciphertext + tag
        ciphertext_with_tag = aesgcm.encrypt(nonce, data_json, None)

        # Combine nonce and ciphertext+tag for storage/transmission
        combined = nonce + ciphertext_with_tag
        return base64.b64encode(combined).decode("utf-8")

    @classmethod
    def decrypt(cls, encrypted_str: str) -> dict[str, Any] | str:
        """Decrypt a base64-encoded string into a dictionary or string.

        Args:
            encrypted_str: Base64-encoded encrypted string.

        Returns:
            Decrypted dictionary or string.

        Raises:
            ValueError: If decryption fails.
        """
        aesgcm = cls._get_aes_gcm()
        try:
            combined = base64.b64decode(encrypted_str)
            if len(combined) < 12:
                raise ValueError("Invalid encrypted data: too short.")

            nonce = combined[:12]
            ciphertext_with_tag = combined[12:]

            decrypted_data = aesgcm.decrypt(nonce, ciphertext_with_tag, None)
            decoded = decrypted_data.decode("utf-8")

            # Try to parse as JSON, return string if it fails
            try:
                result = json.loads(decoded)
                if isinstance(result, dict):
                    return result
                return decoded
            except json.JSONDecodeError:
                return decoded
        except Exception as e:
            logger.error("Decryption failed: %s", e)
            raise ValueError("Decryption failed. Invalid data or key.") from e
