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
