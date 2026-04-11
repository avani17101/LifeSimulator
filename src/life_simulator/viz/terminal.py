"""Rich-based terminal visualization for simulation results."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from life_simulator.models.simulation_tree import SimNode, SimTree


def _confidence_color(c: float) -> str:
    if c >= 0.7:
        return "green"
    if c >= 0.4:
        return "yellow"
    return "red"


def _money(v: float) -> str:
    if v < 0:
        return f"-${abs(v):,.0f}"
    return f"${v:,.0f}"


class TerminalVisualizer:
    def __init__(self):
        self.console = Console()

    def render(self, sim_tree: SimTree) -> None:
        """Render full simulation output."""
        self.console.print()
        self.render_tree(sim_tree)
        self.console.print()
        self.render_comparison(sim_tree)
        self.console.print()
        self.render_narratives(sim_tree)

    def render_tree(self, sim_tree: SimTree) -> None:
        """Render branching tree view."""
        tree = Tree(
            f"[bold cyan]Decision:[/] {sim_tree.decision.question}"
        )

        root = sim_tree.root
        self._add_node_label(tree, root, is_root=True)

        for child in root.children:
            self._add_branch(tree, child)

        self.console.print(tree)

    def render_comparison(self, sim_tree: SimTree) -> None:
        """Side-by-side comparison of final outcomes."""
        paths = sim_tree.all_paths()
        if not paths:
            return

        table = Table(
            title="Outcome Comparison (Final Year)",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Metric", style="bold", min_width=16)

        # Find option labels
        for path in paths:
            # path[1] is the first step after root
            option_id = path[1].action_taken if len(path) > 1 else "?"
            # Find the matching option label
            label = option_id
            for opt in sim_tree.decision.options:
                if opt.id == option_id:
                    label = opt.label
                    break
            table.add_column(label, min_width=18)

        metrics = [
            ("Job Title", lambda s: s.career.job_title),
            ("Income", lambda s: _money(s.finances.annual_income)),
            ("Net Worth", lambda s: _money(s.net_worth)),
            ("Savings", lambda s: _money(s.finances.savings)),
            ("Debt", lambda s: _money(s.finances.debt)),
            ("Location", lambda s: s.location),
            ("Health", lambda s: s.health.value),
            ("Relationship", lambda s: s.relationship.value),
            ("Satisfaction", lambda s: f"{s.life_satisfaction:.1f}/10"),
            ("Stress", lambda s: f"{s.stress_level:.1f}/10"),
            ("Confidence", lambda s: None),  # special handling
        ]

        for name, extractor in metrics:
            if name == "Confidence":
                row = [name] + [
                    f"{path[-1].confidence:.0%}" for path in paths
                ]
            else:
                row = [name] + [
                    extractor(path[-1].state) for path in paths
                ]
            table.add_row(*row)

        self.console.print(table)

    def render_narratives(self, sim_tree: SimTree) -> None:
        """Render narrative timeline for each path."""
        paths = sim_tree.all_paths()

        for path in paths:
            if len(path) < 2:
                continue

            option_id = path[1].action_taken
            label = option_id
            for opt in sim_tree.decision.options:
                if opt.id == option_id:
                    label = opt.label
                    break

            lines: list[str] = []
            for node in path[1:]:  # skip root
                s = node.state
                color = _confidence_color(node.confidence)
                lines.append(
                    f"  [{color}]{node.year}[/] | "
                    f"{s.career.job_title} | "
                    f"{_money(s.finances.annual_income)} | "
                    f"{s.narrative}"
                )

            body = "\n".join(lines)
            self.console.print(
                Panel(body, title=f"[bold]{label}[/]", border_style="blue")
            )

    def _add_branch(self, parent: Tree, node: SimNode) -> None:
        state = node.state
        color = _confidence_color(node.confidence)

        label = (
            f"[{color}]{node.year}[/] "
            f"{state.career.job_title} | "
            f"{_money(state.finances.annual_income)} | "
            f"Sat:{state.life_satisfaction:.1f}"
        )
        branch = parent.add(label)

        for child in node.children:
            self._add_branch(branch, child)

    def _add_node_label(
        self, tree: Tree, node: SimNode, is_root: bool = False
    ) -> None:
        if is_root:
            s = node.state
            tree.add(
                f"[dim]Now:[/] {s.career.job_title} @ {s.location} | "
                f"{_money(s.finances.annual_income)} | Age {s.age}"
            )
