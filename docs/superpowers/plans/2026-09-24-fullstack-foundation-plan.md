# Full-Stack Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver one reproducible controlled-scenario path from a canonical
observation to a policy-approved monitoring state, persisted in SQLite,
delivered by FastAPI/WebSocket, and displayed by a minimal Next.js dashboard.

**Architecture:** Keep `app/models.py` as the canonical domain-model module.
Pure deterministic stages produce typed evidence; `MonitoringService` composes
them and persists a `MonitoringResult`. FastAPI is a thin delivery boundary,
and the Next.js application is a presentation-only consumer of FastAPI's
OpenAPI-derived contract and monitoring stream.

**Tech Stack:** Python 3.11+, Pydantic, FastAPI, Uvicorn, standard-library
`sqlite3`, pytest, Ruff, Next.js, TypeScript, Tailwind CSS, Vitest, React
Testing Library, and a lightweight charting library only if history needs one.

**Spec:** `docs/superpowers/specs/2026-09-24-fullstack-architecture-design.md`

## Global Constraints

- Preserve `app/models.py` as the canonical model module for this foundation.
- The deterministic policy is the only producer of `MONITOR`, `RECHECK`,
  and `ESCALATE`; neither the frontend nor the agent may bypass it.
- Use only deterministic controlled scenarios. Do not implement datasets,
  ESP32 firmware, or an LLM in this phase.
- Keep Streamlit unchanged until the replacement path passes automated and
  manual verification; remove it only in the final isolated task.
- SQLite is behind repository interfaces; domain and policy modules do not use
  SQL, FastAPI, WebSocket, or frontend imports.
- Keep thresholds in a typed, documented configuration object, not hidden
  constants. Defaults are research-demo parameters, not clinical values.
- FastAPI/Pydantic OpenAPI is the backend contract source of truth; generated
  TypeScript types do not duplicate physiological logic.
- Do not add microservices, Kafka, Redis, Kubernetes, PostgreSQL, vector
  storage, mobile clients, cloud deployment, diagnosis/treatment behavior, or
  autonomous clinical action.

## Ownership Map

| Area | Responsibility | Initial files |
| --- | --- | --- |
| Domain logic | Canonical models and deterministic evidence/policy calculations | `app/models.py`, `app/signal/`, `app/personalization/`, `app/anomaly/`, `app/context/`, `app/risk/`, `app/decision/` |
| Application orchestration | Runs stages in order, manages injected dependencies, persists result | `app/application/monitoring.py` |
| Infrastructure | Scenario source, repository implementation, SQL schema, event hub | `app/ingestion/scenarios/`, `app/storage/`, `backend/websocket/` |
| API boundary | HTTP/WS validation, serialization, dependency assembly | `backend/main.py`, `backend/api/` |
| Presentation | API/WS client, accessible state/history display, connection feedback | `frontend/` |
| Research/experiments | Future A–D comparisons and metrics; no first-slice behavior | `experiments/` remains unchanged |

## Public Interfaces Established by the Foundation

```python
# app/models.py
class Action(str, Enum):
    MONITOR = "monitor"
    RECHECK = "recheck"
    ESCALATE = "escalate"

class SignalQuality(BaseModel): ...
class Baseline(BaseModel): ...
class AnomalyResult(BaseModel): ...
class Context(BaseModel): ...
class RiskAssessment(BaseModel): ...
class Decision(BaseModel): ...
class MonitoringResult(BaseModel): ...
class MonitoringThresholds(BaseModel): ...

class SignalQualityAssessor:
    def assess(self, observation: Observation) -> SignalQuality: ...

class BaselineProvider(Protocol):
    def get_baseline(self, subject_id: str, metric: str) -> Baseline | None: ...

class TemporalAnomalyEvaluator:
    def evaluate(
        self, observation: Observation, baseline: Baseline | None,
        prior_consecutive_count: int,
    ) -> AnomalyResult: ...

class ContextResolver:
    def resolve(self, observation: Observation) -> Context: ...

class RiskAssessor:
    def assess(
        self, quality: SignalQuality, anomaly: AnomalyResult, context: Context,
    ) -> RiskAssessment: ...

class DeterministicPolicy:
    def decide(
        self, risk: RiskAssessment, quality: SignalQuality, context: Context,
        recommendation: AgentRecommendation | None = None,
    ) -> Decision: ...

class MonitoringService:
    def process(self, observation: Observation) -> MonitoringResult: ...

class MonitoringRepository(Protocol):
    def record(self, result: MonitoringResult) -> None: ...
    def current(self, subject_id: str) -> MonitoringResult | None: ...
    def history(self, subject_id: str, limit: int) -> list[MonitoringResult]: ...
    def consecutive_deviation_count(self, subject_id: str, metric: str) -> int: ...
    def set_consecutive_deviation_count(
        self, subject_id: str, metric: str, count: int,
    ) -> None: ...
```

