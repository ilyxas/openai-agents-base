"""Deterministic orchestrator coordinating task execution lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from src.agents.critic_agent import CriticAgent
from src.core.task_graph import TaskGraph, TaskState, TaskStep
from src.policies.policy_gate import PolicyGate


class RunState(str, Enum):
    """High-level run state model for orchestration."""

    INITIALIZED = "initialized"
    PLANNING = "planning"
    AUTHORIZING = "authorizing"
    EXECUTING = "executing"
    EVALUATING = "evaluating"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


class StepExecutor(Protocol):
    """Execution contract for worker-like executors."""

    def execute(self, step: TaskStep) -> object:
        """Execute a step and return result payload."""


class OrchestratorHook(Protocol):
    """Optional hook surface for lifecycle tracing."""

    def on_run_start(self, state: RunState) -> None:
        """Called when orchestration starts."""

    def on_step_state_change(self, step: TaskStep, state: TaskState) -> None:
        """Called on each step transition."""

    def on_run_end(self, state: RunState) -> None:
        """Called when orchestration ends."""


@dataclass(slots=True)
class Orchestrator:
    """Deterministic lifecycle controller for task graph execution."""

    graph: TaskGraph
    policy_gate: PolicyGate
    critic: CriticAgent
    max_retries: int = 1
    hook: OrchestratorHook | None = None
    run_state: RunState = RunState.INITIALIZED

    def run(self, executor: StepExecutor) -> RunState:
        self.run_state = RunState.PLANNING
        self._emit_run_start()

        while not self.graph.all_completed() and not self.graph.has_terminal_failure():
            ready_steps = self.graph.iter_ready_for_authorization()
            if not ready_steps:
                break

            for step in ready_steps:
                self.run_state = RunState.AUTHORIZING
                decision = self.policy_gate.evaluate(self.graph, step)
                if not decision.allowed:
                    self.graph.transition(step.step_id, TaskState.REJECTED, error=decision.reason)
                    self._emit_step(step)
                    continue

                self.graph.transition(step.step_id, TaskState.AUTHORIZED)
                self._emit_step(step)

                self.run_state = RunState.EXECUTING
                self.graph.transition(step.step_id, TaskState.RUNNING)
                self._emit_step(step)

                try:
                    result = executor.execute(step)
                except Exception as exc:  # pragma: no cover - safety path
                    self.graph.transition(step.step_id, TaskState.FAILED_TERMINAL, error=str(exc))
                    self._emit_step(step)
                    continue

                self.run_state = RunState.EVALUATING
                verdict = self.critic.evaluate(step, result)

                if verdict == CriticAgent.ACCEPT:
                    self.graph.transition(step.step_id, TaskState.COMPLETED, result=result)
                elif verdict == CriticAgent.REVISE and step.retries < self.max_retries:
                    step.retries += 1
                    self.graph.transition(step.step_id, TaskState.NEEDS_REVISION, result=result)
                elif verdict == CriticAgent.REPLAN:
                    self.graph.transition(step.step_id, TaskState.REPLANNED, result=result)
                else:
                    self.graph.transition(step.step_id, TaskState.FAILED_TERMINAL, result=result)
                self._emit_step(step)

        self.run_state = RunState.FINALIZING
        if self.graph.all_completed():
            self.run_state = RunState.COMPLETED
        elif self.graph.has_terminal_failure():
            self.run_state = RunState.FAILED
        self._emit_run_end()
        return self.run_state

    def _emit_run_start(self) -> None:
        if self.hook is not None:
            self.hook.on_run_start(self.run_state)

    def _emit_step(self, step: TaskStep) -> None:
        if self.hook is not None:
            self.hook.on_step_state_change(step, step.state)

    def _emit_run_end(self) -> None:
        if self.hook is not None:
            self.hook.on_run_end(self.run_state)
