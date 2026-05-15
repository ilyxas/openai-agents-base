"""Specialized WorkerAgent prototype for repository-oriented tasks."""

from __future__ import annotations

from src.core.task_graph import TaskStep


class RepoWorkerAgent:
    """Executes repository-focused task steps."""

    name = "RepoWorkerAgent"

    def execute(self, step: TaskStep) -> dict[str, object]:
        return {
            "status": "ok",
            "worker": self.name,
            "step_id": step.step_id,
            "description": step.description,
        }