`RiskAssessment` is migrated from its scaffold-level `action` field to
evidence-only fields: score, severity, reasons, and missing context.
`Decision.action` owns the final system state. This realizes the approved
risk-versus-policy boundary instead of retaining a duplicate decision field.

## Review Focus

- Low quality with an alarming value yields `RECHECK`, not a confidently
  inferred `ESCALATE` or `MONITOR`.
- Critical risk with missing/exercise context or a `MONITOR` agent
  recommendation still yields `ESCALATE`.
- Different subject IDs never share baseline, streak, current-state, or history.
- WebSocket disconnection does not prevent persistence; REST returns the latest
  stored result after reconnection.
- Backend schema changes fail contract verification until generated TypeScript
  API types are deliberately refreshed.

---

### Task 1: Establish typed foundation-domain contracts

**Files:**

- Modify: `app/models.py`
- Modify: `tests/test_models.py`
- Create: `tests/unit/test_models.py`

**Interfaces:**

- Add `SignalQualityStatus`, `AnomalySeverity`, `SignalQuality`,
  `AnomalyResult`, `Context`, `Decision`, `MonitoringResult`, and
  `MonitoringThresholds` alongside existing canonical models.
- `Observation.timestamp` validates timezone awareness; `signal_quality`
  remains constrained to `[0, 1]`.
- `RiskAssessment` contains evidence only; `Decision.action` contains the
  final system state and reasons.

- [ ] **Step 1: Write failing model-contract tests**

```python
def test_observation_rejects_naive_timestamp() -> None:
    with pytest.raises(ValidationError):
        Observation(timestamp=datetime(2026, 9, 24), subject_id="P01",
                    source=DataSource.SCENARIO, heart_rate=70)

def test_monitoring_result_keeps_risk_separate_from_final_decision() -> None:
    result = MonitoringResult(..., risk=RiskAssessment(score=0.8, ...),
                              decision=Decision(action=Action.RECHECK, ...))
    assert result.decision.action is Action.RECHECK
    assert not hasattr(result.risk, "action")
```

- [ ] **Step 2: Run the focused test and observe the expected failure**

Run: `pytest tests/unit/test_models.py -q`

Expected: FAIL because the models and validation do not exist and the scaffold
still exposes `RiskAssessment.action`.

- [ ] **Step 3: Implement the smallest canonical contract**

```python
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
```

Add focused validators and bounded typed fields only. Retain `app/models.py`;
move the existing acceptance test into `tests/unit/` only if doing so does not
hide a regression.

- [ ] **Step 4: Verify model behavior and lint it**

Run: `pytest tests/test_models.py tests/unit/test_models.py -q && ruff check app/models.py tests/test_models.py tests/unit/test_models.py`

Expected: all model tests pass and Ruff reports no violations.

- [ ] **Step 5: Refactor only duplicated fixtures or model construction**

Extract a test helper only if two tests need identical valid observations; do
not split `app/models.py`.

- [ ] **Step 6: Commit**

```bash
git add app/models.py tests/test_models.py tests/unit/test_models.py
git commit -m "refactor: define monitoring domain contracts"
```

### Task 2: Add deterministic evidence stages and policy safety rules

**Files:**

- Create: `app/signal/quality.py`
- Create: `app/personalization/baseline.py`
- Create: `app/anomaly/temporal.py`
- Create: `app/context/resolver.py`
- Create: `app/risk/__init__.py`
- Create: `app/risk/assessor.py`
- Modify: `app/decision/policy.py`
- Create: `tests/unit/test_signal_quality.py`
- Create: `tests/unit/test_baseline.py`
- Create: `tests/unit/test_temporal_anomaly.py`
- Create: `tests/unit/test_context.py`
- Create: `tests/unit/test_risk.py`
- Create: `tests/unit/test_policy.py`

