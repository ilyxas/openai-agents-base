# OpenAI Agents SDK Life Cycle for Multi-Agent Orchestration

## Overview

This document translates the high-level architecture from `docs/architecture.md` into a low-level execution life cycle using OpenAI Agents SDK primitives.

The implementation model is a **manager-centered orchestration**:

- A **Planner Agent** creates a structured `TaskGraph`.
- A **Policy Gate** validates constraints before execution.
- An **Orchestrator Agent** executes graph steps, delegates work, and controls retries/re-planning.
- **Worker Agents** perform bounded atomic tasks through tools.
- A **Critic Agent** evaluates quality and completion criteria.
- A **HITL Agent** introduces human approval where required.
- **Tracing** records every run for observability and diagnostics.

The OpenAI Agents SDK maps this to:

- `Agent` for each role.
- `Runner.run(...)` loop for each orchestration turn.
- `Agent.as_tool()` (manager pattern) and optional `handoffs` (specialist takeover pattern).
- `input_guardrails`, `output_guardrails`, and tool guardrails for policy/safety boundaries.
- `session` or `result.to_input_list()` for multi-turn state continuity.

## Design Mapping to Repository Architecture

- `src/agents/planner_agent.py` → Planner role: transforms intent into `TaskGraph`.
- `src/policies/policy_gate.py` → Policy validator: budget/risk/tool constraints.
- `src/agents/orchestrator.py` → Central controller and execution loop coordinator.
- `src/agents/worker_agents/*` → Domain specialists wrapped as tools or handoff targets.
- `src/agents/critic_agent.py` → Quality evaluator and feedback producer.
- `src/agents/hitl_agent.py` → Human approval and escalation integration.
- `src/core/task_graph.py` → Canonical workflow state (`TaskGraph`, `TaskStep`, status, dependencies).
- `src/tracing/trace_logger.py` → Structured run/step events and post-mortem traces.
- `src/flows/task_flow.py` → Predefined end-to-end composition of these roles.

## Low-Level Life Cycle

## 1) Intake and Run Context Initialization

1. Receive user `TaskIntent`.
2. Create `RunConfig` defaults for model/provider/tracing/tool execution policies.
3. Create conversation continuity strategy:
   - `session` for persistent runs, or
   - `to_input_list()` when state is app-managed.
4. Attach global run hooks for lifecycle events (`on_agent_start`, `on_tool_start`, `on_handoff`, etc.).

## 2) Planning Phase

1. `Runner.run(planner_agent, TaskIntent, ...)`.
2. Planner returns structured plan payload mapped to `TaskGraph`.
3. Persist graph and initialize step state (`pending`).
4. Emit planning trace with graph hash/version.

## 3) Policy Validation Phase

1. Execute Policy Gate checks against `TaskGraph`.
2. Validate:
   - safety/risk constraints,
   - budget/time/tool limits,
   - dependency correctness.
3. Outcomes:
   - **approved** → continue to execution,
   - **needs_revision** → return feedback to Planner and regenerate,
   - **rejected** → fail run with actionable diagnostics.

## 4) Orchestration Phase (Main Execution Loop)

For each executable `TaskStep` (dependencies satisfied):

1. Orchestrator selects next step(s) and strategy:
   - sequential for strict dependencies,
   - parallel for independent branches.
2. Delegation model:
   - **agents as tools** when orchestrator retains control,
   - **handoff** when specialist should own the active turn.
3. Worker executes tools and returns structured output.
4. Orchestrator updates step state:
   - `in_progress` → `completed` on success,
   - `in_progress` → `failed` on error.
5. On failure:
   - retry (bounded attempts/backoff),
   - fallback worker/tool,
   - re-plan subgraph via Planner when failure is structural.

## 5) Critic Evaluation Phase

1. Critic reviews completed step outputs against acceptance criteria.
2. Critic produces verdict:
   - `pass`,
   - `revise` (localized fix),
   - `replan` (graph-level adaptation).
