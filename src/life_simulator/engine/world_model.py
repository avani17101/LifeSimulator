"""Hybrid transition engine: statistical grounding + LLM reasoning."""

from life_simulator.data.grounding import StatisticalGrounding
from life_simulator.llm.client import LLMClient
from life_simulator.llm.prompts import build_transition_prompt
from life_simulator.models.decision import DecisionOption
from life_simulator.models.person_state import (
    HealthStatus,
    PersonState,
)


class WorldModel:
    """Takes (state, action) -> new_state using data + LLM."""

    def __init__(self, grounding: StatisticalGrounding, llm: LLMClient):
        self.grounding = grounding
        self.llm = llm

    def transition(
        self,
        state: PersonState,
        action: DecisionOption,
        year_delta: int = 1,
    ) -> tuple[PersonState, float]:
        """Produce a new PersonState after taking an action.

        Returns (new_state, confidence).
        """
        stats = self._gather_stats(state, action)
        prompt = build_transition_prompt(state, action, stats, year_delta)
        raw = self.llm.generate_transition(prompt)

        confidence = raw.pop("confidence", 0.5)
        new_state = self._validate(raw, state, stats)
        return new_state, confidence

    def _gather_stats(
        self, state: PersonState, action: DecisionOption
    ) -> dict:
        salary = self.grounding.salary_range(
            state.career.job_title,
            state.location,
            state.career.years_experience,
        )
        return {
            "salary_p25": salary[0],
            "salary_median": salary[1],
            "salary_p75": salary[2],
            "transition_prob": self.grounding.career_transition_probability(
                state.career.job_title, action.id
            ),
            "col_index": self.grounding.cost_of_living_index(state.location),
            "health_probs": self.grounding.health_outcome_probability(
                state.age, state.health.value, state.stress_level
            ),
            "education_premium": self.grounding.education_income_premium(
                state.education.value
            ),
        }

    def _validate(
        self, raw: dict, prev: PersonState, stats: dict
    ) -> PersonState:
        """Validate and clamp LLM output against constraints."""
        # Clamp salary to reasonable range (p10 to p90 approximation)
        if "finances" in raw and "annual_income" in raw["finances"]:
            p25, median, p75 = stats["salary_p25"], stats["salary_median"], stats["salary_p75"]
            iqr = p75 - p25
            low = max(0, p25 - 0.5 * iqr)
            high = p75 + 0.5 * iqr
            raw["finances"]["annual_income"] = max(
                low, min(high, raw["finances"]["annual_income"])
            )

        # Clamp satisfaction and stress
        for field in ("life_satisfaction", "stress_level"):
            if field in raw:
                raw[field] = max(1.0, min(10.0, float(raw[field])))

        # Validate health status
        if "health" in raw:
            valid = {s.value for s in HealthStatus}
            if raw["health"] not in valid:
                raw["health"] = prev.health.value

        # Ensure age incremented
        if "age" in raw:
            raw["age"] = max(raw["age"], prev.age + 1)

        return PersonState.model_validate(raw)
