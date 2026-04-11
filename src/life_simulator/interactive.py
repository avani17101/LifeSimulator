"""Interactive scenario builder using Rich prompts."""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt
from rich.table import Table

from life_simulator.models.decision import Decision, DecisionOption
from life_simulator.models.person_state import (
    CareerState,
    EducationLevel,
    FinancialState,
    HealthStatus,
    PersonState,
    RelationshipStatus,
)

console = Console()

EDUCATION_CHOICES = {
    "1": EducationLevel.HIGH_SCHOOL,
    "2": EducationLevel.ASSOCIATES,
    "3": EducationLevel.BACHELORS,
    "4": EducationLevel.MASTERS,
    "5": EducationLevel.MBA,
    "6": EducationLevel.PHD,
    "7": EducationLevel.PROFESSIONAL,
}

HEALTH_CHOICES = {
    "1": HealthStatus.EXCELLENT,
    "2": HealthStatus.GOOD,
    "3": HealthStatus.FAIR,
    "4": HealthStatus.POOR,
}

RELATIONSHIP_CHOICES = {
    "1": RelationshipStatus.SINGLE,
    "2": RelationshipStatus.PARTNERED,
    "3": RelationshipStatus.MARRIED,
    "4": RelationshipStatus.DIVORCED,
}


def _select(prompt_text: str, choices: dict[str, object], default: str = "2") -> object:
    """Display numbered choices and return the selected value."""
    lines = []
    for key, val in choices.items():
        label = val.value if hasattr(val, "value") else str(val)
        label = label.replace("_", " ").title()
        lines.append(f"  [cyan]{key}[/]) {label}")
    console.print("\n".join(lines))
    choice = Prompt.ask(prompt_text, choices=list(choices.keys()), default=default)
    return choices[choice]


def _money_prompt(label: str, default: float) -> float:
    """Prompt for a dollar amount."""
    raw = Prompt.ask(f"  {label}", default=f"{default:,.0f}")
    # Strip $, commas, spaces
    cleaned = raw.replace("$", "").replace(",", "").replace(" ", "")
    return float(cleaned)


def build_scenario_interactive() -> tuple[PersonState, Decision]:
    """Walk the user through building a scenario interactively."""
    console.print(
        Panel(
            "[bold cyan]Life Simulator[/] — Interactive Scenario Builder\n"
            "Answer the prompts below to set up your simulation.\n"
            "Press Enter to accept [dim]default values[/].",
            border_style="cyan",
        )
    )

    # --- Person State ---
    console.print("\n[bold yellow]About You[/]")
    age = IntPrompt.ask("  Age", default=28)
    location = Prompt.ask("  City/Metro area", default="San Francisco")

    console.print("\n[bold yellow]Education[/]")
    education = _select("  Level", EDUCATION_CHOICES, default="3")

    console.print("\n[bold yellow]Career[/]")
    job_title = Prompt.ask("  Job title", default="Software Engineer")
    industry = Prompt.ask("  Industry", default="Technology")
    years_in_role = IntPrompt.ask("  Years in current role", default=3)
    years_experience = IntPrompt.ask("  Total years of experience", default=5)
    is_employed = Confirm.ask("  Currently employed?", default=True)

    console.print("\n[bold yellow]Finances[/]")
    annual_income = _money_prompt("Annual income ($)", 100_000)
    savings = _money_prompt("Savings ($)", 50_000)
    debt = _money_prompt("Debt ($)", 0)
    monthly_expenses = _money_prompt("Monthly expenses ($)", 4_000)
    investments = _money_prompt("Investment portfolio ($)", 20_000)

    console.print("\n[bold yellow]Life[/]")
    health = _select("  Health", HEALTH_CHOICES, default="2")
    relationship = _select("  Relationship", RELATIONSHIP_CHOICES, default="1")
    dependents = IntPrompt.ask("  Number of dependents", default=0)
    satisfaction = FloatPrompt.ask("  Life satisfaction (1-10)", default=7.0)
    stress = FloatPrompt.ask("  Stress level (1-10)", default=5.0)

    narrative = Prompt.ask(
        "\n  [bold]Describe your current situation[/] (1-2 sentences)",
        default="Looking to make a change and explore new opportunities.",
    )

    state = PersonState(
        age=age,
        education=education,
        location=location,
        career=CareerState(
            job_title=job_title,
            industry=industry,
            years_in_role=years_in_role,
            years_experience=years_experience,
            is_employed=is_employed,
        ),
        finances=FinancialState(
            annual_income=annual_income,
            savings=savings,
            debt=debt,
            monthly_expenses=monthly_expenses,
            investment_portfolio=investments,
        ),
        health=health,
        relationship=relationship,
        dependents=dependents,
        life_satisfaction=max(1.0, min(10.0, satisfaction)),
        stress_level=max(1.0, min(10.0, stress)),
        narrative=narrative,
    )

    # --- Decision ---
    console.print("\n[bold yellow]The Decision[/]")
    question = Prompt.ask(
        "  What decision are you facing?",
        default="What should I do next with my career?",
    )
    context = Prompt.ask(
        "  Any additional context? (optional)",
        default="",
    )

    num_options = IntPrompt.ask("  How many options are you considering?", default=2)
    num_options = max(2, min(5, num_options))

    options: list[DecisionOption] = []
    for i in range(num_options):
        console.print(f"\n  [bold cyan]Option {i + 1}[/]")
        label = Prompt.ask("    Short label", default=f"Option {i + 1}")
        description = Prompt.ask("    Description (what does this path look like?)")
        duration = FloatPrompt.ask("    Estimated duration (years)", default=1.0)
        option_id = label.lower().replace(" ", "_")[:20]
        options.append(
            DecisionOption(
                id=option_id,
                label=label,
                description=description,
                estimated_duration_years=duration,
            )
        )

    decision = Decision(question=question, options=options, context=context)

    # --- Confirmation ---
    console.print()
    _show_summary(state, decision)

    if not Confirm.ask("\n[bold]Run simulation with this scenario?[/]", default=True):
        console.print("[dim]Cancelled.[/]")
        raise SystemExit(0)

    return state, decision


def _show_summary(state: PersonState, decision: Decision) -> None:
    """Show a summary table before running."""
    table = Table(title="Your Scenario", show_header=False, border_style="cyan")
    table.add_column("Field", style="bold", min_width=20)
    table.add_column("Value", min_width=30)

    table.add_row("Age", str(state.age))
    table.add_row("Location", state.location)
    table.add_row("Education", state.education.value.replace("_", " ").title())
    table.add_row("Job", f"{state.career.job_title} ({state.career.industry})")
    table.add_row("Experience", f"{state.career.years_experience} years")
    table.add_row("Income", f"${state.finances.annual_income:,.0f}")
    table.add_row("Net Worth", f"${state.net_worth:,.0f}")
    table.add_row("Health", state.health.value.title())
    table.add_row("Relationship", state.relationship.value.replace("_", " ").title())
    table.add_row("Satisfaction", f"{state.life_satisfaction}/10")
    table.add_row("Stress", f"{state.stress_level}/10")
    table.add_section()
    table.add_row("Decision", decision.question)
    for i, opt in enumerate(decision.options, 1):
        table.add_row(f"  Option {i}", f"{opt.label} — {opt.description[:60]}")

    console.print(table)
