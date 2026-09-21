# Architecture

```text
                DATA SOURCES
       +----------------+----------------+
       |                                 |
   LIVE / ESP32                     REPLAY / DATASET
       |                                 |
       +----------------+----------------+
                        |
                 Canonical Schema
                        |
                 Signal Quality
                        |
               Personal Baseline
                        |
               Temporal Anomaly
                        |
                  Context Engine
                        |
                State / Risk Model
                        |
              +---------+---------+
              |                   |
         Agent Layer        Policy Engine
              |                   |
       ask / retrieve /     validate state,
       explain / recommend  action, escalation
              |                   |
              +---------+---------+
                        |
              Dashboard / Event Log
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
Visualization and demo surface only. It must not contain business logic.
