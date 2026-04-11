"""CLI entrypoint for life simulator."""

import json
import os
from pathlib import Path

import typer
from rich.console import Console

from life_simulator.data.distributions import MockGrounding
from life_simulator.engine.simulation import SimulationEngine
from life_simulator.engine.world_model import WorldModel
from life_simulator.export import export_json, export_markdown
from life_simulator.llm.client import LLMClient
from life_simulator.models.decision import Decision, DecisionOption
from life_simulator.models.person_state import (
    CareerState,
    EducationLevel,
    FinancialState,
    PersonState,
)
from life_simulator.viz.terminal import TerminalVisualizer

app = typer.Typer(
    name="lifesim",
    help="Life Decision Simulator — explore your future paths.",
    no_args_is_help=True,
)
console = Console()

DEFAULT_MODEL = "claude-sonnet-4-20250514"
OUTPUT_DIR = Path.home() / ".lifesim" / "results"

MODEL_HELP = (
    "Model to use. Examples:\n"
    "  claude-sonnet-4-20250514  (Anthropic, needs ANTHROPIC_API_KEY)\n"
    "  ollama/llama3.1           (local Ollama, free)\n"
    "  ollama/qwen2.5            (local Ollama, free)\n"
    "  openai/gpt-4o             (OpenAI, needs OPENAI_API_KEY)\n"
    "  openrouter/meta-llama/llama-3.1-70b-instruct (needs OPENROUTER_API_KEY)\n"
)


def _check_api_key(model: str) -> None:
    """Check that required API keys are set for cloud providers."""
    if model.startswith("claude") or model.startswith("anthropic/"):
        if not os.environ.get("ANTHROPIC_API_KEY"):
            console.print(
                "[bold red]Error:[/] ANTHROPIC_API_KEY not set.\n"
                "\n"
                "  [cyan]export ANTHROPIC_API_KEY='sk-ant-...'[/]\n"
                "\n"
                "Or use a free local model: [cyan]--model ollama/llama3.1[/]\n"
            )
            raise typer.Exit(1)
    elif model.startswith("openai/"):
        if not os.environ.get("OPENAI_API_KEY"):
            console.print("[bold red]Error:[/] OPENAI_API_KEY not set.")
            raise typer.Exit(1)
    elif model.startswith("openrouter/"):
        if not os.environ.get("OPENROUTER_API_KEY"):
            console.print("[bold red]Error:[/] OPENROUTER_API_KEY not set.")
            raise typer.Exit(1)
    # ollama and other local providers need no key


@app.command()
def new(
    steps: int = typer.Option(5, "--steps", "-s", help="Years to simulate"),
    model: str = typer.Option(DEFAULT_MODEL, "--model", "-m", help=MODEL_HELP),
    save: bool = typer.Option(True, "--save/--no-save", help="Save results to ~/.lifesim/results"),
) -> None:
    """Interactively build a scenario and run a simulation."""
    _check_api_key(model)

    from life_simulator.interactive import build_scenario_interactive

    state, decision = build_scenario_interactive()
    _run_simulation(state, decision, steps, model, save=save)


@app.command()
def simulate(
    config: str = typer.Option(
        ..., "--config", "-c", help="Path to JSON scenario config"
    ),
    steps: int = typer.Option(5, "--steps", "-s", help="Years to simulate"),
    model: str = typer.Option(DEFAULT_MODEL, "--model", "-m", help=MODEL_HELP),
    save: bool = typer.Option(True, "--save/--no-save", help="Save results to ~/.lifesim/results"),
) -> None:
    """Run a life decision simulation from a config file."""
    _check_api_key(model)

    path = Path(config)
    if not path.exists():
        console.print(f"[red]Config file not found: {config}[/]")
        raise typer.Exit(1)

    data = json.loads(path.read_text())
    initial_state = PersonState.model_validate(data["person"])
    decision = Decision.model_validate(data["decision"])

    _run_simulation(initial_state, decision, steps, model, save=save)


@app.command()
def example(
    steps: int = typer.Option(5, "--steps", "-s", help="Years to simulate"),
    model: str = typer.Option(DEFAULT_MODEL, "--model", "-m", help=MODEL_HELP),
    save: bool = typer.Option(True, "--save/--no-save", help="Save results to ~/.lifesim/results"),
) -> None:
    """Run the built-in career crossroads example."""
    _check_api_key(model)

    console.print("[bold cyan]Career Crossroads Example[/]")
    console.print("28-year-old software engineer in San Francisco deciding between:")
    console.print("  1. Pursue an MBA at a top program")
    console.print("  2. Join an early-stage startup as co-founder")
    console.print("  3. Stay and grow at current company")
    console.print()

    initial_state = PersonState(
        age=28,
        education=EducationLevel.BACHELORS,
        location="San Francisco",
        career=CareerState(
            job_title="Software Engineer",
            industry="Technology",
            years_in_role=3,
            years_experience=5,
        ),
        finances=FinancialState(
            annual_income=155_000,
            savings=80_000,
            debt=25_000,
            monthly_expenses=5_500,
            investment_portfolio=40_000,
        ),
        health="good",
        relationship="partnered",
        life_satisfaction=6.5,
        stress_level=6.0,
        narrative="Working at a mid-size tech company, feeling ready for a change.",
    )

    decision = Decision(
        question="What should I do with my career at this crossroads?",
        options=[
            DecisionOption(
                id="mba",
                label="Pursue MBA",
                description=(
                    "Leave job to attend a top-20 MBA program. "
                    "2-year program costing ~$150K total. "
                    "Aiming for product management or consulting exit."
                ),
                estimated_duration_years=2,
                tags=["education", "career", "financial"],
            ),
            DecisionOption(
                id="startup",
                label="Co-found a startup",
                description=(
                    "Leave job to co-found a B2B SaaS startup with a college friend. "
                    "Initial funding from savings + small angel round. "
                    "High risk, potentially high reward."
                ),
                estimated_duration_years=3,
                tags=["career", "financial", "entrepreneurship"],
            ),
            DecisionOption(
                id="stay",
                label="Stay and grow",
                description=(
                    "Stay at current company, pursue promotion to senior engineer "
                    "and eventually engineering manager. Stable path with "
                    "predictable growth."
                ),
                estimated_duration_years=1,
                tags=["career", "stability"],
            ),
        ],
        context="Has 5 years of experience, strong technical skills, a partner who is supportive but risk-averse.",
    )

    _run_simulation(initial_state, decision, steps, model, save=save)


@app.command()
def history() -> None:
    """List past simulation results."""
    if not OUTPUT_DIR.exists():
        console.print("[dim]No simulations saved yet. Run [cyan]lifesim new[/cyan] to get started.[/]")
        return

    md_files = sorted(OUTPUT_DIR.glob("simulation_*.md"), reverse=True)
    if not md_files:
        console.print("[dim]No simulations saved yet.[/]")
        return

    console.print(f"[bold cyan]Saved Simulations[/] ({OUTPUT_DIR})\n")
    for f in md_files[:20]:
        name = f.stem
        parts = name.split("_")
        if len(parts) >= 3:
            date_str = parts[1]
            time_str = parts[2]
            display = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]} {time_str[:2]}:{time_str[2:4]}"
        else:
            display = f.name

        text = f.read_text()
        question = ""
        for line in text.split("\n"):
            if line.startswith("**") and line.endswith("**") and "?" in line:
                question = line.strip("*")
                break

        json_path = f.with_suffix(".json")
        has_json = " [dim](+json)[/]" if json_path.exists() else ""

        console.print(f"  [cyan]{display}[/]  {question}{has_json}")
        console.print(f"    [dim]{f}[/]")


def _run_simulation(
    initial_state: PersonState,
    decision: Decision,
    steps: int,
    model: str,
    save: bool = True,
) -> None:
    grounding = MockGrounding()

    try:
        llm = LLMClient(model=model)
    except Exception as e:
        console.print(f"[bold red]Failed to initialize LLM client:[/] {e}")
        raise typer.Exit(1)

    world_model = WorldModel(grounding=grounding, llm=llm)
    engine = SimulationEngine(world_model=world_model, steps=steps)

    console.print(f"\n[dim]Simulating {len(decision.options)} paths × {steps} years • {llm.display_name}[/]")
    if llm.provider == "ollama":
        console.print("[dim]Using local Ollama (free, no API key needed)[/]")
    console.print()

    try:
        result = engine.simulate(initial_state, decision)
    except Exception as e:
        console.print(f"\n[bold red]Simulation failed:[/] {e}")
        if llm.provider == "ollama":
            console.print("[dim]Make sure Ollama is running: ollama serve[/]")
        raise typer.Exit(1)

    viz = TerminalVisualizer()
    viz.render(result)

    cost_str = f"${llm.estimated_cost:.3f}" if llm.estimated_cost > 0 else "free (local)"
    console.print(
        f"\n[dim]Cost: {cost_str} "
        f"({llm.total_input_tokens} in / {llm.total_output_tokens} out)[/]"
    )

    if save:
        json_path = export_json(result, OUTPUT_DIR)
        md_path = export_markdown(result, OUTPUT_DIR)
        console.print("\n[green]Results saved:[/]")
        console.print(f"  [dim]{md_path}[/]")
        console.print(f"  [dim]{json_path}[/]")


if __name__ == "__main__":
    app()
