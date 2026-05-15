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

The execution lifecycle transforms a high-level user intent into a structured workflow that is validated, executed, and evaluated iteratively, ensuring robustness and adaptability at each stage.

### Step-by-Step Process:

1. Task: The high-level intent or goal provided by a user to initiate the process.

2. Planner Agent:Converts the TaskIntent into a TaskGraph—a structured representation of the workflow with explicit steps, dependencies, and resource requirements.

• The TaskGraph may be revisited and adjusted dynamically based on feedback during execution.

3. PolicyGate:Evaluates the proposed TaskGraph to ensure compliance with predefined constraints:

• Budget limitations.

• Safety and risk assessments.

• Required tool availability and permissions.

4. Orchestrator:Orchestrates the execution process based on the validated TaskGraph, ensuring each step is executed at the right time and under the right conditions. The Orchestrator:

• Delegates atomic tasks to Worker Agents.

• Tracks progress and state changes (pending, in_progress, completed, failed, etc.).

• Responds to feedback or failures by retrying steps, initiating re-planning, or adjusting the workflow recursively.

5. Worker Agents:Execute the atomic TaskSteps as assigned by the Orchestrator. Each Worker Agent performs a bounded operation, such as generating content, performing computations, or interacting with external systems, and returns structured results.

6. Observer/Critic:Evaluates the outcomes of executed steps to ensure they meet defined quality standards. The Critic:

• Verifies whether outputs align with the TaskStep’s expected outcome.

• Provides feedback to the Orchestrator, potentially triggering adjustments, retries, or escalation to the Planner Agent for re-planning.

7. Human-in-the-Loop (HITL):For critical decisions or ambiguous tasks, the workflow pauses, and control is delegated to a human reviewer. The human decision is integrated back into the process, ensuring compliance with policy and correctness.

8. Tracing:A continuous tracing system logs all execution activities, including task delegation, outputs, state changes, retries, and feedback. Traces are used for debugging, auditing, and optimization of future workflows.


## Key Clarifications:

• The process is recursive, with the Orchestrator at the center of decision-making:

• Feedback from Observer/Critic or Worker Agents can trigger retries, adjustments, or re-planning through the Planner Agent.

• The Orchestrator ensures the workflow is adaptive and progresses iteratively, never as a static step-by-step sequence.

• The TaskGraph serves as a flexible blueprint rather than a fixed, immutable plan.
