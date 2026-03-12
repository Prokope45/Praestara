from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class GrowthModule(ABC):
    # --- Core mathematical structure ---
    @abstractmethod
    def capacity_vector(self, state: Any) -> dict:
        raise NotImplementedError

    @abstractmethod
    def ceiling_vector(self, state: Any) -> dict:
        raise NotImplementedError

    @abstractmethod
    def stress_budget(self, state: Any, constraints: Any) -> dict:
        raise NotImplementedError

    @abstractmethod
    def subschema_modulators(self, state: Any, context: Any) -> dict:
        raise NotImplementedError

    @abstractmethod
    def interference_factor(self, state: Any, allocation: Any) -> float:
        raise NotImplementedError

    @abstractmethod
    def adherence_gate(self, reflection_data: Any) -> float:
        raise NotImplementedError

    @abstractmethod
    def degradation_ladder(self, state: Any, constraints: Any) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def update_state(self, state: Any, execution_data: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def project_trajectory(self, state: Any, weeks: int) -> Any:
        raise NotImplementedError

    # --- Alignment layer integration ---
    @abstractmethod
    def daily_commitments(self, state: Any) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def reflect(self, state: Any, reflection_input: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def realign(self, state: Any, weekly_input: Any) -> Any:
        raise NotImplementedError

    # --- Existing operational surface ---
    @abstractmethod
    def project(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    @abstractmethod
    def build_execution(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError
