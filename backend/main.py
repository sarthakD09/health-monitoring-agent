from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
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

@app.websocket("/ws/monitor/{subject_id}")
async def monitor_websocket(
    websocket: WebSocket,
    subject_id: str,
) -> None:
    await websocket.accept()

    service = get_monitoring_service(subject_id)

    try:
        while True:
            payload = await websocket.receive_json()

            observation = Observation.model_validate(payload)

            if observation.subject_id != subject_id:
                await websocket.send_json(
                    {
                        "error": "subject_id does not match WebSocket path",
                    }
                )
                continue

            result = service.process(observation)

            await websocket.send_json(result.model_dump(mode="json"))

    except WebSocketDisconnect:
        return