"""Deterministic policy validation for task-step authorization."""

from __future__ import annotations

from dataclasses import dataclass

from src.core.task_graph import TaskGraph, TaskStep


@dataclass(slots=True)
class PolicyDecision:
    """Policy gate decision for a step."""

    allowed: bool
    reason: str = ""


class PolicyGate:
    """Simple policy gate validating dependencies and agent registration."""

    def __init__(self, available_agents: set[str] | None = None) -> None:
        self.available_agents = available_agents or set()

    def evaluate(self, graph: TaskGraph, step: TaskStep) -> PolicyDecision:
        if self.available_agents and step.agent_name not in self.available_agents:
            return PolicyDecision(False, f"unknown agent: {step.agent_name}")
        if not graph.is_dependency_satisfied(step):
            return PolicyDecision(False, "dependencies not completed")
        return PolicyDecision(True)
