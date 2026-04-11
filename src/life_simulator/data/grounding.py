from abc import ABC, abstractmethod


class StatisticalGrounding(ABC):
    """Interface for providing real-world statistical anchors."""

    @abstractmethod
    def salary_range(
        self, job_title: str, location: str, experience_years: int
    ) -> tuple[float, float, float]:
        """Return (p25, median, p75) salary for role/location/experience."""
        ...

    @abstractmethod
    def career_transition_probability(
        self, from_role: str, to_role: str
    ) -> float:
        """Probability of transitioning between roles (0-1)."""
        ...

    @abstractmethod
    def cost_of_living_index(self, location: str) -> float:
        """COL index relative to national average (1.0 = average)."""
        ...

    @abstractmethod
    def health_outcome_probability(
        self, age: int, current_health: str, stress_level: float
    ) -> dict[str, float]:
        """Probability distribution over health statuses at next time step."""
        ...

    @abstractmethod
    def education_income_premium(
        self, education: str, field: str
    ) -> float:
        """Multiplier on income for given education level."""
        ...