**Interfaces:**

- `SignalQualityAssessor.assess()` marks missing/below-minimum quality as
  insufficient with reasons.
- `StaticBaselineProvider` implements `BaselineProvider` for deterministic
  scenario subjects and never infers across subjects.
- `TemporalAnomalyEvaluator.evaluate()` uses the supplied baseline and prior
  count; it stores no hidden global state.
- `ContextResolver.resolve()` returns activity when present and explicitly
  records missing activity.
- `RiskAssessor.assess()` is evidence-only.
- `DeterministicPolicy.decide()` applies this precedence: insufficient
  quality → `RECHECK`; reliable critical risk → `ESCALATE`; missing required
  context → `RECHECK`; otherwise `MONITOR` or `RECHECK` from evidence.
  An agent recommendation cannot lower a safety-required state.

- [ ] **Step 1: Write failing stage and policy tests**

```python
def test_low_quality_measurement_requires_recheck() -> None:
    quality = SignalQualityAssessor(thresholds).assess(low_quality_observation)
    decision = policy.decide(low_quality_risk, quality, known_context)
    assert decision.action is Action.RECHECK

def test_critical_risk_cannot_be_downgraded_by_activity_or_agent() -> None:
    decision = policy.decide(
        critical_risk, acceptable_quality, exercise_context,
        AgentRecommendation(action=Action.MONITOR, confidence=1.0),
    )
    assert decision.action is Action.ESCALATE
```

Also test no baseline, absent activity, normal deviation, elevated consecutive
deviation, critical deviation, and per-subject baseline lookup.

- [ ] **Step 2: Run tests and observe expected failures**

Run: `pytest tests/unit/test_signal_quality.py tests/unit/test_baseline.py tests/unit/test_temporal_anomaly.py tests/unit/test_context.py tests/unit/test_risk.py tests/unit/test_policy.py -q`

Expected: FAIL with missing modules/classes and the scaffold pass-through policy.

- [ ] **Step 3: Implement pure, injected deterministic calculations**

```python
class TemporalAnomalyEvaluator:
    def evaluate(self, observation: Observation, baseline: Baseline | None,
                 prior_consecutive_count: int) -> AnomalyResult:
        # Return explicit unknown/no-baseline evidence; do not guess a baseline.
        ...

class DeterministicPolicy:
    def decide(self, risk: RiskAssessment, quality: SignalQuality,
               context: Context,
               recommendation: AgentRecommendation | None = None) -> Decision:
        ...
```

Use `MonitoringThresholds` passed to constructors. Document why each default
is a demonstration parameter. Do not import persistence, FastAPI, or agent
providers.

- [ ] **Step 4: Verify deterministic behavior and regression safety**

Run: `pytest tests/unit -q && ruff check app tests/unit`

Expected: all evidence and policy tests pass, including both safety cases.

- [ ] **Step 5: Refactor shared test fixtures without changing thresholds**

Create `tests/conftest.py` only if it removes repeated valid observations and
baselines. Keep each expected safety outcome explicit.

- [ ] **Step 6: Commit**

```bash
git add app/signal app/personalization app/anomaly app/context app/risk app/decision tests
git commit -m "feat: add deterministic monitoring stages"
```

### Task 3: Orchestrate a controlled scenario through `MonitoringService`

**Files:**

- Create: `app/ingestion/scenarios/__init__.py`
- Create: `app/ingestion/scenarios/controlled.py`
- Create: `app/application/__init__.py`
- Create: `app/application/monitoring.py`
- Create: `app/storage/repository.py`
- Create: `app/storage/memory.py`
- Create: `tests/integration/test_monitoring_service.py`
- Create: `tests/integration/test_controlled_scenario.py`

**Interfaces:**

- `ControlledScenarioAdapter.next_observation(scenario_id: str) -> Observation`
  supplies deterministic chronological records for one named subject. The
  initial scenarios are `normal`, `sustained_deviation`,
  `critical_deviation`, and `low_quality`.
