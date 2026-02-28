from __future__ import annotations

from datetime import date
from typing import Any

from sqlmodel import SQLModel


class AlignmentCommitment(SQLModel):
    module: str
    commitment_id: str
    label: str
    context: dict[str, Any] | None = None


class AlignmentDailyResponse(SQLModel):
    date: date
    commitments: list[AlignmentCommitment]


class AlignmentCompletion(SQLModel):
    module: str
    commitment_id: str
    completed: bool
    context: dict[str, Any] | None = None


class AlignmentDailyRequest(SQLModel):
    date: date
    commitments_completed: list[AlignmentCompletion]


class AlignmentDailyResult(SQLModel):
    module: str
    status: str


class AlignmentDailyPostResponse(SQLModel):
    date: date
    results: list[AlignmentDailyResult]


class AlignmentWeeklyModuleSummary(SQLModel):
    module: str
    adherence_rate: float
    capacity_delta: float
    burnout_index: float | None
    constraint_mismatch_count: int
    exposure_density: float


class AlignmentWeeklySummaryResponse(SQLModel):
    week_start: date
    summaries: list[AlignmentWeeklyModuleSummary]


class AlignmentWeeklyAdjustment(SQLModel):
    module: str
    target_sessions: int | None = None
    priority_shift: str | None = None
    constraint_updates: dict[str, Any] | None = None


class AlignmentWeeklyMeetingRequest(SQLModel):
    week_start: date
    adjustments: list[AlignmentWeeklyAdjustment]


class AlignmentWeeklyMeetingResponse(SQLModel):
    week_start: date
    results: list[AlignmentDailyResult]


class AlignmentHistoryEntry(SQLModel):
    date: date
    commitments: list[str]
    reflection_status: str
    modules_affected: list[str]
    exposure_links: list[str]
    constraint_snapshot: dict


class AlignmentHistoryResponse(SQLModel):
    timeline: list[AlignmentHistoryEntry]
