"""BehavioralExportPack v1.0 and related schemas.

These schemas define the data contract for cross-system behavioral health
data flow. All fields are designed to prevent identity leakage:
- Timestamps are day-level only
- No free text crosses the boundary
- Sensitivity-classified observations are filtered by export policy
"""
from __future__ import annotations

import hashlib
import json
import uuid as _uuid
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

try:
    from infrastructure.security.canonical_json_spec import canonicalize as _canonicalize
except ImportError:
    import os as _os
    import sys as _sys
    # schemas.py is at praestara/backend/app/export_security/ — 4 dirs up to Strios root
    _strios_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", "..", "..", ".."))
    if _strios_root not in _sys.path:
        _sys.path.insert(0, _strios_root)
    try:
        from infrastructure.security.canonical_json_spec import canonicalize as _canonicalize
    except ImportError:
        # Final fallback: inline implementation matching the spec exactly
        import math as _math
        def _normalize(v):
            if isinstance(v, dict):
                return {k: _normalize(val) for k, val in v.items()}
            if isinstance(v, list):
                return [_normalize(i) for i in v]
            if isinstance(v, float):
                if _math.isnan(v) or _math.isinf(v):
                    raise ValueError(f"Cannot canonicalize non-finite float: {v}")
                return round(v, 6)
            return v
        def _canonicalize(data):
            import json as _json
            return _json.dumps(_normalize(data), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


class SensitivityClass(str, Enum):
    CLINICAL = "clinical"
    OPERATIONAL = "operational"
    SAFE_AGGREGATE = "safe_aggregate"
    PRIVATE = "private"


class VariableGroupID(str, Enum):
    NUTRITION = "nutrition"
    PSYCHOLOGICAL = "psychological"
    EXERCISE = "exercise"
    SLEEP = "sleep"
    ADHERENCE = "adherence"
    SUBSTANCE_USE = "substance_use"
    SOCIAL = "social"
    COGNITIVE = "cognitive"
    RECOVERY = "recovery"


class Observation(BaseModel):
    concept_id: str
    value: Union[float, str, bool]
    unit: Optional[str] = None
    timestamp: date = Field(description="Day-level only, no sub-day precision")
    certainty: float = Field(ge=0.0, le=1.0)
    sensitivity_class: SensitivityClass

    @field_validator("timestamp", mode="before")
    @classmethod
    def coerce_to_date(cls, v: Any) -> date:
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            return date.fromisoformat(v[:10])
        return v


class VariableGroup(BaseModel):
    group_id: str
    observations: List[Observation] = []


class TrajectoryWindow(BaseModel):
    start: date
    end: date


class UrgencyLevel(str, Enum):
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


class TriggerReason(str, Enum):
    SCORE_THRESHOLD_BREACH = "score_threshold_breach"
    TRAJECTORY_DETERIORATION = "trajectory_deterioration"
    ADHERENCE_COLLAPSE = "adherence_collapse"


class ExportPolicy(BaseModel):
    """Tenant-configurable export filtering policy.

    Applied before any data enters the BehavioralExportPack.
    Cannot weaken the hard minimums defined here.
    """
    allowed_groups: List[str] = Field(
        default_factory=lambda: [g.value for g in VariableGroupID]
    )
    max_time_window_days: int = Field(default=30, ge=1, le=365)
    sensitivity_class_threshold: SensitivityClass = SensitivityClass.CLINICAL
    min_confidence: float = Field(default=0.6, ge=0.0, le=1.0)
    timestamp_resolution: str = "day"
    free_text: str = "strip"
    location_signals: str = "strip"
    rare_concept_suppression_threshold: int = Field(
        default=5, ge=1,
        description="Suppress concept_id values seen in fewer than this many subjects per tenant"
    )

    _SENSITIVITY_ORDER = {
        SensitivityClass.SAFE_AGGREGATE: 0,
        SensitivityClass.OPERATIONAL: 1,
        SensitivityClass.CLINICAL: 2,
        SensitivityClass.PRIVATE: 3,
    }

    def allows_sensitivity(self, cls: SensitivityClass) -> bool:
        threshold = self._SENSITIVITY_ORDER.get(self.sensitivity_class_threshold, 2)
        level = self._SENSITIVITY_ORDER.get(cls, 3)
        return level <= threshold


class BehavioralExportPack(BaseModel):
    """v1.0 — Pseudonymized behavioral health data export.

    This is the sole data contract for Praestara → Synergen communication.
    Identity is pseudonymized. No PII fields. Day-level timestamps only.
    """
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    pseudonym_id: str
    pseudonym_version: int
    tenant_id: str = Field(description="Opaque UUID, never human-readable")
    variable_groups: List[VariableGroup]
    trajectory_window: TrajectoryWindow
    missingness_map: Dict[str, str] = Field(default_factory=dict)
    export_nonce: str = Field(default_factory=lambda: str(_uuid.uuid4()))
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    export_hash: str = ""
    signature: str = ""
    signature_key_version: int = 0

    # Urgent escalation (optional — present only for urgent path)
    urgency_level: Optional[UrgencyLevel] = None
    trigger_reason: Optional[TriggerReason] = None

    def canonical_json(self) -> str:
        """Canonical JSON for signature and hash computation.

        Excludes signature, export_hash, and signature_key_version.
        Delegates to the shared canonical JSON spec so Praestara and Synergen
        always produce byte-identical output.
        """
        data = self.model_dump(mode="json")
        for key in ("signature", "export_hash", "signature_key_version"):
            data.pop(key, None)
        return _canonicalize(data)

    def compute_export_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


class UrgentEscalation(BaseModel):
    """Convenience wrapper for constructing urgent-path packs."""
    urgency_level: UrgencyLevel
    trigger_reason: TriggerReason
