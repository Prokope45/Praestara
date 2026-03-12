from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GlobalConstraintState:
    total_time_budget: float
    energy_state: float
    stress_index: float
    cognitive_load_index: float
