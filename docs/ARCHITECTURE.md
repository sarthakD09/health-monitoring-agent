# Architecture

```text
  CONTROLLED SCENARIOS / DATASET REPLAY / ESP32
                        |
              Adapters → Canonical Observation
                        |
  Signal Quality → Personal Baseline → Temporal Anomaly
                        |
             Context → Risk Assessment → Policy
                        |
                 MONITOR / RECHECK / ESCALATE
                        |
            Python application service + SQLite
                        |
              FastAPI REST and WebSocket boundary
                        |
                Next.js + TypeScript presentation
```

## Core boundaries

### Ingestion
Adapters translate external data into canonical observations.

### Signal
Preprocessing and signal-quality estimation. Must be deterministic where possible.

### Personalization
Estimates person-specific baselines and deviation scores.

### Anomaly
Temporal rules/models detect sustained or unusual deviations.

### Context
Combines activity, schedule, history, symptoms, and other contextual evidence.

### Decision
Produces an intermediate `RiskAssessment`.

### Policy
Maps evidence and risk into `MONITOR`, `RECHECK`, or `ESCALATE`. Safety policy remains deterministic.

### Agent
Uses tools to retrieve evidence and interact with the patient. It returns a structured recommendation, not an unchecked final action.

### Storage
Stores longitudinal observations, decisions, feedback, and experiment metadata.

### Dashboard
The Next.js frontend is the target visualization and interaction surface. It
must not contain business logic. The current Streamlit dashboard is legacy and
will remain untouched until the FastAPI, Next.js, integration-test, and manual
verification gates in the architecture specification are met.

## Full specification

The detailed, frozen migration design is in
`docs/superpowers/specs/2026-09-24-fullstack-architecture-design.md`.
