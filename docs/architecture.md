# OpenAI Agents Architecture

## Core Principles

This repository provides a foundational framework for building scalable multi-agent systems based on OpenAI Agents SDK.

### Core Components:

- **Agents**: LLMs configured with instructions, tools, guardrails, and handoffs.
- **Sandbox Agents**: Agents preconfigured to work within containers, suitable for long-term and isolated tasks.
- **Agents as Tools / Handoffs**: Delegating specific tasks to sub-agents dynamically.
- **Tools**: Abstract actions enabling agents to interact with external systems (APIs, Functions, Utilities, etc.).
- **Guardrails**: Safety protocols ensuring robust input/output validation for higher stability.
- **Human-in-the-Loop (HITL)**: Mechanisms involving human intervention in workflows.
- **Sessions**: Automatic history management to maintain agent conversations coherently across runs.
- **Tracing**: Tracking agent runs for debugging and optimization.
- **Realtime Agents**: Voice agents with full `gpt-realtime-2` capabilities.

## Architectural Invariants

1. **Agent Independence**: Each agent must be modular and isolated.
2. **Tool Reusability**: Tools should allow integration across multiple workflows.
3. **Composable Flows**: Workflows should be decomposable into smaller atomic tasks.
4. **Safe Execution**: Each execution step must incorporate guardrails for validation.
5. **Tracing and Observability**: Every step must produce trace logs for monitoring and debugging.

## Repository Structure

```plaintext
openai-agents-base/
├── src/
│   ├── agents/                 # All agent definitions and implementations
│   │   ├── base_agent.py       # Abstract base agent class
│   │   ├── planner_agent.py    # Planner Agent: generates TaskGraph
│   │   ├── orchestrator.py     # Orchestrator: manages workflow execution
│   │   ├── critic_agent.py     # Observer/Critic: evaluates execution steps
│   │   ├── hitl_agent.py       # HITL (Human-in-the-Loop) agent for approvals
│   │   └── worker_agents/      # Specialized agents for atomic tasks
│   ├── core/                   # Core logic and data structures
│   │   ├── task_graph.py       # Models: TaskGraph, TaskState, TaskStep
│   │   ├── contracts.py        # Contracts defining agent input/output
│   ├── policies/               # Policies and validation rules
│   │   ├── policy_gate.py      # Validation of TaskGraph against constraints
│   ├── tracing/                # Tracing and debugging tools
│   │   ├── trace_logger.py
│   ├── flows/                  # Predefined workflows and task flows
│   │   ├── base_flow.py        # Generic execution flow
│   │   └── task_flow.py        # Example workflow
│   ├── utils/                  # Utilities and shared helpers
│   │   ├── logger.py
│   │   ├── serializers.py
├── docs/
│   ├── architecture.md         # Documentation for architecture and system design
├── tests/
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
├── .github/
│   └── workflows/ci.yml        # CI/CD workflows
├── pyproject.toml              # Python project configuration
└── README.md                   # Repository overview and usage
```

## Execution Cycle

### Step-by-Step Process:

1. **Task**: The high-level intent from a user.
2. **Planner Agent**: Converts `TaskIntent` into a `TaskGraph` (a plan of steps to execute).
3. **PolicyGate**: Validates the TaskGraph according to policies (budget, safety, risks).
4. **Orchestrator**: Manages execution, delegates steps to Worker Agents, and tracks progress.
5. **Worker Agents**: Perform atomic tasks defined in TaskGraph, report results back.
6. **Observer/Critic**: Evaluates completed steps, monitors quality, and sends feedback.
7. **Human-in-the-Loop (HITL)**: Engages humans for critical decisions or approvals.
8. **Tracing**: Logs all execution details for debugging and optimization.

### Detailed Execution Cycle

#### 1. TaskIntent

- **Purpose**: `TaskIntent` captures the high-level user goal that starts the workflow. It describes what the user wants to achieve before the system decides which agents, tools, or handoffs are required.
- **Data Contract**: The minimal contract should include input metadata such as a unique request identifier, the original user prompt, normalized intent text, optional constraints, and a short description of the expected outcome.
- **Relation**: `TaskIntent` is the input to the `PlannerAgent`, which converts a user-facing request into a deterministic execution plan instead of relying on implicit agent behavior.

