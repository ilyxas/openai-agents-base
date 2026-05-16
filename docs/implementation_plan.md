# Implementation Plan

## Purpose

This document defines how to implement the repository architecture from:

- `docs/agents_sdk_life_cycle.md`
- `docs/architecture.md`

It also clarifies the role of SDK materials under `docs/reference/`.

## Architecture vs SDK References

### Repository Architecture (source of truth)

The project concept is defined by this repository's own architecture documents:

- deterministic orchestration lifecycle
- TaskGraph-driven planning and execution
- separation of Planner, Worker, Critic, Policy, Runtime, and Orchestrator responsibilities

These constraints come from `docs/agents_sdk_life_cycle.md` and `docs/architecture.md` and must drive implementation decisions.

### SDK Reference Materials (supporting examples)

The content in:

- `docs/reference/docs`
- `docs/reference/examples`

is external SDK guidance and usage examples. It is not the project architecture itself.

Use these references to learn API patterns (agents, tools, hooks, guardrails, handoffs), but do not treat them as a direct implementation blueprint for this repository.

## Implementation Goals

1. Implement a deterministic `TaskGraph` runtime model.
2. Implement an executable deterministic `Orchestrator` loop.
3. Implement minimal Planner/Worker/Critic agents aligned with the lifecycle.
4. Add focused tests for deterministic orchestration behavior.

## Phased Plan

### Phase 1: TaskGraph Foundation

- Define `TaskState` and valid state transitions.
- Define `TaskStep` with dependencies and execution metadata.
- Implement `TaskGraph` readiness checks (`ready`/`next runnable` logic).
- Enforce transition validity and terminal/completion checks.

### Phase 2: Deterministic Orchestrator

- Implement an explicit run state machine (authorize -> execute -> evaluate).
- Add deterministic branching for `accept`, `revise`, `replan`, and terminal failure/rejection.
- Add bounded retry behavior controlled by policy.
- Expose hook points for lifecycle tracing.

### Phase 3: Agent Layer

- `PlannerAgent`: build a `TaskGraph` from task intent.
- `WorkerAgent`: execute atomic task steps via runtime tools.
- `CriticAgent`: return deterministic verdicts for step outcomes.

### Phase 4: Validation

- Add unit tests for dependency ordering.
- Add unit tests for revision/retry paths.
- Add unit tests for policy rejection and terminal branches.
- Keep tests deterministic and isolated from external services.

## Acceptance Criteria

- The architecture docs remain the primary project specification.
- SDK reference docs/examples are used only as API usage guidance.
- A deterministic end-to-end path exists: plan -> authorize -> execute -> evaluate.
- Core orchestration branches and policy outcomes are covered by tests.
