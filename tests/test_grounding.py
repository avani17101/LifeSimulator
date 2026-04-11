"""Test statistical grounding."""

from life_simulator.data.distributions import MockGrounding


def test_salary_range_known_role():
    g = MockGrounding()
    p25, med, p75 = g.salary_range("Software Engineer", "San Francisco", 5)
    # Mid-level SWE in SF: should be COL-adjusted
    assert p25 > 100_000  # base 105k * 1.82
    assert med > p25
    assert p75 > med


def test_salary_range_unknown_role():
    g = MockGrounding()
    p25, med, p75 = g.salary_range("Underwater Basket Weaver", "Austin", 5)
    # Should return default mid-level range * Austin COL
    assert p25 > 0
    assert med > p25


def test_col_fuzzy_match():
    g = MockGrounding()
    assert g.cost_of_living_index("San Francisco") == 1.82
    assert g.cost_of_living_index("san francisco") == 1.82  # case-insensitive
    assert g.cost_of_living_index("Unknown City") == 1.0  # default


def test_career_transition_prob():
    g = MockGrounding()
    p = g.career_transition_probability("Software Engineer", "Engineering Manager")
    assert 0 < p < 1
    # Unknown transition should return low default
    p2 = g.career_transition_probability("Chef", "Astronaut")
    assert p2 == 0.02


def test_health_outcomes():
    g = MockGrounding()
    probs = g.health_outcome_probability(30, "good", 5.0)
    assert abs(sum(probs.values()) - 1.0) < 0.01
    # High stress should increase decline probability
    probs_stressed = g.health_outcome_probability(30, "good", 9.0)
    assert probs_stressed["fair"] > probs["fair"]
