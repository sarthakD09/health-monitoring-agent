from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class DataSource(str, Enum):
    LIVE = "live"
    REPLAY = "replay"
    SCENARIO = "scenario"


class Action(str, Enum):
    MONITOR = "monitor"
    RECHECK = "recheck"
    ESCALATE = "escalate"


class SignalQualityStatus(str, Enum):
    TRUSTWORTHY = "trustworthy"
    INSUFFICIENT = "insufficient"


class AnomalySeverity(str, Enum):
    UNKNOWN = "unknown"
    NORMAL = "normal"
    ELEVATED = "elevated"
    CRITICAL = "critical"


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

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_be_timezone_aware(cls, timestamp: datetime) -> datetime:
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        return timestamp


class SignalQuality(BaseModel):
    status: SignalQualityStatus
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)


class Baseline(BaseModel):
    subject_id: str
    metric: str
    center: float
    scale: float
    window_size: int


class AnomalyResult(BaseModel):
    metric: str
    severity: AnomalySeverity
    deviation: float | None = None
    consecutive_count: int = Field(ge=0)
    reasons: list[str] = Field(default_factory=list)


class Context(BaseModel):
    activity: str | None = None
    symptoms: list[str] = Field(default_factory=list)
    patient_feedback: str | None = None
    is_available: bool = True
    missing_fields: list[str] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float = Field(ge=0.0, le=1.0)
    severity: AnomalySeverity
    reasons: list[str] = Field(default_factory=list)
    missing_context: list[str] = Field(default_factory=list)


class Decision(BaseModel):
    action: Action
    reasons: list[str] = Field(default_factory=list)


class MonitoringResult(BaseModel):
    observation: Observation
    signal_quality: SignalQuality
    baseline: Baseline | None
    anomaly: AnomalyResult
    context: Context
    risk: RiskAssessment
    decision: Decision


class MonitoringThresholds(BaseModel):
    """Research-demo defaults; they are not clinical thresholds."""

    signal_quality_minimum: float = Field(default=0.7, ge=0.0, le=1.0)
    elevated_deviation: float = Field(default=2.0, ge=0.0)
    critical_deviation: float = Field(default=3.0, ge=0.0)
    consecutive_deviations_required: int = Field(default=2, ge=1)

    @model_validator(mode="after")
    def critical_deviation_must_not_be_lower_than_elevated(self) -> "MonitoringThresholds":
        if self.critical_deviation < self.elevated_deviation:
            raise ValueError("critical_deviation must be at least elevated_deviation")
        return self


class AgentRecommendation(BaseModel):
    action: Action
    question: str | None = None
    reasons: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
