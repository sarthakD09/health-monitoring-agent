# Full-Stack Architecture Design

## 1. Purpose and research scope

This repository is a research-oriented prototype for personalized and
context-aware physiological alert management. It investigates a monitoring
workflow that combines physiological evidence, personal baselines, context,
patient feedback, and deterministic safety policy. It is not a medical device
and does not diagnose or treat patients.

The initial deliverable is one small, reproducible vertical slice from a
controlled scenario to a visible system state. It establishes stable boundaries
for later dataset replay and ESP32 input without claiming clinical validity.

## 2. Research question

Can personalized and context-aware monitoring reduce inappropriate
physiological alerts while maintaining adequate detection performance?

The repository must support comparison of these independently reproducible
experiment configurations:

| Configuration | Evidence used |
| --- | --- |
| A. Fixed Threshold | Population or configured threshold only |
| B. Personalized Baseline | Fixed threshold plus subject-specific baseline |
| C. Personalized + Context | Baseline evidence plus contextual evidence |
| D. Full Adaptive Loop | Personalized/contextual evidence plus patient feedback and adaptive reassessment |

Metrics may include false-alert rate, false alerts/hour, precision, recall,
F1, sensitivity/specificity where justified by labels, detection delay, and
alert burden. No component may assume that a later configuration improves any
metric.

## 3. Non-goals

The foundation does not implement diagnosis, treatment advice, autonomous
clinical action, an LLM safety controller, public-dataset downloads, ESP32
firmware, a production-scale distributed system, or a full dashboard. It does
not merge unrelated people or data sources into a fictional synchronized
patient stream. It does not claim ground truth from patient feedback.

The first slice does not require a vector database, microservices, Kafka,
Redis, Kubernetes, PostgreSQL, a mobile application, or cloud deployment.

## 4. Architectural principles

- The deterministic monitoring and safety pipeline is authoritative.
- Every source adapter produces the same canonical `Observation`; downstream
  code is source agnostic.
- Domain and application code are Python modules, independent of FastAPI,
  Next.js, and provider-specific hardware or agent SDKs.
- Typed Pydantic models are used at process and API boundaries. Small typed
  Python values may be used internally where a Pydantic model adds no value.
- Risk describes evidence; policy decides the allowed system state.
- Uncertainty and poor-quality signals result in reacquisition or `RECHECK`,
  not fabricated certainty.
- The frontend presents backend state and submits interactions. It never owns
  physiological analysis, baseline calculation, risk assessment, or policy.
- Storage is accessed through a narrow interface so SQLite can later be
  replaced without changing domain behavior.
- Research assumptions, thresholds, and experimental variants remain explicit,
  versioned, and testable.

## 5. System context

```text
Controlled scenarios   Public-dataset replay   ESP32 hardware
        │                       │                    │
        └──────────── adapters produce Observation ──┘
                                │
                         Python domain core
                                │
                         application service
                                │
                FastAPI REST and monitoring WebSocket
                                │
                     Next.js + TypeScript dashboard
                                │
                         SQLite event history
```

The same application service accepts replayed and live observations. Each
stream remains scoped to one subject and preserves source timestamps.

## 6. Component architecture

The initial repository layout evolves only where the first slice needs it:

```text
app/
  models.py                 # retained unless focused modules become necessary
  ingestion/                # adapter contracts and controlled scenario adapter
  signal/                   # signal-quality assessment
  personalization/          # subject baseline calculation/look-up
  anomaly/                  # temporal deviation assessment
  context/                  # normalized contextual evidence
  risk/                     # evidence-to-risk assessment
  decision/                 # deterministic policy
  application/monitoring.py # pipeline orchestration use case
  storage/                  # repository interface and SQLite implementation
  agent/                    # future structured-tool and recommendation boundary
backend/
  main.py                   # FastAPI application assembly only
  api/                      # thin REST handlers
  websocket/                # monitoring update delivery
frontend/                   # Next.js presentation application
```

`app/models.py` remains the canonical location for the first slice. It is not
split merely to match a target directory diagram. A future move to
`app/models/` requires multiple cohesive domain modules whose independent
maintenance outweighs migration cost, documented by an ADR and accompanied by
compatibility-aware tests.

## 7. Monitoring data flow

```text
Observation
  → signal quality
  → personalized baseline
  → temporal anomaly
  → context
  → risk assessment
  → deterministic policy
  → MONITOR | RECHECK | ESCALATE
```

`MonitoringService` owns this sequence. It returns a typed result containing
the observation, evidence summaries, risk assessment, decision, and
machine-readable reasons. It may persist the outcome and publish it after the
policy has produced the final state.

