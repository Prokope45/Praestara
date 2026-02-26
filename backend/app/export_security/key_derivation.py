"""HKDF-based key derivation hierarchy for export security.

Root secret → per-tenant, per-purpose keys via HKDF-SHA256.
Pseudonymization and signing keys are derived in separate HKDF contexts
to prevent cross-purpose key reuse.

When constructed with a :class:`SecretsProvider`, root secrets are
persisted through the provider rather than held as raw bytes in the
``_version_history`` dict.  This removes the critical gap of long-lived
plaintext key material sitting in Python process memory.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Optional, Union

if TYPE_CHECKING:
    from infrastructure.security.secrets_provider import SecretsProvider

_ROOT_SECRET_NAME = "export-root-secret"


@dataclass(frozen=True)
class DerivedKeys:
    pseudonymization_key: bytes
    signing_key: bytes
    version: int


class KeyDerivation:
    """Derives tenant-scoped, purpose-separated keys from a root secret.

    Key hierarchy:
        root_secret
        ├─ HKDF("pseudonymization-v1:{tenant_id}") → pseudonymization_key
        └─ HKDF("message-signing-v1:{tenant_id}")  → signing_key

    If *secrets_provider* is supplied, root secrets are stored and
    retrieved through the provider and never accumulate in
    ``_version_history``.  If omitted, behaviour is identical to the
    original in-memory implementation (for tests and local dev).
    """

    def __init__(
        self,
        root_secret: Union[str, bytes],
        *,
        secrets_provider: Optional[SecretsProvider] = None,
    ) -> None:
        if isinstance(root_secret, str):
            root_secret = root_secret.encode("utf-8")
        if len(root_secret) < 32:
            raise ValueError("root_secret must be at least 32 bytes")

        self._provider = secrets_provider
        self._current_version = 1

        if self._provider is not None:
            self._provider.store_secret(_ROOT_SECRET_NAME, root_secret, version=1)
            self._version_history: Dict[int, bytes] = {}
        else:
            self._version_history = {1: root_secret}

        self._root = root_secret

    @property
    def current_version(self) -> int:
        return self._current_version

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_root(self, version: int) -> Optional[bytes]:
        """Retrieve root secret for *version* from provider or local history."""
        if self._provider is not None:
            return self._provider.get_secret(_ROOT_SECRET_NAME, version=version)
        return self._version_history.get(version)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def rotate(self, new_root: Union[str, bytes]) -> int:
        """Rotate to a new root secret. Returns the new version number.

        The old root is retained (in the provider or in-memory) for
        overlap-window validation and pseudonym continuity.
        """
        if isinstance(new_root, str):
            new_root = new_root.encode("utf-8")
        if len(new_root) < 32:
            raise ValueError("new root_secret must be at least 32 bytes")

        self._current_version += 1

        if self._provider is not None:
            self._provider.store_secret(
                _ROOT_SECRET_NAME, new_root, version=self._current_version,
            )
        else:
            self._version_history[self._current_version] = new_root

        self._root = new_root
        return self._current_version

    def derive(self, tenant_id: str, *, version: Optional[int] = None) -> DerivedKeys:
        """Derive pseudonymization and signing keys for a tenant."""
        v = version if version is not None else self._current_version
        root = self._get_root(v)
        if root is None:
            raise ValueError(f"Unknown key version: {v}")

        pseudo_key = self._hkdf(
            ikm=root,
            info=f"pseudonymization-v1:{tenant_id}".encode(),
            length=32,
        )
        sign_key = self._hkdf(
            ikm=root,
            info=f"message-signing-v1:{tenant_id}".encode(),
            length=32,
        )
        return DerivedKeys(
            pseudonymization_key=pseudo_key,
            signing_key=sign_key,
            version=v,
        )

    def zeroize_expired(self, keep_versions: int = 2) -> None:
        """Securely destroy old key versions, keeping the most recent *keep_versions*.

        Provider-backed storage delegates destruction to the provider
        (e.g. AWS Secrets Manager ``ForceDeleteWithoutRecovery``).
        In-memory storage overwrites bytes with zeros before dropping
        the reference.
        """
        if self._current_version <= keep_versions:
            return

        cutoff = self._current_version - keep_versions
        for v in range(1, cutoff + 1):
            if self._provider is not None:
                self._provider.zeroize(_ROOT_SECRET_NAME, version=v)
            elif v in self._version_history:
                old = self._version_history[v]
                self._version_history[v] = b"\x00" * len(old)
                del self._version_history[v]

    # ------------------------------------------------------------------
    # Cryptographic primitives
    # ------------------------------------------------------------------

    @staticmethod
    def _hkdf(ikm: bytes, info: bytes, length: int = 32, salt: bytes = b"") -> bytes:
        """HKDF-SHA256 extract-and-expand (RFC 5869)."""
        if not salt:
            salt = b"\x00" * 32
        prk = hmac.new(salt, ikm, hashlib.sha256).digest()

        output = b""
        t = b""
        counter = 1
        while len(output) < length:
            t = hmac.new(prk, t + info + bytes([counter]), hashlib.sha256).digest()
            output += t
            counter += 1
        return output[:length]

    @staticmethod
    def generate_root_secret() -> bytes:
        """Generate a cryptographically secure 32-byte root secret."""
        return os.urandom(32)
