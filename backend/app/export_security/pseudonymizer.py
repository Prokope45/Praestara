"""Pseudonymization via HMAC-SHA256 with versioned, longitudinally stable identities.

Praestara owns identity. Raw user UUIDs never leave this process.
Pseudonyms are deterministic per (key_version, user_uuid) pair so Synergen
can maintain longitudinal trajectory continuity.
"""
from __future__ import annotations

import hmac
import hashlib
from typing import Dict, Optional, Tuple

from .key_derivation import KeyDerivation


class Pseudonymizer:
    """Produces stable, versioned pseudonym IDs from user UUIDs.

    On key rotation, the overlap window allows Synergen to correlate old and
    new pseudonyms via temporal matching — no explicit migration events are
    sent externally.
    """

    def __init__(self, kd: KeyDerivation, tenant_id: str) -> None:
        self._kd = kd
        self._tenant_id = tenant_id

    @property
    def current_version(self) -> int:
        return self._kd.current_version

    def pseudonymize(self, user_uuid: str, *, version: Optional[int] = None) -> Tuple[str, int]:
        """Return (pseudonym_id, pseudonym_version) for a user.

        The pseudonym is deterministic: same (version, user_uuid) always
        produces the same output, enabling longitudinal tracking.
        """
        v = version if version is not None else self._kd.current_version
        keys = self._kd.derive(self._tenant_id, version=v)
        digest = hmac.new(
            keys.pseudonymization_key,
            user_uuid.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return digest, v

    def overlap_pseudonyms(self, user_uuid: str) -> Dict[int, str]:
        """Return pseudonyms for all active key versions (overlap window).

        During key rotation, both the old and new versions are active.
        Synergen uses the temporal overlap of trajectory windows to match
        the old pseudonym to the new one without receiving an explicit
        migration event.
        """
        results: Dict[int, str] = {}
        for v in range(max(1, self._kd.current_version - 1), self._kd.current_version + 1):
            try:
                pid, _ = self.pseudonymize(user_uuid, version=v)
                results[v] = pid
            except ValueError:
                continue
        return results
