"""ExportBuilder — assembles signed BehavioralExportPacks from raw Praestara data.

Applies the export filtering policy, pseudonymizes the subject, signs the pack,
and produces a tamper-evident envelope ready for transport to Synergen.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Set, Union

from .key_derivation import KeyDerivation
from .pseudonymizer import Pseudonymizer
from .schemas import (
    BehavioralExportPack,
    ExportPolicy,
    Observation,
    SensitivityClass,
    TrajectoryWindow,
    TriggerReason,
    UrgencyLevel,
    VariableGroup,
)


class ExportBuilder:
    """Builds signed, policy-filtered BehavioralExportPacks.

    Usage:
        kd = KeyDerivation(root_secret)
        builder = ExportBuilder(kd, tenant_id="...", policy=ExportPolicy())
        pack = builder.build_pack(
            user_uuid="...",
            variable_groups=[...],
            trajectory_window=TrajectoryWindow(start=..., end=...),
        )
    """

    def __init__(
        self,
        kd: KeyDerivation,
        tenant_id: str,
        policy: Optional[ExportPolicy] = None,
        rare_concepts: Optional[Set[str]] = None,
    ) -> None:
        self._kd = kd
        self._tenant_id = tenant_id
        self._pseudonymizer = Pseudonymizer(kd, tenant_id)
        self._policy = policy or ExportPolicy()
        self._rare_concepts = rare_concepts or set()

    @property
    def policy(self) -> ExportPolicy:
        return self._policy

    def build_pack(
        self,
        user_uuid: str,
        variable_groups: List[VariableGroup],
        trajectory_window: TrajectoryWindow,
        missingness_map: Optional[Dict[str, str]] = None,
        urgency_level: Optional[UrgencyLevel] = None,
        trigger_reason: Optional[TriggerReason] = None,
    ) -> BehavioralExportPack:
        """Build a complete, signed export pack for one subject."""
        pseudonym_id, pseudonym_version = self._pseudonymizer.pseudonymize(user_uuid)

        filtered_groups = self._apply_policy(variable_groups, trajectory_window)

        pack = BehavioralExportPack(
            pseudonym_id=pseudonym_id,
            pseudonym_version=pseudonym_version,
            tenant_id=self._tenant_id,
            variable_groups=filtered_groups,
            trajectory_window=trajectory_window,
            missingness_map=missingness_map or {},
            urgency_level=urgency_level,
            trigger_reason=trigger_reason,
        )

        pack.export_hash = pack.compute_export_hash()

        keys = self._kd.derive(self._tenant_id)
        pack.signature = self._sign(keys.signing_key, pack.canonical_json())
        pack.signature_key_version = keys.version

        return pack

    def _apply_policy(
        self,
        groups: List[VariableGroup],
        window: TrajectoryWindow,
    ) -> List[VariableGroup]:
        """Filter variable groups and observations per export policy."""
        policy = self._policy

        cutoff_start = window.end - timedelta(days=policy.max_time_window_days)
        effective_start = max(window.start, cutoff_start)

        filtered: List[VariableGroup] = []
        for group in groups:
            if group.group_id not in policy.allowed_groups:
                continue

            obs: List[Observation] = []
            for o in group.observations:
                if not policy.allows_sensitivity(o.sensitivity_class):
                    continue
                if o.sensitivity_class == SensitivityClass.PRIVATE:
                    continue
                if o.certainty < policy.min_confidence:
                    continue
                if o.timestamp < effective_start or o.timestamp > window.end:
                    continue
                if o.concept_id in self._rare_concepts:
                    continue
                obs.append(o)

            if obs:
                filtered.append(VariableGroup(group_id=group.group_id, observations=obs))

        return filtered

    @staticmethod
    def _sign(signing_key: bytes, canonical_json: str) -> str:
        """HMAC-SHA256 signature over canonical JSON."""
        return hmac.new(
            signing_key,
            canonical_json.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def verify_signature(self, pack: BehavioralExportPack) -> bool:
        """Verify the HMAC signature on a pack. Used for testing."""
        keys = self._kd.derive(self._tenant_id, version=pack.signature_key_version)
        expected = self._sign(keys.signing_key, pack.canonical_json())
        return hmac.compare_digest(expected, pack.signature)
