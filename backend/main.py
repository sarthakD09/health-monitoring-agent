from fastapi import FastAPI, HTTPException

from app.application.monitoring import MonitoringService
from app.models import Observation


app = FastAPI(
    title="Health Monitoring Agent API",
    version="0.1.0",
    description=(
        "Research prototype API for personalized and context-aware "
        "physiological monitoring."
    ),
)


_services: dict[str, MonitoringService] = {}


def get_monitoring_service(subject_id: str) -> MonitoringService:
    if not subject_id:
        raise HTTPException(
            status_code=400,
            detail="subject_id must not be empty",
        )

    if subject_id not in _services:
        _services[subject_id] = MonitoringService(
            subject_id=subject_id,
        )

    return _services[subject_id]


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/observations")
def process_observation(observation: Observation):
    service = get_monitoring_service(observation.subject_id)

    try:
        return service.process(observation)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc