"""Test core data models."""

from life_simulator.models.person_state import (
    CareerState,
    EducationLevel,
    FinancialState,
    PersonState,
)
from life_simulator.models.decision import Decision, DecisionOption
from life_simulator.models.simulation_tree import SimNode, SimTree


def _sample_state() -> PersonState:
    return PersonState(
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


def test_person_state_net_worth():
    state = _sample_state()
    assert state.net_worth == 80_000 + 40_000 - 25_000


def test_person_state_json_roundtrip():
    state = _sample_state()
    json_str = state.model_dump_json()
    restored = PersonState.model_validate_json(json_str)
    assert restored.age == state.age
    assert restored.finances.annual_income == state.finances.annual_income


def test_decision_model():
    d = Decision(
        question="What next?",
        options=[
            DecisionOption(id="a", label="Option A", description="Do A"),
            DecisionOption(id="b", label="Option B", description="Do B"),
        ],
    )
    assert len(d.options) == 2


def test_sim_tree_paths():
    state = _sample_state()
    root = SimNode(year=2026, state=state)
    child1 = SimNode(year=2027, state=state, action_taken="a")
    child2 = SimNode(year=2027, state=state, action_taken="b")
    leaf1 = SimNode(year=2028, state=state, action_taken="a")
    child1.children = [leaf1]
    root.children = [child1, child2]

    decision = Decision(
        question="Test?",
        options=[DecisionOption(id="a", label="A", description="A")],
    )
    tree = SimTree(root=root, decision=decision)
    paths = tree.all_paths()
    assert len(paths) == 2  # two leaf nodes
    assert len(paths[0]) == 3  # root -> child1 -> leaf1
    assert len(paths[1]) == 2  # root -> child2
