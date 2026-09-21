# AGENTS.md — project instructions for Codex/AI coding agents

## Mission
Build a scalable, explainable research prototype for personalized and context-aware physiological alert management.

## Non-negotiable architecture
1. `app/` contains reusable production-style modules.
2. `experiments/` contains research-only scripts; experiments must not silently alter core behavior.
3. `tests/` covers every core decision path.
4. Input adapters normalize into canonical `PatientState` / `Observation` objects.
5. Safety/policy logic must remain deterministic and testable without an LLM.
6. The agent may retrieve evidence, ask questions, summarize, and recommend. Policy validates the final state/action.
7. Provider-specific code stays behind an interface.

## Explainability rules
- Functions should have narrow responsibilities and type hints.
- Prefer explicit dataclasses/Pydantic models over untyped dictionaries at module boundaries.
- Comments explain *why*, not obvious *what*.
- Avoid giant files and hidden global state.
- Every model/threshold must have a documented rationale or configuration entry.

## Research rules
- Never claim clinical validity.
- Never invent ground truth labels.
- Keep dataset-specific assumptions in dataset adapters.
- Preserve timestamps and subject boundaries during replay.
- Do not merge unrelated patients across datasets.
- Patient feedback is contextual evidence, not ground truth.

## Safety rules
- Signal quality can lower confidence or trigger reacquisition.
- Workout/activity context must never disable safety-critical monitoring.
- Patient acknowledgement/snooze must not disable safety-critical monitoring.
- Uncertainty should map to recheck/ask rather than forced certainty.
- Final escalation state must be produced by deterministic policy.

## Coding workflow
Before changing code:
1. Read the relevant architecture and tests.
2. Identify the smallest vertical slice that proves the change.
3. Implement with tests.
4. Run targeted tests, then the full test suite.
5. Update docs/DECISIONS.md for architectural choices.
6. Commit a coherent unit of work.

Do not refactor unrelated code while implementing a feature.
