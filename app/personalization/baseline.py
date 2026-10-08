from dataclasses import dataclass

from app.models import MonitoringThresholds, Observation


@dataclass(frozen=True)
class BaselineState:
    subject_id: str
    metric: str
    mean: float
    variance: float
    count: int
    alpha: float
    warmup_minimum: int

    @property
    def scale(self) -> float:
        return max(self.variance**0.5, 1e-6)

    @property
    def warmup_complete(self) -> bool:
        return self.count >= self.warmup_minimum


class EWMA:
    def __init__(
        self,
        subject_id: str,
        metric: str,
        alpha: float,
        warmup_minimum: int,
        thresholds: MonitoringThresholds | None = None,
    ) -> None:
        if not 0.0 < alpha <= 1.0:
            raise ValueError("alpha must be in the range (0, 1]")

        if warmup_minimum < 1:
            raise ValueError("warmup_minimum must be at least 1")

        self.subject_id = subject_id
        self.metric = metric
        self.alpha = alpha
        self.warmup_minimum = warmup_minimum
        self.thresholds = thresholds or MonitoringThresholds()

        self._mean: float | None = None
        self._variance = 0.0
        self._count = 0

    def update(self, observation: Observation) -> BaselineState:
        if observation.subject_id != self.subject_id:
            raise ValueError("observation subject does not match baseline subject")

        value = getattr(observation, self.metric, None)

        if value is None:
            raise ValueError(f"observation does not contain metric: {self.metric}")

        if (
            observation.signal_quality is None
            or observation.signal_quality < self.thresholds.signal_quality_minimum
        ):
            return self.state

        if self._mean is None:
            self._mean = value
            self._variance = 0.0
            self._count = 1
            return self.state

        previous_mean = self._mean
        self._mean = (1.0 - self.alpha) * previous_mean + self.alpha * value

        deviation = value - previous_mean
        self._variance = (1.0 - self.alpha) * self._variance + self.alpha * deviation**2

        self._count += 1

        return self.state

    @property
    def state(self) -> BaselineState:
        if self._mean is None:
            raise ValueError("baseline has no valid observations")

        return BaselineState(
            subject_id=self.subject_id,
            metric=self.metric,
            mean=self._mean,
            variance=self._variance,
            count=self._count,
            alpha=self.alpha,
            warmup_minimum=self.warmup_minimum,
        )

    def restore(self, state: BaselineState) -> None:
        if state.subject_id != self.subject_id:
            raise ValueError("baseline state subject does not match baseline subject")

        if state.metric != self.metric:
            raise ValueError("baseline state metric does not match baseline metric")

        if state.alpha != self.alpha:
            raise ValueError("baseline state alpha does not match baseline alpha")

        if state.warmup_minimum != self.warmup_minimum:
            raise ValueError("baseline state warmup minimum does not match baseline configuration")

        self._mean = state.mean
        self._variance = state.variance
        self._count = state.count
