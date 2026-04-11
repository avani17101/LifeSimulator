"""Export simulation results to JSON and Markdown."""

from datetime import datetime
from pathlib import Path

from life_simulator.models.simulation_tree import SimTree


def _money(v: float) -> str:
    if v < 0:
        return f"-${abs(v):,.0f}"
    return f"${v:,.0f}"


def export_json(sim_tree: SimTree, output_dir: Path) -> Path:
    """Save full simulation tree as JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"simulation_{ts}.json"
    path.write_text(sim_tree.model_dump_json(indent=2))
    return path


def export_markdown(sim_tree: SimTree, output_dir: Path) -> Path:
    """Save a human-readable markdown report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"simulation_{ts}.md"

    root_state = sim_tree.root.state
    paths = sim_tree.all_paths()

    lines = [
        "# Life Simulation Report",
        "",
        f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        "",
        "## Starting Point",
        "",
        f"- **Age:** {root_state.age}",
        f"- **Location:** {root_state.location}",
        f"- **Job:** {root_state.career.job_title} ({root_state.career.industry})",
        f"- **Income:** {_money(root_state.finances.annual_income)}",
        f"- **Net Worth:** {_money(root_state.net_worth)}",
        f"- **Health:** {root_state.health.value.title()}",
        f"- **Relationship:** {root_state.relationship.value.replace('_', ' ').title()}",
        "",
        "## Decision",
        "",
        f"**{sim_tree.decision.question}**",
        "",
    ]

    for opt in sim_tree.decision.options:
        lines.append(f"- **{opt.label}:** {opt.description}")
    lines.append("")

    # Outcome comparison
    lines.append("## Outcome Comparison")
    lines.append("")

    if paths:
        # Build markdown table
        headers = ["Metric"] + [_option_label(sim_tree, p) for p in paths]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        metrics = [
            ("Job Title", lambda s: s.career.job_title),
            ("Income", lambda s: _money(s.finances.annual_income)),
            ("Net Worth", lambda s: _money(s.net_worth)),
            ("Savings", lambda s: _money(s.finances.savings)),
            ("Debt", lambda s: _money(s.finances.debt)),
            ("Location", lambda s: s.location),
            ("Health", lambda s: s.health.value.title()),
            ("Satisfaction", lambda s: f"{s.life_satisfaction:.1f}/10"),
            ("Stress", lambda s: f"{s.stress_level:.1f}/10"),
        ]

        for name, extractor in metrics:
            row = [name] + [extractor(p[-1].state) for p in paths]
            lines.append("| " + " | ".join(row) + " |")

        lines.append("")

    # Detailed timelines
    lines.append("## Detailed Timelines")
    lines.append("")

    for path_nodes in paths:
        if len(path_nodes) < 2:
            continue
        label = _option_label(sim_tree, path_nodes)
        lines.append(f"### {label}")
        lines.append("")

        for node in path_nodes[1:]:
            s = node.state
            conf = f"{node.confidence:.0%}" if node.confidence else "N/A"
            lines.append(
                f"**{node.year}** — {s.career.job_title} | "
                f"{_money(s.finances.annual_income)} | "
                f"Confidence: {conf}"
            )
            lines.append(f"> {s.narrative}")
            lines.append("")

    path.write_text("\n".join(lines))
    return path


def _option_label(sim_tree: SimTree, path_nodes: list) -> str:
    """Get the option label for a path."""
    if len(path_nodes) < 2:
        return "?"
    option_id = path_nodes[1].action_taken
    for opt in sim_tree.decision.options:
        if opt.id == option_id:
            return opt.label
    return option_id or "?"
