from app.anomaly.detector import detect_anomaly
from app.context.engine import build_context
from app.decision.policy import decide
from app.models import (
    AnomalyResult,
    AnomalySeverity,
    MonitoringResult,
    MonitoringThresholds,
    Observation,
    Baseline,
    SignalQualityStatus,
)
from app.personalization.baseline import BaselineState, EWMA
from app.risk.assessment import assess_risk
from app.signal.quality import evaluate_signal_quality
from app.storage.sqlite import SQLiteBaselineRepository


class MonitoringService:
    def __init__(
        self,
        subject_id: str,
        metric: str = "heart_rate",
        alpha: float = 0.1,
        warmup_minimum: int = 3,
        thresholds: MonitoringThresholds | None = None,
        baseline_repository: SQLiteBaselineRepository | None = None,
    ) -> None:
        self.thresholds = thresholds or MonitoringThresholds()

        self.baseline = EWMA(
            subject_id=subject_id,
            metric=metric,
            alpha=alpha,
            warmup_minimum=warmup_minimum,
            thresholds=self.thresholds,
        )
        self.baseline_repository = baseline_repository

        if self.baseline_repository is not None:
            persisted_state = self.baseline_repository.load(
                subject_id=subject_id,
                metric=metric,
            )

            if persisted_state is not None:
                self.baseline.restore(persisted_state)

        self._consecutive_deviations = 0

    def _to_baseline(self, state: BaselineState) -> Baseline:
        return Baseline(
            subject_id=state.subject_id,
            metric=state.metric,
            center=state.mean,
            scale=state.scale,
            window_size=state.count,
        )

    def process(
        self,
        observation: Observation,
    ) -> MonitoringResult:
        signal_quality = evaluate_signal_quality(
            observation,
            self.thresholds,
        )

        baseline_state = None

        if signal_quality.status == SignalQualityStatus.TRUSTWORTHY:
            try:
                baseline_state = self.baseline.state
            except ValueError:
                baseline_state = None

        if baseline_state is None:
            anomaly = self._warmup_or_unknown()
        else:
            anomaly = detect_anomaly(
                observation,
                baseline_state,
                self.thresholds,
                consecutive_count=self._consecutive_deviations + 1,
            )

        if anomaly.severity == AnomalySeverity.ELEVATED:
            self._consecutive_deviations += 1
        else:
            self._consecutive_deviations = 0

        context = build_context(observation)

        risk = assess_risk(
            anomaly,
            context,
        )

        decision = decide(
            anomaly,
            risk,
            context,
            self.thresholds,
        )

        self._update_baseline(
            observation,
            anomaly,
            signal_quality.status,
        )

        return MonitoringResult(
            observation=observation,
            signal_quality=signal_quality,
            baseline=(self._to_baseline(baseline_state) if baseline_state is not None else None),
            anomaly=anomaly,
            context=context,
            risk=risk,
            decision=decision,
        )

    def _update_baseline(
        self,
        observation: Observation,
        anomaly: AnomalyResult,
        signal_quality_status: SignalQualityStatus,
    ) -> None:
        if anomaly.severity in {
            AnomalySeverity.CRITICAL,
            AnomalySeverity.ELEVATED,
        }:
            return

        if signal_quality_status != SignalQualityStatus.TRUSTWORTHY:
            return

        try:
            state = self.baseline.update(observation)

            if self.baseline_repository is not None:
                self.baseline_repository.save(state)

        except ValueError:
            return

    def _warmup_or_unknown(self) -> AnomalyResult:
        return AnomalyResult(
            metric=self.baseline.metric,
            severity=AnomalySeverity.UNKNOWN,
            deviation=None,
            consecutive_count=0,
            reasons=["Personal baseline is not initialized"],
        )