An agent can read structured evidence, identify missing information, ask a
question, explain a result, and issue an `AgentRecommendation`. Its
recommendation is an input to policy validation, never a substitute for the
pipeline.

## 8. Canonical domain model

The existing Pydantic `Observation` remains the canonical adapter output. It
includes an aware timestamp, subject identifier, source, optional vital
measurements, optional activity, signal quality, and bounded metadata.
Adapters must validate source-specific payloads before constructing it; core
logic must not consume raw ESP32 packets or dataset rows.

The domain also represents:

- `SignalQuality`: quality score/status and reasons for trustworthy or
  insufficient evidence.
- `Baseline`: subject, metric, center, variability, sample/window metadata.
- `AnomalyResult`: metric deviation, temporal evidence, and reasons.
- `Context`: activity, symptoms, feedback, availability, and uncertainty.
- `RiskAssessment`: evidence-derived score, reasons, and missing context.
- `AgentRecommendation`: a recommendation, confidence, reasons, question,
  and missing-information request.
- `Decision` or explicit `SystemState`: `MONITOR`, `RECHECK`, or `ESCALATE`,
  with policy reasons.

Stable names and exact field definitions are selected by the first vertical
slice's tests. Numeric thresholds and quality rules belong in explicit,
versioned configuration rather than hidden constants.

## 9. Application-service boundary

`app/application/monitoring.py` exposes a typed use case such as
`MonitoringService.process(observation: Observation) -> MonitoringResult`.
Its dependencies are injected interfaces for baseline lookup/update, context
resolution, storage, and event publishing where they are needed.

FastAPI handlers deserialize input, call this service, and serialize its typed
result. They do not calculate baselines, assign risk, apply escalation rules,
or access source-specific data. The frontend calls the API and does none of
these tasks.

## 10. Risk versus policy boundary

Risk assessment answers, “What does the available evidence indicate?” It may
report uncertainty, missing context, anomaly severity, and an evidence score.

Policy answers, “Given that evidence, what state is allowed?” It deterministically
maps inputs to `MONITOR`, `RECHECK`, or `ESCALATE`, records its reasons, and
enforces safety constraints. Policy validation is the final state-producing
operation, including when an agent recommendation is present.

## 11. Agent boundary

The agent is a future orchestration component with typed tools such as current
vitals, signal quality, baseline, activity, recent history, trend analysis,
and a patient-question interface. It may return a structured recommendation
and explanation. Provider-specific LLM code remains behind an interface in
`app/agent/`.

The agent cannot ingest raw signals as a privileged safety authority, alter a
baseline without the approved application path, or directly publish a final
system state. An unavailable agent leaves deterministic monitoring operational.

## 12. Dataset adapter boundary

Dataset adapters live under `app/ingestion/datasets/` only when an adapter is
implemented. They translate one subject's source records into chronological
`Observation` objects while preserving original timestamps, subject identity,
provenance, and dataset-specific assumptions. WESAD, PPG-DaLiA, BIDMC PPG &
Respiration, and optional BUT PPG are future inputs, not initial dependencies.

## 13. ESP32 hardware adapter boundary

An ESP32 adapter under `app/ingestion/hardware/` converts validated sensor
messages from the planned MAX30102, MPU6050, temperature sensor, and patient
controls into `Observation` and contextual evidence. It isolates serial/BLE
and firmware framing from the domain core. Hardware failures and incomplete
packets become quality/availability evidence; they do not create invented
measurements.

## 14. FastAPI REST boundary

FastAPI is the backend process boundary. Pydantic request/response models and
generated OpenAPI are the source of truth for frontend/backend contracts. The
initial slice exposes only the endpoints required to demonstrate its path:

- `GET /api/health` for process readiness.
- `GET /api/state` for the current policy-approved monitoring result.
- `GET /api/history` for bounded recent results.
- A narrow controlled-scenario advance operation to feed the first demonstration
  through the same application service.

Patient feedback is added only when the adaptive-reassessment slice is
implemented. It is submitted as contextual evidence, not a decision override.

## 15. WebSocket boundary

`WS /ws/monitor` delivers serialized, policy-approved monitoring updates to
connected presentation clients. It does not accept actions that alter policy,
baseline, or raw measurements. A connection failure must not interrupt the
pipeline or persistence; a client can recover through `GET /api/state` and
`GET /api/history`.

## 16. Next.js frontend boundary

The frontend is a standalone Next.js + TypeScript application using Tailwind
CSS and, when a chart is needed, a lightweight charting library such as
Recharts. It displays current vital values, signal quality, baseline/deviation
summary, context, decision state, reasons, history, and connection state.