- `InMemoryMonitoringRepository` implements `MonitoringRepository` and
  stores state per subject/metric for application tests.
- `MonitoringService.process()` obtains baseline and prior streak, runs every
  stage in approved order, records the policy-approved result, then updates the
  streak.

- [ ] **Step 1: Write failing application and scenario integration tests**

```python
def test_controlled_sustained_deviation_reaches_recheck() -> None:
    service, adapter = configured_service_and_adapter()
    adapter.next_observation("sustained_deviation")
    result = service.process(adapter.next_observation("sustained_deviation"))
    assert result.decision.action is Action.RECHECK

def test_service_records_only_the_policy_approved_result() -> None:
    result = service.process(critical_observation)
    assert repository.current("P01") == result
    assert result.decision.action is Action.ESCALATE
```

- [ ] **Step 2: Run integration tests and observe expected failures**

Run: `pytest tests/integration/test_controlled_scenario.py tests/integration/test_monitoring_service.py -q`

Expected: FAIL because adapter, repository protocol, and application service do
not exist.

- [ ] **Step 3: Implement the minimal source-agnostic vertical slice**

```python
class MonitoringService:
    def process(self, observation: Observation) -> MonitoringResult:
        quality = self._quality_assessor.assess(observation)
        baseline = self._baselines.get_baseline(observation.subject_id, "heart_rate")
        prior_count = self._repository.consecutive_deviation_count(
            observation.subject_id, "heart_rate"
        )
        anomaly = self._anomalies.evaluate(observation, baseline, prior_count)
        context = self._context.resolve(observation)
        risk = self._risk.assess(quality, anomaly, context)
        decision = self._policy.decide(risk, quality, context)
        result = MonitoringResult(...)
        self._repository.record(result)
        self._repository.set_consecutive_deviation_count(...)
        return result
```

Keep scenario data in the adapter, not the application service. Do not create
dataset or hardware directories without an implemented adapter.

- [ ] **Step 4: Verify the in-memory vertical path**

Run: `pytest tests/unit tests/integration/test_controlled_scenario.py tests/integration/test_monitoring_service.py -q && ruff check app tests`

Expected: controlled scenarios prove normal, recheck, escalation, and
low-quality behavior through the same service entry point.

- [ ] **Step 5: Refactor dependency assembly only**

Add a test-local service factory only if constructor setup is duplicated. Do not
add a global singleton.

- [ ] **Step 6: Commit**

```bash
git add app/application app/ingestion/scenarios app/storage tests/integration
git commit -m "feat: orchestrate controlled monitoring scenarios"
```

### Task 4: Persist monitoring state with SQLite behind the repository port

**Files:**

- Create: `app/storage/sqlite.py`
- Modify: `app/storage/repository.py`
- Create: `tests/integration/test_sqlite_repository.py`
- Modify: `tests/integration/test_monitoring_service.py`

**Interfaces:**

- `SQLiteMonitoringRepository(database_path: Path)` implements every
  `MonitoringRepository` method using `sqlite3`.
- `initialize()` creates a versioned schema for serialized monitoring results
  and subject/metric anomaly streaks. Rows retain source timestamp and subject
  ID for bounded subject-scoped queries.
- JSON serialization uses Pydantic model JSON APIs; no SQL appears in
  `MonitoringService` or policy code.

- [ ] **Step 1: Write failing persistence tests**

```python
def test_sqlite_repository_round_trips_current_and_history(tmp_path: Path) -> None:
    repository = SQLiteMonitoringRepository(tmp_path / "monitoring.db")
    repository.initialize()
    repository.record(result_for("P01"))
    repository.record(later_result_for("P01"))
    assert repository.current("P01").observation.timestamp == later_timestamp
    assert len(repository.history("P01", limit=10)) == 2

def test_sqlite_repository_does_not_mix_subject_history(tmp_path: Path) -> None:
    ...
    assert [item.observation.subject_id for item in repository.history("P01", 10)] == ["P01"]
```

- [ ] **Step 2: Run persistence tests and observe expected failures**

Run: `pytest tests/integration/test_sqlite_repository.py -q`

Expected: FAIL because the SQLite repository and schema do not exist.

- [ ] **Step 3: Implement the narrow SQLite adapter**

