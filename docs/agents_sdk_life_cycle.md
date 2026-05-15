## Overview: Deterministic Multi-Agent Orchestration

This framework orchestrates execution lifecycles using modular and extensible components. It enables deterministic control for a wide variety of project scenarios by integrating:
- `Agents`: Propose logical steps.
- `Orchestrator`: Centrally regulates all state transitions.
- `Runtime`: Executes authorized steps.
- `Critic`: Evaluates quality and compliance, feeding back into iterative workflows.
- `HITL`: Integrates critical human decisions.

The core execution principle separates **planning**, **authorization**, **execution**, and **validation steps** into a systematic lifecycle framework:
1. Proposal: Agents decompose tasks into structured plans.
2. Validation: Orchestrator ensures compliance with rules and policies.
3. Execution: Runtime executes atomic steps on workers.
4. Evaluation: Results are recursively validated to modify or finalize outputs.

## Core Clarification

The **Orchestrator is not an LLM Agent**.

The Orchestrator is deterministic control logic (algorithm/state machine) that enforces lifecycle transitions:

- `validate`
- `approve`
- `reject`
- `ask_human`
- `replan`
- `execute`

In short:

- **Agent proposes next step**.
- **Orchestrator authorizes next step**.
- **Runtime executes next step**.

## Component Responsibilities

- **Planner Agent**: converts task intent into an initial `TaskGraph` proposal.
- **Project Agents**: specialized reasoning/generation agents for domain tasks.
- **Critic Agent**: evaluates outputs against quality/acceptance criteria.
- **HITL Component**: obtains human decision for gated or high-risk transitions.
- **Policy Gate**: deterministic checks for budget, risk, permission, compliance, tool availability.
- **Deterministic Orchestrator**: lifecycle controller and state transition authority.
- **Runtime**: executes authorized units (tools, agent calls, handoffs, sandbox execution).
- **Tracing Layer**: emits auditable lifecycle events and metrics.

## Modular Extensibility for Projects

Each project dynamically configures its modules:
- **Agents**: Specialized planners/workers/critics.
- **Tools**: Local or external tools, such as computation pipelines, HTTP/API bridges.
- **Guardrails**: Input, output, and execution boundaries.
- **Policies**: Budgets, compliance rules, risk thresholds.
- **Runtime Modes**: Sandbox, live systems, or parallel workers.

### Example:
For a "Game Development" scenario, components may include:
- **Planner Agent**: TaskGraph decomposition (code scaffolding).
- **Worker Agents**: Implement gameplay, UI, and build process.
- **Tools**: File I/O and build/test tools.
- **Guardrails**: Ensure safe command execution.
- **Policies**: Validate code quality before packaging.
- **Runtime**: Handles shell/task execution connected to worker roles.

## Visual Flow Between Components

```text
+-------------------+      propose next step      +---------------------------+
| Planner/Worker    | --------------------------> | Deterministic Orchestrator|
| Agent(s)          |                             | (state machine / policy)  |
+-------------------+                             +-------------+-------------+
                                                              |
                     +----------------------- authorize -------+-------+
                     |                                           reject |
                     v                                                  v
          +------------------------+                         +--------------------+
          | Runtime Executor       |                         | Failure/Stop Path  |
          | (tools/sandbox/handoff)|                         | + diagnostics      |
          +-----------+------------+                         +--------------------+
                      |
                      | result/events
                      v
          +------------------------+
          | Critic + Guardrails    |
          | (quality/safety check) |
          +-----------+------------+
                      |
        pass ---------+--------- revise/replan --------+
                      |                                 |
                      v                                 v
            +------------------+                +------------------+
            | Complete/Finalize|                | Re-enter planner |
            +------------------+                +------------------+

Human approval gate can be triggered by orchestrator before authorization:
Orchestrator -> HITL decision -> authorize/reject/modify -> Runtime
```

## Low-Level Life Cycle

## 1) Registration and Bootstrapping

Before execution, a project registers capabilities into the framework:

- `AgentRegistry`: planner, workers, critic, optional realtime/sandbox agents.
- `ToolRegistry`: function tools, MCP tools, hosted tools, local runtime tools.
- `GuardrailRegistry`: input/output/tool guardrails.
- `PolicyRegistry`: deterministic rules and thresholds.
- `FlowRegistry`: reusable flow templates.

Output of this phase: runnable project profile + lifecycle configuration.

## 2) Task Intake and Plan Proposal

1. Receive high-level user task intent.
2. Planner Agent proposes a `TaskGraph` (steps, dependencies, expected outputs).
3. Orchestrator records proposal as `proposed` state.

## 3) Deterministic Validation and Authorization

For each candidate step, Orchestrator evaluates deterministic checks:

- policy/rules,
- risk level,
- tool permissions,
- budget/time limits,
- prerequisite completion.

Decision outcomes:

- `approve` -> dispatch to runtime,
- `reject` -> mark terminal failure or request alternative,
- `ask_human` -> pause for HITL decision,
- `replan` -> request revised proposal from planner.

## 4) Runtime Execution of Authorized Step

Runtime executes only approved steps via:

- tool invocations,
- delegated worker agent runs,
- handoffs,
- sandbox/container tasks when required.

Each execution emits structured result payloads and trace events.

## 5) Quality and Safety Review

After runtime returns:

1. Critic Agent checks acceptance criteria.
2. Guardrails enforce safety/compliance boundaries.
3. Orchestrator applies deterministic transition:
   - `accept` -> `completed`,
   - `revise` -> re-execute adjusted step,
   - `replan` -> planner creates updated subgraph,
   - `fail` -> retry/fallback/terminate based on policy.

## 6) Iterative Graph Completion

Orchestrator repeats authorize -> execute -> evaluate until:

- all required steps are completed, or
- a terminal rejection/failure is reached.

## 7) Finalization

- aggregate deliverables,
- run final output guardrails,
- persist full trace + final graph snapshot,
- return final artifact and execution report.

## State Model

Step states:

- `proposed`
- `authorized`
- `blocked_human`
- `running`
- `completed`
- `needs_revision`
- `replanned`
- `rejected`
- `failed_terminal`

Run states:

- `initialized -> planning -> authorizing -> executing -> evaluating -> finalizing -> completed`
- terminal branch: `failed` / `rejected` / `cancelled`

## OpenAI Agents SDK Mapping

- `Agent`: planner/worker/critic implementations.
- `Runner.run(...)`: agent/tool turn execution in runtime stage.
- `Agent.as_tool()`: manager-style delegated specialization.
- `handoffs`: controlled role transfer for specific subflows.
- `input_guardrails` / `output_guardrails` / tool guardrails: runtime safety checks.
- `session` or `result.to_input_list()`: conversation continuity.
- tracing hooks/events: lifecycle observability.

The deterministic orchestrator remains outside these SDK agent calls and decides **if/when** a call is allowed.

## Example: Build a Small Real Game (Repository Architecture Simulation)

### Initial Task

"Create a small playable browser game (2D space dodger) with scoring, collision logic, and a packaged release artifact."

### Registered Capabilities for This Project

- Agents:
  - Planner Agent
  - Gameplay Logic Agent
  - UI/UX Agent
  - Test Writer Agent
  - Critic Agent
- Tools:
  - file read/write tool
  - shell build/test tool
  - static analysis/lint tool
  - artifact packaging tool
- Guardrails:
  - no unsafe shell commands,
  - output code style constraints,
  - dependency/license policy checks
- Policies:
  - max retries per step,
  - required tests before packaging,
  - mandatory HITL for final release approval

### Execution Simulation

1. **Plan proposal**
   - Planner proposes graph:
     1. scaffold game loop,
     2. implement player/enemy movement,
     3. implement collision + score,
     4. create UI HUD,
     5. generate tests,
     6. run lint/tests,
     7. build package,
     8. request release approval.

2. **Authorize step 1-4**
   - Orchestrator validates rules and approves implementation steps.
   - Runtime executes using Gameplay/UI agents + file/shell tools.

3. **Evaluate and revise**
   - Critic reports unstable collision edge case.
   - Orchestrator chooses `revise` (not full replan).
   - Runtime applies targeted fix.

4. **Authorize testing gate**
   - Orchestrator enforces policy: package step blocked until lint/tests pass.
   - Runtime runs Test Writer + lint/test tools.
   - Guardrail blocks one risky command; orchestrator rejects and requests safe alternative.

5. **Replan branch (conditional)**
   - Build time exceeds budget threshold.
   - Orchestrator triggers `replan` for optimization subgraph.
   - Planner proposes reduced asset pipeline; orchestrator approves.

6. **HITL approval**
   - Before publication, orchestrator enters `ask_human`.
   - Human requests score reset UX change.
   - Orchestrator authorizes one additional revision step.

7. **Finalize**
   - Runtime produces release artifact.
   - Critic + output guardrails pass.
   - Orchestrator closes run as `completed` with full trace report.

### What This Demonstrates

- Deterministic authorization control by the orchestrator.
- Separation of concerns: proposal vs authorization vs execution.
- Registry-based extensibility for future projects/scenarios.
- Full lifecycle coverage: validation, retries, replanning, HITL, guardrails, and tracing.
