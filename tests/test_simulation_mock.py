"""End-to-end simulation test with mocked LLM."""

from unittest.mock import MagicMock

from life_simulator.data.distributions import MockGrounding
from life_simulator.engine.simulation import SimulationEngine
from life_simulator.engine.world_model import WorldModel
from life_simulator.models.decision import Decision, DecisionOption
from life_simulator.models.person_state import (
    CareerState,
    EducationLevel,
    FinancialState,
    PersonState,
)


def _fake_llm_response(step: int = 0) -> dict:
    return {
        "age": 29 + step,
        "education": "bachelors",
        "location": "San Francisco",
        "career": {
            "job_title": "Senior Software Engineer",
            "industry": "Technology",
            "years_in_role": 1,
            "years_experience": 6 + step,
            "is_employed": True,
        },
        "finances": {
            "annual_income": 175_000,
            "savings": 95_000 + step * 15_000,
            "debt": 20_000,
            "monthly_expenses": 5_800,
            "investment_portfolio": 55_000 + step * 10_000,
        },
        "health": "good",
        "relationship": "partnered",
        "dependents": 0,
        "life_satisfaction": 7.0,
        "stress_level": 5.5,
        "narrative": f"Year {step + 1}: Promoted and settling into the new role.",
        "confidence": 0.7,
    }


def test_full_simulation_mock():
    grounding = MockGrounding()

    # Mock the LLM client
    mock_llm = MagicMock()
    call_count = 0

    def side_effect(prompt):
        nonlocal call_count
        result = _fake_llm_response(call_count)
        call_count += 1
        return result

    mock_llm.generate_transition = MagicMock(side_effect=side_effect)

    world_model = WorldModel(grounding=grounding, llm=mock_llm)
    engine = SimulationEngine(world_model=world_model, steps=3)

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
    )

    decision = Decision(
        question="What next?",
        options=[
            DecisionOption(id="stay", label="Stay", description="Stay put"),
            DecisionOption(id="go", label="Go", description="Leave"),
        ],
    )

    tree = engine.simulate(state, decision)

    # Should have 2 branches (one per option)
    assert len(tree.root.children) == 2

    # Each branch should have 3 steps
    paths = tree.all_paths()
    assert len(paths) == 2
    for path in paths:
        assert len(path) == 4  # root + 3 steps

    # Verify final states have narratives
    for path in paths:
        assert path[-1].state.narrative != ""

    # Total LLM calls: 2 options * 3 steps = 6
    assert mock_llm.generate_transition.call_count == 6


def test_visualization_no_crash():
    """Verify visualization doesn't crash on mock data."""
    from life_simulator.viz.terminal import TerminalVisualizer
    from life_simulator.models.simulation_tree import SimNode, SimTree

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
        narrative="Test narrative.",
    )

    state2 = state.model_copy(update={
        "age": 29,
        "narrative": "Got promoted.",
        "finances": FinancialState(
            annual_income=175_000,
            savings=95_000,
            debt=20_000,
            monthly_expenses=5_800,
            investment_portfolio=55_000,
        ),
    })

    root = SimNode(year=2026, state=state)
    child = SimNode(year=2027, state=state2, action_taken="stay", confidence=0.7)
    root.children = [child]

    decision = Decision(
        question="What next?",
        options=[DecisionOption(id="stay", label="Stay", description="Stay")],
    )
    tree = SimTree(root=root, decision=decision)

    viz = TerminalVisualizer()
    # Should not crash
    viz.render(tree)