```python
class SQLiteMonitoringRepository:
    def record(self, result: MonitoringResult) -> None:
        # Store subject ID, timestamp, and model_dump_json() transactionally.
        ...

    def history(self, subject_id: str, limit: int) -> list[MonitoringResult]:
        # Query the requested subject only, newest first, with a bounded limit.
        ...
```

Use parameterized queries, context-managed connections, and a schema-version
table. Fail visibly on database errors; do not convert a storage failure into a
different policy state.

- [ ] **Step 4: Verify persistence through the actual service**

Run: `pytest tests/integration/test_sqlite_repository.py tests/integration/test_monitoring_service.py -q && ruff check app/storage tests/integration`

Expected: stored results and anomaly streaks survive repository recreation,
remain subject-scoped, and do not alter policy outputs.

- [ ] **Step 5: Refactor serialization in one private helper if repeated**

Keep the repository protocol unchanged; do not introduce an ORM or database
framework.

- [ ] **Step 6: Commit**

```bash
git add app/storage tests/integration
git commit -m "feat: persist monitoring results in sqlite"
```

### Task 5: Expose the deterministic slice through FastAPI REST

**Files:**

- Modify: `pyproject.toml`
- Create: `backend/__init__.py`
- Create: `backend/main.py`
- Create: `backend/api/__init__.py`
- Create: `backend/api/routes.py`
- Create: `backend/api/dependencies.py`
- Create: `tests/integration/test_api.py`
- Create: `tests/contract/test_openapi.py`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**

- `create_app(database_path: Path | str = "health_monitoring.db") -> FastAPI`
  assembles concrete adapters and creates the repository schema at startup.
- `GET /api/health` returns a non-clinical readiness payload.
- `GET /api/state?subject_id=P01` returns the latest `MonitoringResult` or
  a documented 404 when no stored state exists.
- `GET /api/history?subject_id=P01&limit=20` returns bounded typed results.
- `POST /api/scenarios/{scenario_id}/advance` obtains one observation through
  `ControlledScenarioAdapter`, calls `MonitoringService`, and returns its
  final result.

- [ ] **Step 1: Write failing REST and OpenAPI tests**

```python
def test_advance_scenario_returns_policy_approved_result(client: TestClient) -> None:
    response = client.post("/api/scenarios/critical_deviation/advance")
    assert response.status_code == 200
    assert response.json()["decision"]["action"] == "escalate"

def test_openapi_exposes_only_initial_monitoring_contract(app: FastAPI) -> None:
    paths = app.openapi()["paths"]
    assert {"/api/health", "/api/state", "/api/history"} <= set(paths)
    assert "/api/patient/feedback" not in paths
```

- [ ] **Step 2: Run API tests and observe expected failures**

Run: `pytest tests/integration/test_api.py tests/contract/test_openapi.py -q`

Expected: FAIL because FastAPI, routes, dependency assembly, and API contract
are absent.

- [ ] **Step 3: Add the minimum backend dependency and thin routes**

Add FastAPI and Uvicorn to `pyproject.toml`; use standard SQLite rather than
an ORM. Route functions validate request/query values, call injected
service/repository dependencies, and return typed response models.

```python
@router.post("/api/scenarios/{scenario_id}/advance", response_model=MonitoringResult)
def advance_scenario(scenario_id: str, service: MonitoringService = Depends(...)) -> MonitoringResult:
    return service.process(adapter.next_observation(scenario_id))
```

Patient feedback is deliberately not exposed. It belongs to a later adaptive
reassessment slice.

- [ ] **Step 4: Verify HTTP behavior, startup, and Python quality gates**

Run: `pytest tests/unit tests/integration/test_api.py tests/contract/test_openapi.py -q && ruff check app backend tests && python -c "from backend.main import create_app; assert create_app(':memory:').openapi()['openapi']"`

Expected: service remains the only monitoring orchestrator; routes expose only
the approved REST surface and OpenAPI generates successfully.

- [ ] **Step 5: Refactor repeated dependency wiring into `dependencies.py`**

