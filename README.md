# Personalized & Context-Aware AI Health Monitoring Agent

Research prototype for adaptive physiological alert management.

## Core research question
Can personalized and context-aware monitoring reduce inappropriate physiological alerts while maintaining adequate detection performance?

## Architectural rule
The deterministic monitoring core owns signal quality, personalization, anomaly detection, risk state, and safety policy. The AI agent orchestrates information retrieval, questioning, explanation, and recommendation. The LLM is never the sole safety decision-maker.

## Modes
- `live`: ESP32/wearable sensor stream
- `replay`: public physiological dataset replay
- `scenario`: controlled synthetic/demo scenarios

All modes emit the same canonical event schema.

## Development philosophy
- Build vertically, not file-by-file.
- Keep interfaces stable so datasets, hardware, models, and agent providers can be swapped.
- Every meaningful change should have tests and a git commit.
- Prefer small, explainable components over clever abstractions.
- Never couple the research core to a specific LLM provider.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
streamlit run app/dashboard/ui.py
```

## Recommended git workflow
```bash
git switch -c feat/<short-name>
# make one coherent change
pytest
git status
git add .
git commit -m "feat: <short description>"
```

Merge small, working increments. Tag milestones such as `v0.1-core`, `v0.2-replay`, `v0.3-agent`, `v0.4-live`.
