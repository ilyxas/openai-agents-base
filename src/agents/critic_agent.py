"""Observer/Critic agent prototype for evaluating execution results."""

from __future__ import annotations

from src.core.task_graph import TaskStep


class CriticAgent:
    """Returns deterministic verdicts on completed step outputs."""

    ACCEPT = "accept"
    REVISE = "revise"
    REPLAN = "replan"
    FAIL = "fail"

    def __init__(self, name: str = "CriticAgent") -> None:
        self.name = name

    def evaluate(self, step: TaskStep, result: object) -> str:
        if isinstance(result, dict):
            status = result.get("status")
            if status == "ok":
                return self.ACCEPT
            if status == "retry":
                return self.REVISE
            if status == "replan":
                return self.REPLAN
            if status == "fail":
                return self.FAIL

        if step.expected_output and isinstance(result, str) and step.expected_output in result:
            return self.ACCEPT
        return self.REVISE