Do not move monitoring behavior into routes or create a singleton that leaks
state between tests.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml backend tests/integration/test_api.py tests/contract/test_openapi.py .github/workflows/ci.yml
git commit -m "feat: add fastapi monitoring api"
```

### Task 6: Add policy-approved monitoring updates over WebSocket

**Files:**

- Create: `backend/websocket/__init__.py`
- Create: `backend/websocket/monitor.py`
- Modify: `backend/main.py`
- Modify: `backend/api/routes.py`
- Create: `tests/integration/test_websocket.py`

**Interfaces:**

- `MonitoringHub.broadcast(result: MonitoringResult) -> Awaitable[None]` is a
  backend infrastructure delivery adapter.
- `WS /ws/monitor` sends only serialized, completed `MonitoringResult`
  messages after scenario processing succeeds.
- The REST route publishes after `MonitoringService.process()` returns and
  persistence finishes; the socket does not accept policy-changing commands.

- [ ] **Step 1: Write failing WebSocket behavior tests**

```python
def test_scenario_advance_broadcasts_persisted_policy_result(client: TestClient) -> None:
    with client.websocket_connect("/ws/monitor") as websocket:
        response = client.post("/api/scenarios/critical_deviation/advance")
        message = websocket.receive_json()
    assert message["decision"]["action"] == response.json()["decision"]["action"]

def test_websocket_disconnect_does_not_block_persistence(client: TestClient) -> None:
    client.post("/api/scenarios/normal/advance")
    assert client.get("/api/state", params={"subject_id": "P01"}).status_code == 200
```

- [ ] **Step 2: Run the WebSocket tests and observe expected failures**

Run: `pytest tests/integration/test_websocket.py -q`

Expected: FAIL because no WebSocket route or broadcast hub exists.

- [ ] **Step 3: Implement a small connection-managed hub**

```python
@router.websocket("/ws/monitor")
async def monitor_updates(websocket: WebSocket) -> None:
    await hub.connect(websocket)
    try:
        await websocket.receive_text()  # Optional keepalive only; ignore commands.
    except WebSocketDisconnect:
        hub.disconnect(websocket)
```

Make broadcasts resilient to disconnected clients. Do not deliver raw adapter
data, accept decision commands, or move policy logic into `backend/`.

- [ ] **Step 4: Verify delivery and REST recovery**

Run: `pytest tests/integration/test_api.py tests/integration/test_websocket.py -q && ruff check backend tests/integration`

Expected: a connected client receives the persisted, policy-approved result;
a disconnected client recovers through REST.

- [ ] **Step 5: Refactor hub lifecycle only if startup/shutdown repeats**

Keep WebSocket connection state in the FastAPI application, not a module global.

- [ ] **Step 6: Commit**

```bash
git add backend tests/integration/test_websocket.py
git commit -m "feat: stream monitoring updates over websocket"
```

### Task 7: Add a minimal Next.js presentation and generated API contract

**Files:**

- Create: `frontend/package.json`
- Create: `frontend/package-lock.json`
- Create: `frontend/next.config.*`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tailwind.config.*`
- Create: `frontend/postcss.config.*`
- Create: `frontend/src/app/layout.tsx`
- Create: `frontend/src/app/page.tsx`
- Create: `frontend/src/app/globals.css`
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/lib/api-schema.d.ts` (generated from OpenAPI)
- Create: `frontend/src/lib/monitoring-stream.ts`
- Create: `frontend/src/components/monitoring-dashboard.tsx`
- Create: `frontend/src/components/monitoring-dashboard.test.tsx`
- Create: `frontend/src/lib/api.test.ts`
- Create: `scripts/export_openapi.py`
- Modify: `.github/workflows/ci.yml`
- Create: `tests/contract/test_frontend_contract.py`

**Interfaces:**

- `scripts/export_openapi.py` imports `create_app()`, writes backend OpenAPI
  JSON to a temporary location, and feeds committed `api-schema.d.ts` through
  an npm `openapi-typescript` script.
- `api.ts` uses generated types to fetch health, current state, history, and
  scenario advance responses. It contains no thresholds, risk formulas,
  baseline code, or state policy.
- `MonitoringDashboard` displays vitals, quality, baseline/anomaly summary,
  context, decision, reasons, history, and API/WebSocket connection state. Its
  scenario-advance control is a demo input, not a clinical action.

- [ ] **Step 1: Write failing frontend and schema-compatibility tests**

```tsx
it("renders the policy state and reasons returned by the API", async () => {
  render(<MonitoringDashboard initialResult={criticalResult} />)
  expect(screen.getByText("ESCALATE")).toBeVisible()
  expect(screen.getByText(/critical deviation/i)).toBeVisible()
})

