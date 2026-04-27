from datetime import datetime
import uuid

import sqlalchemy as sa
from pydantic import ConfigDict
from sqlmodel import Column, Field, SQLModel


class BeSciTextSample(SQLModel):
    text: str
    occurred_at: datetime | None = None
    source: str | None = None


class BeSciLatentState(SQLModel):
    arousal: float
    valence: float
    control: float
    volatility: float
    social_orientation: float
    reward_seeking: float
    cognitive_flexibility: float
    self_focus: float


class BeSciSignal(SQLModel):
    name: str
    score: float
    rationale: str


class BeSciEvidence(SQLModel):
    name: str
    summary: str
    matches: list[str]


class BeSciDomainAnalysis(SQLModel):
    domain: str
    matched_terms: list[str]
    sample_count: int
    current_state: BeSciLatentState
    trajectory_score: float
    summary: str
    higher_order_factors: list[BeSciSignal] = []


class BeSciAlignmentSignal(SQLModel):
    name: str
    score: float
    rationale: str
    related_domains: list[str] = []


class BeSciFeatureSummary(SQLModel):
    lexical_density: float
    semantic_density: float
    temporal_balance: float
    token_count: int
    calibration_confidence: float
    contextual_richness: float = 0.0
    signal_coverage: float = 0.0


class BeSciNarrativeBlock(SQLModel):
    lens: str
    title: str
    body: str


class BeSciTrajectoryAnalysis(SQLModel):
    model_config = ConfigDict(protected_namespaces=())
    sample_count: int
    model_version: str = "besci-v4.6-besci4-grounded"
    representation_backend: str = "hybrid-anchor-covariance-neurocomp-v4_6"
    summary_backend: str = "deterministic_template"
    instant_state: BeSciLatentState
    calibrated_state: BeSciLatentState
    current_state: BeSciLatentState
    baseline_state: BeSciLatentState
    recent_state: BeSciLatentState
    change_from_baseline: BeSciLatentState
    change_from_recent: BeSciLatentState
    trajectory_score: float
    summary: str
    current_state_summary: str = ""
    temporal_scope: str = "untimed_sequence"
    total_summary: str = ""
    narrative_blocks: list[BeSciNarrativeBlock] = []
    signals: list[BeSciSignal]
    dimension_signals: list[BeSciSignal] = []
    process_signals: list[BeSciSignal] = []
    computational_axes: list[BeSciSignal] = []
    higher_order_factors: list[BeSciSignal] = []
    domain_analyses: list[BeSciDomainAnalysis] = []
    alignment_signals: list[BeSciAlignmentSignal] = []
    evidence: list[BeSciEvidence] = []
    feature_summary: BeSciFeatureSummary | None = None


class BeSciAnalyzeRequest(SQLModel):
    samples: list[BeSciTextSample]


class BeSciAnalyzeResponse(SQLModel):
    analysis: BeSciTrajectoryAnalysis


class BeSciSnapshot(SQLModel, table=True):
    __tablename__ = "besci_snapshot"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, index=True)
    sample_count: int = Field(default=0)
    checkin_sample_count: int = Field(default=0)
    chat_sample_count: int = Field(default=0)
    trajectory_score: float = Field(ge=-1.0, le=1.0)
    current_state: dict = Field(sa_column=Column(sa.JSON, nullable=False))
    baseline_state: dict = Field(sa_column=Column(sa.JSON, nullable=False))
    change_from_baseline: dict = Field(sa_column=Column(sa.JSON, nullable=False))
    summary: str = Field(sa_column=Column(sa.Text, nullable=False))
    signals: list[dict] = Field(sa_column=Column(sa.JSON, nullable=False))
    computed_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class BeSciSnapshotPublic(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    sample_count: int
    checkin_sample_count: int
    chat_sample_count: int
    trajectory_score: float
    current_state: dict
    baseline_state: dict
    change_from_baseline: dict
    summary: str
    signals: list[dict]
    computed_at: datetime


class BeSciHistoryPublic(SQLModel):
    data: list[BeSciSnapshotPublic]
    count: int
