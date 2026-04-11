"""Hybrid transition engine: statistical grounding + LLM reasoning."""

import logging

from life_simulator.data.grounding import StatisticalGrounding
from life_simulator.llm.client import LLMClient, LLMParseError
from life_simulator.llm.prompts import build_transition_prompt
from life_simulator.models.decision import DecisionOption
from life_simulator.models.person_state import (
    HealthStatus,
    PersonState,
    RelationshipStatus,
)

logger = logging.getLogger(__name__)


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
        Falls back to previous state with low confidence on LLM failure.
        """
        stats = self._gather_stats(state, action)
        prompt = build_transition_prompt(state, action, stats, year_delta)

        try:
            raw = self.llm.generate_transition(prompt)
        except LLMParseError:
            logger.warning("LLM returned unparseable JSON. Falling back to previous state.")
            return self._fallback_state(state, year_delta), 0.1

        confidence = raw.pop("confidence", 0.5)
        new_state, confidence = self._validate(raw, state, stats, confidence)
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
        self, raw: dict, prev: PersonState, stats: dict, confidence: float
    ) -> tuple[PersonState, float]:
        """Validate and clamp LLM output. Reduces confidence on corrections."""
        corrections = 0

        # Clamp salary to reasonable range (p10 to p90 approximation)
        if "finances" in raw and "annual_income" in raw["finances"]:
            p25, p75 = stats["salary_p25"], stats["salary_p75"]
            iqr = p75 - p25
            low = max(0, p25 - 0.5 * iqr)
            high = p75 + 0.5 * iqr
            original = raw["finances"]["annual_income"]
            clamped = max(low, min(high, original))
            if abs(clamped - original) > 1000:
                logger.info("Clamped salary: $%,.0f → $%,.0f", original, clamped)
                corrections += 1
            raw["finances"]["annual_income"] = clamped

            # Check salary jump isn't extreme (>50% in one year)
            prev_income = prev.finances.annual_income
            if prev_income > 0:
                ratio = clamped / prev_income
                if ratio > 1.5 or ratio < 0.5:
                    logger.info("Large salary change: %.0f%% year-over-year", (ratio - 1) * 100)
                    corrections += 1

        # Ensure non-negative finances where appropriate
        if "finances" in raw:
            for field in ("annual_income", "debt", "monthly_expenses"):
                if field in raw["finances"]:
                    raw["finances"][field] = max(0, raw["finances"][field])

        # Clamp satisfaction and stress
        for field in ("life_satisfaction", "stress_level"):
            if field in raw:
                val = float(raw[field])
                clamped = max(1.0, min(10.0, val))
                if abs(clamped - val) > 0.01:
                    corrections += 1
                raw[field] = clamped

        # Validate health status
        if "health" in raw:
            valid = {s.value for s in HealthStatus}
            if raw["health"] not in valid:
                logger.info("Invalid health '%s', keeping previous", raw["health"])
                raw["health"] = prev.health.value
                corrections += 1

        # Validate relationship status
        if "relationship" in raw:
            valid = {s.value for s in RelationshipStatus}
            if raw["relationship"] not in valid:
                raw["relationship"] = prev.relationship.value
                corrections += 1

        # Ensure age incremented correctly
        if "age" in raw:
            expected = prev.age + 1
            if raw["age"] != expected:
                logger.info("Age corrected: %d → %d", raw["age"], expected)
                raw["age"] = expected
                corrections += 1

        # Validate narrative exists and is meaningful
        if not raw.get("narrative") or len(str(raw.get("narrative", ""))) < 10:
            raw["narrative"] = f"Continued on current path in {prev.location}."
            corrections += 1

        # Ensure dependents non-negative
        if "dependents" in raw:
            raw["dependents"] = max(0, int(raw["dependents"]))

        # Reduce confidence proportional to corrections
        if corrections > 0:
            penalty = min(0.3, corrections * 0.05)
            confidence = max(0.1, confidence - penalty)
            logger.info("Applied %d corrections, confidence: %.2f", corrections, confidence)

        try:
            new_state = PersonState.model_validate(raw)
        except Exception as e:
            logger.warning("Validation failed: %s. Falling back.", e)
            return self._fallback_state(prev, 1), 0.1

        return new_state, confidence

    def _fallback_state(self, prev: PersonState, year_delta: int) -> PersonState:
        """Create a minimal progression from previous state when LLM fails."""
        return prev.model_copy(update={
            "age": prev.age + year_delta,
            "career": prev.career.model_copy(update={
                "years_in_role": prev.career.years_in_role + year_delta,
                "years_experience": prev.career.years_experience + year_delta,
            }),
            "narrative": "Continued on the current path with no major changes.",
        })
