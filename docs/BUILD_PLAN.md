# Build Plan

## Milestone 0 — repository foundation
- canonical schemas
- configuration
- interfaces
- test harness
- CI

## Milestone 1 — vertical monitoring slice
Input → quality → baseline → anomaly → policy → dashboard.
Use deterministic scenario data to prove the loop.

## Milestone 2 — replay research mode
Add dataset adapters for WESAD first, then PPG-DaLiA/BIDMC as experiments require. Preserve subject boundaries and timestamps.

## Milestone 3 — evaluation harness
Implement fixed-threshold, personalized, context-aware, and full-loop experiment configurations. Produce reproducible metrics and plots.

## Milestone 4 — agentic layer
Add provider-agnostic tool interface, structured agent output, patient-question tool, and policy validation.

## Milestone 5 — live hardware adapter
ESP32 serial/BLE adapter → canonical schema. No downstream rewrite should be necessary.

## Milestone 6 — hardening
Observability, error handling, documentation, CI, reproducible configuration, demo scenarios, and final report artifacts.
