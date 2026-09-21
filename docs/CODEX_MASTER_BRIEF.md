# Codex Master Brief

## Role
You are the primary engineering agent for this repository. Work inside the existing architecture; do not replace it with a new framework unless an explicit decision is recorded in `docs/DECISIONS.md`.

## Product
Build a research-grade but practical prototype of a Personalized and Context-Aware AI Health Monitoring Agent for adaptive physiological alert management.

## Core research question
Can personalized and context-aware monitoring reduce inappropriate physiological alerts while maintaining adequate detection performance?

## Required system behavior
1. Accept physiological observations from live ESP32 streams, public dataset replay, or controlled scenarios.
2. Normalize all sources into the canonical models in `app/models.py`.
3. Assess signal quality before trusting a measurement.
4. Estimate a subject-specific baseline.
5. Detect sustained/temporal deviations.
6. Add context: activity, recent history, symptoms, workout state where available.
7. Produce a structured risk assessment.
8. Allow an agent to retrieve evidence and ask for missing context.
9. Pass agent recommendations through deterministic policy validation.
10. Emit `MONITOR`, `RECHECK`, or `ESCALATE` plus machine-readable reasons.
11. Log the evidence and decision for later evaluation.

## Research baselines
Keep these independently reproducible:
- A: fixed threshold
- B: personalized baseline
- C: personalized + context
- D: full adaptive loop with patient feedback

Primary metrics: false alerts/hour or false-alert rate. Secondary: precision, recall, F1, sensitivity/specificity when supported by ground truth, detection delay, alert burden.

## Dataset strategy
- WESAD: personalization/context/self-report experiments.
- PPG-DaLiA: activity-aware PPG/HR experiments.
- BIDMC PPG & Respiration: multimodal physiological experiments.
- Optional BUT PPG: signal-quality experiments.
Do not merge unrelated subjects or datasets into one fictitious patient.

## Agent boundary
The LLM is not the raw-signal interpreter and is not the unchecked final safety decision-maker. It uses typed tools such as current vitals, signal quality, baseline, activity, history, trend analysis, patient questioning, and explanation. The deterministic policy layer validates the resulting action.

## Safety boundary
- Context does not disable safety monitoring.
- Snooze/acknowledgement does not disable safety monitoring.
- Missing/uncertain evidence should prefer recheck/questioning over fabricated certainty.
- Never claim diagnosis, treatment, medical-grade accuracy, or clinical validation.

## Coding standards
- Python 3.11+.
- Type hints at public boundaries.
- Pydantic/domain models for cross-module contracts.
- Small functions; no giant controller files.
- Dependency injection at module boundaries where useful.
- Keep provider-specific implementations behind interfaces.
- UI is a consumer of the core; no core logic in Streamlit callbacks.
- Every behavior change needs tests.
- Every architecture change needs a decision-log entry.

## Token-efficient execution protocol
Do not dump the entire codebase into chat.

For each task:
1. Inspect only relevant files.
2. State the intended change in 3–6 bullets.
3. Implement the smallest coherent vertical slice.
4. Run targeted tests.
5. Run the full suite when practical.
6. Summarize changed files, tests, and the next logical milestone.
7. Commit the change with one focused commit message.

Prefer this progression:
`foundation → vertical slice → replay → evaluation → agent → live hardware → hardening`.

Do not rewrite working modules merely for style. Avoid speculative abstractions until a second implementation needs them.

## Git protocol
- Never work directly on `main` for feature work.
- Branch naming: `feat/<topic>`, `fix/<topic>`, `exp/<topic>`.
- One conceptual change per commit.
- Before commit: `pytest` and relevant lint/type checks.
- Tag milestone releases: `v0.1-core`, `v0.2-replay`, `v0.3-eval`, `v0.4-agent`, `v0.5-live`.
- Never commit secrets, raw private patient data, `.env`, or large raw datasets.
- Use Git LFS or external dataset references later if a dataset is too large for normal Git.

## Definition of done for a feature
- Working implementation.
- Tests for normal and failure paths.
- Updated relevant docs.
- No architecture rule violated.
- Reproducible command to run it.
- Focused git commit.
