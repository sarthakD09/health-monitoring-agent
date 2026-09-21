from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DataSource(str, Enum):
    LIVE = "live"
    REPLAY = "replay"
    SCENARIO = "scenario"


class Action(str, Enum):
    MONITOR = "monitor"
    RECHECK = "recheck"
    ESCALATE = "escalate"


class Observation(BaseModel):
    timestamp: datetime
    subject_id: str
    source: DataSource
    heart_rate: float | None = None
    spo2: float | None = None
    temperature: float | None = None
    activity: str | None = None
    signal_quality: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Baseline(BaseModel):
    subject_id: str
    metric: str
    center: float
    scale: float
    window_size: int


class RiskAssessment(BaseModel):
    action: Action
    score: float = Field(ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)
    missing_context: list[str] = Field(default_factory=list)


class AgentRecommendation(BaseModel):
    action: Action
    question: str | None = None
    reasons: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