It uses generated or explicitly maintained TypeScript API types derived from
the FastAPI OpenAPI schema. Backend Pydantic/OpenAPI remains authoritative;
TypeScript types must not reproduce policy rules or physiological algorithms.
Contract tests use representative API fixtures or generated types to detect
schema drift. The frontend handles unavailable API/stream connections visibly
and never converts them into a clinical conclusion.

## 17. SQLite storage boundary

SQLite is the initial persistence implementation. A storage interface records
observations, baseline snapshots where used, risk assessments, decisions,
feedback, agent events, and experiment metadata as the owning slice requires.
It supports current state and subject-scoped history queries. SQL and database
connections are not used directly by domain, policy, route, or frontend code.

Schema migration/version handling must be explicit before persisted prototype
data is relied upon. Storage failures are surfaced as operational errors and
must not cause a safety-critical escalation to be silently discarded.

## 18. Error and uncertainty handling

- Invalid adapter payloads are rejected with source-specific validation errors
  before entering the core.
- Missing metrics, unavailable context, stale data, or low signal quality are
  explicit evidence states.
- Insufficient evidence produces `RECHECK` or a request for more information
  according to deterministic policy; it does not create a normal result by
  default.
- REST responses use stable error schemas and appropriate status codes;
  WebSocket disconnects are recoverable client failures.
- Every result carries enough reasons and provenance to explain why it was
  produced without exposing raw private data unnecessarily.

## 19. Safety constraints

- The LLM/agent cannot bypass deterministic policy.
- Context, exercise status, snooze, or acknowledgement cannot suppress a
  safety-critical escalation.
- Patient acknowledgement and feedback are contextual evidence, not clinical
  ground truth and not a monitoring disable switch.
- Poor signal quality cannot produce unsupported certainty.
- Uncertainty may produce `RECHECK`; it must not force `MONITOR`.
- The system communicates research-prototype status and makes no diagnosis,
  treatment, medical-device, or clinical-validity claim.

## 20. Testing strategy

Test every core decision path before the integration boundary:

- Unit tests cover model validation, quality, baseline, temporal anomaly,
  context, risk, and policy constraints.
- Application integration tests run controlled scenarios through
  `MonitoringService` and storage.
- Backend integration tests cover REST serialization and the implemented
  WebSocket update path.
- Contract tests confirm FastAPI/OpenAPI response shapes match frontend API
  consumers.
- Frontend tests cover state presentation and failed API/stream states, while
  build and type checks verify the production bundle.

New behavioral work follows red → observed failure → minimal implementation →
green. Tests must never assert clinical validity or invent labels.

## 21. CI requirements

CI continues to install the project on Python 3.11+, run `pytest`, and run
Ruff. Once backend modules exist, it also performs an import/application
startup check. Once the frontend exists, CI installs from its lockfile and
runs frontend tests, TypeScript checking, and a production build. No product
dependency is installed during this specification-only change.

## 22. Git and version-control strategy

`main` and `v0.1.0-scaffold` remain recovery points. Full-stack work occurs on
`feat/fullstack-architecture` in small coherent commits; history is never
rewritten, main is not pushed directly, and force-push is not used. Each
behavioral change includes relevant tests and documentation updates. The
Streamlit removal is isolated in its own validated commit.

## 23. Migration strategy from the existing scaffold

1. Keep the scaffold's domain concepts, package names, and Streamlit dashboard
   intact while defining the architecture.
2. Add only the first-slice domain behavior and `MonitoringService` with tests.
3. Add controlled-scenario ingress and SQLite behind interfaces.
4. Add FastAPI REST/WebSocket delivery and test it.
5. Add the minimal Next.js presentation layer and contract/build tests.
6. Manually verify the API-to-frontend path and run all relevant tests.
7. Only then remove the Streamlit dashboard and its dependencies in a clean,
   dedicated commit.

## 24. Future extension points

Future slices can add source adapters, experiment runners, evaluation reports,
feedback/adaptive reassessment, agent providers, and ESP32 transport support
without changing the canonical observation or policy authority. PostgreSQL,
cloud deployment, and richer observability remain possible only if a concrete
technical requirement is documented and approved through an ADR.

## 25. Explicitly rejected approaches

The project rejects Streamlit as the final production dashboard; React/Next.js
business logic; a Node.js backend; direct ESP32 coupling to domain logic;
unchecked LLM decisions; microservices; Kafka; Redis; Kubernetes; PostgreSQL
at this stage; cloud-first deployment; multi-agent safety control; vector
databases; and a mobile application. These choices are rejected because they
do not serve the small, deterministic, explainable first vertical slice.
