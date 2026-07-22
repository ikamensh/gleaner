# Iteration 1

**Goal:** Harden the core capture contract around idempotent uploads and safe local acceptance testing.

**Outcome:** Completed. Duplicate upload semantics use last-write-wins without inflating counters, mock/cloud storage behavior aligned, live production e2e tests gated behind explicit opt-in, docs updated, and CI dependencies cleaned up.