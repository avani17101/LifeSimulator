"""Test result export (JSON + Markdown)."""

import tempfile
from pathlib import Path

from life_simulator.export import export_json, export_markdown
from life_simulator.models.decision import Decision, DecisionOption
from life_simulator.models.person_state import (
    CareerState,
    EducationLevel,
    FinancialState,
    PersonState,
)
from life_simulator.models.simulation_tree import SimNode, SimTree


def _build_tree() -> SimTree:
    state = PersonState(
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
        narrative="Starting point.",
    )
    state2 = state.model_copy(update={
        "age": 29,
        "narrative": "Got promoted to senior.",
        "finances": FinancialState(
            annual_income=180_000,
            savings=100_000,
            debt=20_000,
            monthly_expenses=5_800,
            investment_portfolio=55_000,
        ),
    })

    root = SimNode(year=2026, state=state)
    child = SimNode(year=2027, state=state2, action_taken="stay", confidence=0.75)
    root.children = [child]

    decision = Decision(
        question="What next?",
        options=[DecisionOption(id="stay", label="Stay", description="Stay put")],
    )
    return SimTree(root=root, decision=decision)


def test_export_json():
    tree = _build_tree()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = export_json(tree, Path(tmpdir))
        assert path.exists()
        assert path.suffix == ".json"
        content = path.read_text()
        assert "Software Engineer" in content
        assert "155000" in content or "155,000" in content or "155_000" in content


def test_export_markdown():
    tree = _build_tree()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = export_markdown(tree, Path(tmpdir))
        assert path.exists()
        assert path.suffix == ".md"
        content = path.read_text()
        assert "Life Simulation Report" in content
        assert "Software Engineer" in content
        assert "What next?" in content
        assert "Stay" in content


def test_export_creates_directory():
    tree = _build_tree()
    with tempfile.TemporaryDirectory() as tmpdir:
        nested = Path(tmpdir) / "deep" / "nested"
        path = export_json(tree, nested)
        assert path.exists()
        assert nested.exists()