#### 2. PlannerAgent → TaskGraph

- **Purpose**: The `PlannerAgent` transforms `TaskIntent` into a `TaskGraph` so the workflow is organized as explicit atomic steps that can be validated, executed, retried, and traced.
- **Data Contract**: `TaskGraph` should describe ordered or dependency-based `TaskStep` entries. Each `TaskStep` should include fields such as `name`, `description`, `agent_spec`, `inputs`, `expected_output`, `dependencies`, and optional execution constraints. The `agent_spec` is the bridge to the SDK layer because it defines which agent configuration, tools, handoffs, and structured output contract should be used for the step.
- **Relation**: The resulting `TaskGraph` is passed to `PolicyGate`, which evaluates whether the planned steps are safe, valid, and allowed to run.

#### 3. PolicyGate

- **Purpose**: `PolicyGate` validates the planned graph before execution begins. This stage enforces budget limits, safety rules, approval requirements, and handoff restrictions so that execution remains compliant and predictable.
- **Data Contract**: A policy decision should capture fields such as `risk_level`, `input_validation`, `budget_status`, `handoff_check`, `required_approval`, and a list of blocking or non-blocking policy findings.
- **Relation**: The policy result determines whether the `Orchestrator` can continue immediately, must pause for approval, or must reject or revise the graph.

#### 4. Orchestrator → Worker Agents Execution

- **Purpose**: The `Orchestrator` manages workflow state, selects the next executable step, delegates work to the correct agent, and tracks progress across the full graph. In SDK terms, this is the coordination layer that decides when a step should be executed through a runner-driven agent invocation.
- **Data Contract**: Each step should move through explicit execution states such as `pending`, `in_progress`, `completed`, `failed`, `blocked`, or `paused`, together with timestamps, retry counters, and references to produced outputs.
- **Relation**: The `Orchestrator` delegates each atomic `TaskStep` to the appropriate Worker Agent and receives the resulting execution artifacts back for state updates.

#### 5. Worker Agents Execution

- **Purpose**: Worker Agents perform the concrete atomic tasks defined in the graph, such as calling tools, using handoffs, producing structured outputs, or completing specialized domain actions. In practice, these map naturally to OpenAI Agents SDK `Agent` definitions configured for a single well-bounded responsibility.
- **Data Contract**: A standard worker response should include `result`, `success`, `errors` when applicable, trace logs, tool activity, and any structured output expected by the corresponding `TaskStep`.
- **Relation**: Worker Agents return outcomes to the `Orchestrator`, which records the result and determines whether to continue, retry, branch, or escalate.

#### 6. Observer/Critic Evaluation

- **Purpose**: The `Observer` or `Critic` evaluates completed step results to improve workflow quality, detect weak outputs, and determine whether the current plan still satisfies the original intent. This stage can use trace data, hooks, and validation outputs emitted during SDK execution.
- **Data Contract**: Evaluation records should reference the executed step, quality metrics, validation results, critique notes, and trace-linked evidence explaining why a step passed, failed, or should be reworked.
- **Relation**: If the evaluation detects gaps or low-quality results, it creates a feedback loop to the `PlannerAgent` for re-planning, refinement, or selective graph regeneration.

#### 7. Human-in-the-Loop (HITL)

- **Purpose**: HITL introduces human review for high-risk, ambiguous, or business-critical decisions that should not be resolved automatically.
- **Data Contract**: A HITL request should include the current context, identified risks, the pending decision, available options, and any adjustments needed for execution to continue safely.
- **Relation**: HITL is triggered by `PolicyGate` or the `Orchestrator` when manual intervention is required before the workflow can proceed.

#### 8. Tracing & Observability

- **Purpose**: Tracing and observability provide the detailed runtime visibility needed for debugging, auditing, optimization, and understanding how the SDK-based workflow behaves across agents, tools, handoffs, and lifecycle hooks.
- **Data Contract**: Trace data should include trace identifiers, span or event identifiers, input and output snapshots, tool calls, handoff events, execution timings, usage metrics, and status change logs for each step.
- **Relation**: Observability spans the entire execution cycle and gives every component shared evidence for diagnostics, quality review, and future optimization of planning and execution behavior.
