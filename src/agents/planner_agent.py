"""PlannerAgent prototype for creating TaskGraph plans."""

from __future__ import annotations

from src.core.task_graph import TaskGraph, TaskStep


class PlannerAgent:
    """Builds an initial task graph from atomic task definitions."""

    def __init__(self, name: str = "PlannerAgent") -> None:
        self.name = name

    def plan(self, task_definitions: list[dict[str, object]]) -> TaskGraph:
        graph = TaskGraph()
        for definition in task_definitions:
            graph.add_step(
                TaskStep(
                    step_id=str(definition["step_id"]),
                    description=str(definition.get("description", "")),
                    agent_name=str(definition["agent_name"]),
                    dependencies=[str(dep) for dep in definition.get("dependencies", [])],
                    input_data=dict(definition.get("input_data", {})),
                    expected_output=(
                        str(definition["expected_output"])
                        if definition.get("expected_output") is not None
                        else None
                    ),
                )
            )
        return graph
