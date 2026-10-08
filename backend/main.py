from fastapi import FastAPI

app = FastAPI(
    title="Health Monitoring Agent API",
    version="0.1.0",
    description=(
        "Research prototype API for personalized and context-aware "
        "physiological monitoring."
    ),
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}