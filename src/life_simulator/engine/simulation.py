"""Simulation engine: orchestrates multi-step, multi-branch simulations."""

from rich.progress import Progress, SpinnerColumn, TextColumn

from life_simulator.engine.world_model import WorldModel
from life_simulator.models.decision import Decision, DecisionOption
from life_simulator.models.person_state import PersonState
from life_simulator.models.simulation_tree import SimNode, SimTree


# Neutral "continue" action for subsequent years
_INERTIA = DecisionOption(
    id="continue",
    label="Continue on current path",
    description="Stay the course with current life trajectory, no major changes.",
)


class SimulationEngine:
    """Runs multi-step, multi-branch life simulations."""

    def __init__(
        self,
        world_model: WorldModel,
        steps: int = 5,
        start_year: int = 2026,
    ):
        self.world_model = world_model
        self.steps = steps
        self.start_year = start_year

    def simulate(
        self, initial_state: PersonState, decision: Decision
    ) -> SimTree:
        """Run simulation for all decision options."""
        root = SimNode(year=self.start_year, state=initial_state)

        total_calls = len(decision.options) * self.steps
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(
                f"Simulating {len(decision.options)} paths × {self.steps} years...",
                total=total_calls,
            )

            for option in decision.options:
                branch = self._simulate_branch(
                    initial_state, option, progress, task
                )
                root.children.append(branch)

        return SimTree(root=root, decision=decision)

    def _simulate_branch(
        self,
        state: PersonState,
        option: DecisionOption,
        progress: Progress,
        task,
    ) -> SimNode:
        """Simulate one decision branch forward through time."""
        current = state
        nodes: list[SimNode] = []

        for step in range(self.steps):
            year = self.start_year + step + 1
            action = option if step == 0 else _INERTIA

            progress.update(
                task,
                description=f"[{option.label}] Year {year}...",
                advance=1,
            )

            new_state, confidence = self.world_model.transition(
                current, action, year_delta=1
            )

            node = SimNode(
                year=year,
                state=new_state,
                action_taken=option.id if step == 0 else "continue",
                confidence=confidence,
            )
            nodes.append(node)
            current = new_state

        # Chain into linear branch
        for i in range(len(nodes) - 1):
            nodes[i].children = [nodes[i + 1]]

        return nodes[0]