3. Orchestrator consumes verdict:
   - proceed,
   - enqueue corrective steps,
   - return to Planner with critic feedback.

## 6) Human-in-the-Loop Phase (Conditional)

Triggered for policy-critical, high-impact, or ambiguous actions:

1. HITL agent receives context package (step output + risk summary + options).
2. Human decision (`approve`, `reject`, `modify`) is captured as structured event.
3. Orchestrator applies decision:
   - continue execution,
   - alter graph/parameters,
   - terminate run.

## 7) Finalization Phase

1. Verify all terminal conditions:
   - all required steps completed,
   - no unresolved critical failures,
   - quality gates satisfied.
2. Produce final aggregated response artifact.
3. Run output guardrails for final response validation.
4. Persist full trace and final `TaskGraph` snapshot.

## 8) Observability and Audit Stream (Cross-Cutting)

At every phase, tracing captures:

- agent run boundaries,
- tool call inputs/outputs,
- handoffs and role transitions,
- guardrail outcomes,
- retries, failures, and replanning decisions,
- token/cost/latency metrics.

This enables deterministic replay, regression analysis, and optimization of orchestration policies.

## Execution State Model

Recommended low-level step states:

- `pending`: declared but not ready.
- `ready`: dependencies satisfied.
- `in_progress`: actively executed by a worker.
- `blocked`: waiting on dependency/HITL.
- `completed`: accepted by Critic.
- `failed_retryable`: transient/tool/runtime failure.
- `failed_terminal`: non-recoverable or policy-rejected.
- `cancelled`: superseded by replanning.

Run-level states:

- `initialized` → `planning` → `validated` → `executing` → `finalizing` → `completed`.
- Any phase can transition to `failed` with trace-linked diagnostics.

## Guardrails and Safety Boundaries

- **Input guardrails**: enforce allowed intent domain before costly execution.
- **Tool guardrails**: validate per-tool invocation and returned payloads.
- **Output guardrails**: enforce final response safety/compliance.
- **Policy Gate** remains the deterministic enforcement layer, while guardrails provide runtime model-side checks.

## Example: Initial Task and Execution Simulation

### Initial Task

"Prepare a production-ready release note package from merged PRs for version `v1.4.0`, including a summary, risk flags, and rollback checklist."

### Required Agent Roles

- **Planner Agent**: decomposes task into graph steps.
- **Orchestrator Agent**: controls execution and state transitions.
- **Worker Agent: Git Analyzer**: collects PR/commit metadata.
- **Worker Agent: Summarizer**: drafts release notes.
- **Worker Agent: Risk Reviewer**: extracts risky changes and rollback concerns.
- **Critic Agent**: verifies completeness and quality.
- **HITL Agent**: requests human approval for final publication.

### Tools Used

- Repository API tool (read PRs, labels, commits).
- Diff/stat analysis tool.
- Template/rendering tool for release note formatting.
- Policy tool for compliance checks.
- Trace logger for run telemetry.

### Simulated Flow

1. **Plan**
   - Planner creates steps:
     1. collect merged PRs,
     2. classify changes,
     3. draft release notes,
     4. generate rollback checklist,
     5. quality validation,
     6. human approval.
2. **Validate**
   - Policy Gate confirms required tools are available and scope is release-only.
3. **Execute**
   - Orchestrator runs Git Analyzer worker for steps 1-2.
   - Summarizer worker drafts release text (step 3).
   - Risk Reviewer worker generates rollback checklist (step 4).
4. **Evaluate**
   - Critic flags missing security-impact section; Orchestrator adds corrective sub-step.
   - Summarizer revises output.
5. **HITL**
   - HITL agent asks release manager to approve publication.
   - Human requests one wording change; Orchestrator applies revision.
6. **Finalize**
   - Critic passes.
   - Output guardrail validates final text.
   - Orchestrator marks run `completed` and stores trace + final artifacts.

### Result

A validated release note package is produced with full audit trail, explicit risk section, rollback checklist, and human approval evidence.