it("shows an unavailable connection without inventing a clinical state", async () => {
  render(<MonitoringDashboard apiError="Backend unavailable" />)
  expect(screen.getByText("Backend unavailable")).toBeVisible()
})
```

```python
def test_generated_frontend_contract_matches_backend_openapi() -> None:
    completed = subprocess.run(
        ["npm", "run", "generate:api", "--", "--check"], cwd="frontend", check=False
    )
    assert completed.returncode == 0
```

- [ ] **Step 2: Run test/build commands and observe expected failures**

Run: `cd frontend && npm test -- --run && npm run typecheck && npm run build`

Expected: FAIL because frontend, generated contract, and UI do not exist. After
installing frontend dependencies, also run
`pytest tests/contract/test_frontend_contract.py -q`.

- [ ] **Step 3: Scaffold only the approved presentation boundary**

Create a standard Next.js TypeScript/Tailwind app with a pinned lockfile. Add
`openapi-typescript`, Vitest, and React Testing Library as development
dependencies. Generate and commit `api-schema.d.ts`. Configure
`NEXT_PUBLIC_API_BASE_URL` and `NEXT_PUBLIC_MONITOR_WS_URL`; no secrets are
needed.

```ts
export async function getCurrentState(subjectId: string): Promise<MonitoringResult> {
  const response = await fetch(`${apiBase}/api/state?subject_id=${subjectId}`)
  if (!response.ok) throw new ApiError(response.status)
  return response.json() as Promise<MonitoringResult>
}
```

Keep API response mapping in `api.ts` and visual/accessibility markup in
components. Add a chart only for returned history and only after basic text or
table display works.

- [ ] **Step 4: Verify frontend, backend contract, and production build**

Run: `cd frontend && npm ci && npm test -- --run && npm run typecheck && npm run lint && npm run build && npm run generate:api -- --check`

Run: `pytest tests/contract/test_frontend_contract.py tests/contract/test_openapi.py -q`

Expected: UI tests pass; TypeScript/build/lint succeed; generated types match
backend OpenAPI without duplicating domain logic.

- [ ] **Step 5: Refactor presentation-only repetition**

Extract a display-only `DecisionBadge` or `ConnectionStatus` only if used
in more than one place. Do not create frontend business services.

- [ ] **Step 6: Commit**

```bash
git add frontend scripts/export_openapi.py tests/contract .github/workflows/ci.yml
git commit -m "feat: add nextjs monitoring dashboard"
```

### Task 8: Verify replacement path, document operation, and remove Streamlit

**Files:**

- Modify: `README.md`
- Modify: `docs/BUILD_PLAN.md`
- Modify: `.github/workflows/ci.yml`
- Delete: `app/dashboard/ui.py`
- Delete: `app/dashboard/__init__.py`
- Modify: `pyproject.toml`
- Create: `tests/integration/test_full_stack_flow.py`

**Interfaces:**

- No new domain or API interface is introduced.
- The end-to-end test advances a controlled scenario through REST, verifies the
  saved REST state and WebSocket payload agree, and asserts the backend
  produced the final decision.
- README run instructions describe separate backend/frontend processes and
  retain the research-prototype safety disclaimer.

- [ ] **Step 1: Write the replacement-path integration test**

```python
def test_controlled_scenario_rest_state_and_websocket_agree(client: TestClient) -> None:
    with client.websocket_connect("/ws/monitor") as socket:
        advanced = client.post("/api/scenarios/critical_deviation/advance").json()
        streamed = socket.receive_json()
    stored = client.get("/api/state", params={"subject_id": "P01"}).json()
    assert streamed["decision"] == advanced["decision"] == stored["decision"]
