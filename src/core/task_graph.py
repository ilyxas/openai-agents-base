"""Core TaskGraph models for deterministic execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskState(str, Enum):
    """Supported lifecycle states for task steps."""

    PROPOSED = "proposed"
    AUTHORIZED = "authorized"
    BLOCKED_HUMAN = "blocked_human"
    RUNNING = "running"
    COMPLETED = "completed"
    NEEDS_REVISION = "needs_revision"
    REPLANNED = "replanned"
    REJECTED = "rejected"
    FAILED_TERMINAL = "failed_terminal"


_ALLOWED_TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.PROPOSED: {TaskState.AUTHORIZED, TaskState.BLOCKED_HUMAN, TaskState.REJECTED, TaskState.REPLANNED},
    TaskState.AUTHORIZED: {TaskState.RUNNING, TaskState.REJECTED, TaskState.FAILED_TERMINAL},
    TaskState.BLOCKED_HUMAN: {TaskState.AUTHORIZED, TaskState.REJECTED, TaskState.REPLANNED},
    TaskState.RUNNING: {TaskState.COMPLETED, TaskState.NEEDS_REVISION, TaskState.FAILED_TERMINAL},
    TaskState.NEEDS_REVISION: {TaskState.AUTHORIZED, TaskState.REPLANNED, TaskState.FAILED_TERMINAL},
    TaskState.REPLANNED: {TaskState.AUTHORIZED, TaskState.REJECTED, TaskState.BLOCKED_HUMAN},
    TaskState.COMPLETED: set(),
    TaskState.REJECTED: set(),
    TaskState.FAILED_TERMINAL: set(),
}


@dataclass(slots=True)
class TaskStep:
    """An atomic executable unit in a task graph."""

    step_id: str
    description: str
    agent_name: str
    dependencies: list[str] = field(default_factory=list)
    input_data: dict[str, Any] = field(default_factory=dict)
    expected_output: str | None = None
    state: TaskState = TaskState.PROPOSED
    result: Any = None
    error: str | None = None
    retries: int = 0


class TaskGraph:
    """A deterministic graph of task steps and their state."""

    def __init__(self) -> None:
        self.steps: dict[str, TaskStep] = {}
        self.order: list[str] = []

    def add_step(self, step: TaskStep) -> None:
        if step.step_id in self.steps:
            raise ValueError(f"Duplicate step id: {step.step_id}")
        for dep in step.dependencies:
            if dep not in self.steps:
                raise ValueError(f"Unknown dependency: {dep}")
        self.steps[step.step_id] = step
        self.order.append(step.step_id)

    def get_step(self, step_id: str) -> TaskStep:
        try:
            return self.steps[step_id]
        except KeyError as exc:
            raise ValueError(f"Unknown step id: {step_id}") from exc

    def is_dependency_satisfied(self, step: TaskStep) -> bool:
        return all(self.steps[dep].state == TaskState.COMPLETED for dep in step.dependencies)

    def iter_ready_for_authorization(self) -> list[TaskStep]:
        candidates = {TaskState.PROPOSED, TaskState.NEEDS_REVISION, TaskState.REPLANNED}
        return [
            self.steps[step_id]
            for step_id in self.order
            if self.steps[step_id].state in candidates and self.is_dependency_satisfied(self.steps[step_id])
        ]

    def transition(
        self,
        step_id: str,
        new_state: TaskState,
        *,
        result: Any = None,
        error: str | None = None,
    ) -> TaskStep:
        step = self.get_step(step_id)
        allowed = _ALLOWED_TRANSITIONS[step.state]
        if new_state not in allowed:
            raise ValueError(f"Invalid transition: {step.state.value} -> {new_state.value}")

        step.state = new_state
        step.result = result if result is not None else step.result
        step.error = error
        return step

    def all_completed(self) -> bool:
        return bool(self.steps) and all(step.state == TaskState.COMPLETED for step in self.steps.values())

    def has_terminal_failure(self) -> bool:
        return any(step.state in {TaskState.REJECTED, TaskState.FAILED_TERMINAL} for step in self.steps.values())
