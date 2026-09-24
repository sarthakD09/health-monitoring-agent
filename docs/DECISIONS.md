# Architecture Decision Log

## ADR-001: Separate deterministic core from agent
**Decision:** The LLM/agent is an orchestration layer; deterministic policy owns final safety state.
**Reason:** Explainability, testing, reproducibility, and safer failure behavior.

## ADR-002: Canonical schema across all data sources
**Decision:** Live sensors, datasets, and simulation emit the same observation/state models.
**Reason:** Enables source swapping without rewriting the inference pipeline.

## ADR-003: Separate live and replay modes
**Decision:** Do not synchronize unrelated physical and recorded patient streams.
**Reason:** Prevents invalid experimental claims.

## ADR-004: Streamlit for prototype UI
**Decision:** Use Streamlit initially; keep UI logic separate from core.
**Reason:** Fast iteration and sufficient for research demonstration.

## ADR-005: Full-stack migration boundary
**Decision:** The target delivery path is a Next.js + TypeScript frontend over
FastAPI, a Python application/domain core, and SQLite. Streamlit is legacy and
will be removed only after the replacement path works, is tested, and is
manually verified.
**Reason:** This creates a stable frontend/backend boundary while preserving
the deterministic Python core and avoiding simultaneous production dashboards.