```

- [ ] **Step 2: Run it before cleanup and stop on failure**

Run: `pytest tests/integration/test_full_stack_flow.py -q`

Expected: PASS before Streamlit removal. If it fails, repair the replacement
path in its owning earlier task; do not delete Streamlit.

- [ ] **Step 3: Perform the required manual replacement-path verification**

Run backend: `uvicorn backend.main:app --host 127.0.0.1 --port 8000`

Run frontend separately: `cd frontend && npm run dev`

Verify in the browser that advancing each controlled scenario updates state and
reasons, history is visible, unavailable backend is a connection problem rather
than a clinical state, and a refresh recovers through REST. Record commands and
outcome in `README.md`.

- [ ] **Step 4: Remove only the validated legacy dashboard**

Remove Streamlit/Plotly dependencies from `pyproject.toml` only after Task 8
tests and manual verification succeed. Do not change the deterministic core in
this cleanup.

- [ ] **Step 5: Run every repository verification gate**

Run: `pytest -q && ruff check app backend tests && python -c "from backend.main import create_app; assert create_app(':memory:').openapi()['paths']"`

Run: `cd frontend && npm ci && npm test -- --run && npm run typecheck && npm run lint && npm run build && npm run generate:api -- --check`

Expected: all Python, backend, contract, frontend, type, lint, and build checks
pass after legacy removal.

- [ ] **Step 6: Commit the isolated legacy migration**

```bash
git add README.md docs/BUILD_PLAN.md .github/workflows/ci.yml pyproject.toml tests/integration
git rm app/dashboard/ui.py app/dashboard/__init__.py
git commit -m "refactor: remove legacy streamlit dashboard"
```

## Expected Repository Structure After the Foundation Phase

```text
app/
  models.py
  application/monitoring.py
  ingestion/scenarios/controlled.py
  signal/quality.py
  personalization/baseline.py
  anomaly/temporal.py
  context/resolver.py
  risk/assessor.py
  decision/policy.py
  storage/{repository,memory,sqlite}.py
  agent/__init__.py
backend/
  main.py
  api/{dependencies,routes}.py
  websocket/monitor.py
frontend/
  src/app/
  src/components/
  src/lib/{api,api-schema,monitoring-stream}.ts
tests/
  unit/
  integration/
  contract/
docs/superpowers/{specs,plans}/
experiments/                 # unchanged; reserved for A–D evaluations
```

## Complete Verification Checklist

- [ ] `pytest -q`
- [ ] `ruff check app backend tests`
- [ ] `python -c "from backend.main import create_app; assert create_app(':memory:').openapi()['paths']"`
- [ ] `pytest tests/integration/test_monitoring_service.py tests/integration/test_sqlite_repository.py tests/integration/test_api.py tests/integration/test_websocket.py tests/integration/test_full_stack_flow.py -q`
- [ ] `pytest tests/contract/test_openapi.py tests/contract/test_frontend_contract.py -q`
- [ ] `cd frontend && npm ci && npm test -- --run`
- [ ] `cd frontend && npm run typecheck && npm run lint && npm run build`
- [ ] `cd frontend && npm run generate:api -- --check`
- [ ] Manual browser verification of REST recovery, WebSocket update, all three
  system states, reason display, and unavailable-backend display
- [ ] `git status --short` is clean after each coherent commit

## Definition of Done

The foundation is complete only when a deterministic controlled scenario enters
as a canonical `Observation`, traverses every approved stage through
`MonitoringService`, persists a typed result in subject-scoped SQLite storage,
returns it through FastAPI REST, broadcasts the same policy-approved result on
the monitoring WebSocket, and renders it in the Next.js UI. Automated unit,
integration, contract, frontend, lint, typecheck, and build checks must pass;
the replacement flow must be manually verified before the isolated
Streamlit-removal commit. The branch must contain no excluded technology or
unsupported clinical claim.

## Known Deferred Work

- WESAD, PPG-DaLiA, BIDMC PPG & Respiration, and BUT PPG adapters, including
  dataset-specific preprocessing and subject-boundary tests.
- ESP32 firmware, serial/BLE transport, MAX30102/MPU6050/temperature hardware
  integration, and physical-device validation.
- Experiment runners for configurations A–D, label-aware metrics, plots, and
  reproducible research reports.
- Patient-feedback endpoint and adaptive reassessment after separate evidence
  modeling and safety tests are designed.
- Agent tools, provider adapters, structured recommendation handling, and
  failure-mode tests; policy authority remains unchanged.
- Authentication, privacy controls, production deployment, PostgreSQL,
  observability expansion, and clinical validation.
