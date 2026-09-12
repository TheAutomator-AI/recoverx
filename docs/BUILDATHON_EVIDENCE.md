# RecoverX — Buildathon Evidence & Evaluation Methodology

## What is being measured

RecoverX evaluates revenue recovery as a constrained decision problem. The same deterministic synthetic payment cohort is passed through three strategies:

1. **Baseline A — Naive Always Retry:** retries every failed event and intentionally ignores safety constraints.
2. **Baseline B — Deterministic Rules:** uses fixed rules for a narrow set of recoverable failures.
3. **RecoverX — AI + Policy:** diagnoses the failure, calibrates confidence, proposes an action, and gives a deterministic policy engine final authority over execution.

## Ground truth

Every generated event contains explicit ground-truth labels for recoverability, ideal recovery strategy, ideal autonomy level, terminal status, duplicate/in-flight hazards, contradictory telemetry, and high-value governance requirements.

## Revenue recovery definition

A recovery is counted only when the benchmark simulator returns a successful recovery outcome for the event. The dashboard and Judge Center label the environment as **synthetic/simulated** so no synthetic result is presented as live merchant revenue.

## Safety invariants

The constrained RecoverX result must satisfy all of the following before it is considered valid:

- zero unsafe executions;
- zero deterministic policy violations;
- no terminal-failure retries;
- no duplicate in-flight executions;
- no automatic retry against contradictory settlement telemetry;
- no unauthorized autonomous execution for governed high-value transactions.

## Why the baselines matter

Raw gross recovery alone is not sufficient. Baseline A can appear to recover more money while violating payment safety rules. RecoverX is compared against the same cohort and simulator, and the judge-facing view reports both gross recovery and safety-constrained performance.

## Reproducibility

The evaluation API accepts a dataset size and random seed. The default judge path runs a 10,000-event benchmark with seed `42`. Re-running the benchmark with the same inputs regenerates the same scenario distribution and allows the comparison to be reproduced.

## Important demo disclosure

This repository is a hackathon prototype. Payment execution, recovery outcomes, customer records, and revenue values shown in the public environment are simulated and must not be interpreted as production merchant data.
