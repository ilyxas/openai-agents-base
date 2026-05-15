"""Specialized WorkerAgent prototype for test execution tasks."""

from __future__ import annotations

from src.core.task_graph import TaskStep


class TestWorkerAgent:
    """Executes test-focused task steps."""

    name = "TestWorkerAgent"

    def execute(self, step: TaskStep) -> dict[str, object]:
        return {
            "status": "ok",
            "worker": self.name,
            "step_id": step.step_id,
            "description": step.description,
        }
