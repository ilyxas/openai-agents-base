"""Unit tests for deterministic task graph and orchestrator prototypes."""

from __future__ import annotations

import unittest

from src.agents.critic_agent import CriticAgent
from src.agents.orchestrator import Orchestrator, RunState
from src.agents.planner_agent import PlannerAgent
from src.core.task_graph import TaskState
from src.policies.policy_gate import PolicyGate


class _SequenceExecutor:
    def __init__(self) -> None:
        self.execution_order: list[str] = []

    def execute(self, step):
        self.execution_order.append(step.step_id)
        return {"status": "ok", "step": step.step_id}


class _RevisionExecutor:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, step):
        self.calls += 1
        if self.calls == 1:
            return {"status": "retry"}
        return {"status": "ok"}


class OrchestratorTaskGraphTests(unittest.TestCase):
    def setUp(self) -> None:
        self.planner = PlannerAgent()

    def test_orchestrator_runs_steps_in_dependency_order(self) -> None:
        graph = self.planner.plan(
            [
                {"step_id": "plan", "description": "Create plan", "agent_name": "repo"},
                {
                    "step_id": "execute",
                    "description": "Execute plan",
                    "agent_name": "repo",
                    "dependencies": ["plan"],
                },
            ]
        )
        orchestrator = Orchestrator(
            graph=graph,
            policy_gate=PolicyGate(available_agents={"repo"}),
            critic=CriticAgent(),
        )
        executor = _SequenceExecutor()

        state = orchestrator.run(executor)

        self.assertEqual(state, RunState.COMPLETED)
        self.assertEqual(executor.execution_order, ["plan", "execute"])
        self.assertEqual(graph.get_step("plan").state, TaskState.COMPLETED)
        self.assertEqual(graph.get_step("execute").state, TaskState.COMPLETED)

    def test_orchestrator_handles_revision_then_completion(self) -> None:
        graph = self.planner.plan(
            [{"step_id": "step-1", "description": "Run", "agent_name": "repo"}]
        )
        orchestrator = Orchestrator(
            graph=graph,
            policy_gate=PolicyGate(available_agents={"repo"}),
            critic=CriticAgent(),
            max_retries=2,
        )

        state = orchestrator.run(_RevisionExecutor())

        self.assertEqual(state, RunState.COMPLETED)
        self.assertEqual(graph.get_step("step-1").state, TaskState.COMPLETED)
        self.assertEqual(graph.get_step("step-1").retries, 1)

    def test_policy_gate_rejects_unknown_agent(self) -> None:
        graph = self.planner.plan(
            [{"step_id": "step-1", "description": "Run", "agent_name": "unknown"}]
        )
        orchestrator = Orchestrator(
            graph=graph,
            policy_gate=PolicyGate(available_agents={"repo"}),
            critic=CriticAgent(),
        )

        state = orchestrator.run(_SequenceExecutor())

        self.assertEqual(state, RunState.FAILED)
        self.assertEqual(graph.get_step("step-1").state, TaskState.REJECTED)


if __name__ == "__main__":
    unittest.main()
