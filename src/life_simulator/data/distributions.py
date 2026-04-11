"""Mock statistical grounding with realistic BLS/Census-derived ranges."""

from life_simulator.data.grounding import StatisticalGrounding


def _normalize(title: str) -> str:
    return title.lower().replace(" ", "_").replace("-", "_")


def _experience_bucket(years: int) -> str:
    if years < 3:
        return "junior"
    if years < 8:
        return "mid"
    return "senior"


class MockGrounding(StatisticalGrounding):
    """Hardcoded but realistic distributions for MVP.

    Sources: BLS OEWS 2024, BEA Regional Price Parities 2023,
    O*NET, Census ACS. Values are approximations for demo purposes.
    """

    # (normalized_title, experience_bucket) -> (p25, median, p75)
    SALARY_DATA: dict[tuple[str, str], tuple[float, float, float]] = {
        # Tech
        ("software_engineer", "junior"): (78_000, 95_000, 118_000),
        ("software_engineer", "mid"): (105_000, 132_000, 168_000),
        ("software_engineer", "senior"): (145_000, 178_000, 225_000),
        ("engineering_manager", "mid"): (150_000, 185_000, 230_000),
        ("engineering_manager", "senior"): (180_000, 220_000, 280_000),
        ("data_scientist", "junior"): (70_000, 85_000, 105_000),
        ("data_scientist", "mid"): (95_000, 118_000, 150_000),
        ("data_scientist", "senior"): (130_000, 160_000, 200_000),
        ("product_manager", "junior"): (75_000, 90_000, 110_000),
        ("product_manager", "mid"): (100_000, 125_000, 158_000),
        ("product_manager", "senior"): (140_000, 170_000, 215_000),
        # Business
        ("consultant", "junior"): (65_000, 80_000, 100_000),
        ("consultant", "mid"): (90_000, 115_000, 148_000),
        ("consultant", "senior"): (130_000, 165_000, 210_000),
        ("investment_banker", "junior"): (85_000, 110_000, 150_000),
        ("investment_banker", "mid"): (150_000, 200_000, 300_000),
        ("mba_student", "any"): (0, 0, 0),  # no income during MBA
        ("startup_founder", "any"): (0, 50_000, 140_000),
        # Healthcare
        ("nurse", "mid"): (60_000, 77_000, 95_000),
        ("physician", "mid"): (200_000, 260_000, 340_000),
        # Education
        ("teacher", "mid"): (42_000, 55_000, 70_000),
        ("professor", "senior"): (75_000, 100_000, 140_000),
        # Creative
        ("designer", "mid"): (60_000, 78_000, 100_000),
        ("marketing_manager", "mid"): (70_000, 90_000, 120_000),
    }

    # Default salary for unknown roles
    DEFAULT_SALARY: dict[str, tuple[float, float, float]] = {
        "junior": (40_000, 52_000, 68_000),
        "mid": (55_000, 72_000, 95_000),
        "senior": (75_000, 98_000, 130_000),
    }

    # Metro area -> COL index (national avg = 1.0)
    COL_INDEX: dict[str, float] = {
        "San Francisco": 1.82,
        "New York": 1.69,
        "San Jose": 1.65,
        "Los Angeles": 1.46,
        "Seattle": 1.49,
        "Boston": 1.42,
        "Washington DC": 1.38,
        "San Diego": 1.35,
        "Denver": 1.13,
        "Portland": 1.15,
        "Austin": 1.14,
        "Chicago": 1.07,
        "Minneapolis": 1.04,
        "Atlanta": 1.02,
        "Dallas": 1.01,
        "Houston": 0.98,
        "Phoenix": 0.97,
        "Philadelphia": 1.08,
        "Miami": 1.22,
        "Nashville": 1.00,
        "Raleigh": 0.96,
        "Remote": 1.00,
    }

    # (from_role, to_role) -> annual transition probability
    CAREER_TRANSITIONS: dict[tuple[str, str], float] = {
        # Software engineer paths
        ("software_engineer", "engineering_manager"): 0.08,
        ("software_engineer", "product_manager"): 0.04,
        ("software_engineer", "startup_founder"): 0.03,
        ("software_engineer", "data_scientist"): 0.05,
        ("software_engineer", "consultant"): 0.03,
        # PM paths
        ("product_manager", "engineering_manager"): 0.03,
        ("product_manager", "startup_founder"): 0.05,
        ("product_manager", "consultant"): 0.04,
        # Consultant paths
        ("consultant", "product_manager"): 0.10,
        ("consultant", "startup_founder"): 0.06,
        ("consultant", "investment_banker"): 0.04,
        # MBA exits
        ("mba_student", "product_manager"): 0.25,
        ("mba_student", "consultant"): 0.30,
        ("mba_student", "investment_banker"): 0.15,
        ("mba_student", "startup_founder"): 0.10,
        ("mba_student", "software_engineer"): 0.05,
        # Startup outcomes
        ("startup_founder", "software_engineer"): 0.15,
        ("startup_founder", "product_manager"): 0.10,
        ("startup_founder", "consultant"): 0.05,
    }

    EDUCATION_PREMIUMS: dict[str, float] = {
        "high_school": 0.70,
        "associates": 0.82,
        "bachelors": 1.00,
        "masters": 1.18,
        "mba": 1.35,
        "phd": 1.25,
        "professional": 1.55,
    }

    def salary_range(
        self, job_title: str, location: str, experience_years: int
    ) -> tuple[float, float, float]:
        bucket = _experience_bucket(experience_years)
        key = (_normalize(job_title), bucket)
        # Try exact match, then "any" experience bucket, then default
        base = self.SALARY_DATA.get(key)
        if base is None:
            base = self.SALARY_DATA.get((_normalize(job_title), "any"))
        if base is None:
            base = self.DEFAULT_SALARY.get(bucket, (50_000, 70_000, 95_000))
        col = self._col(location)
        return (base[0] * col, base[1] * col, base[2] * col)

    def career_transition_probability(
        self, from_role: str, to_role: str
    ) -> float:
        key = (_normalize(from_role), _normalize(to_role))
        return self.CAREER_TRANSITIONS.get(key, 0.02)

    def cost_of_living_index(self, location: str) -> float:
        return self._col(location)

    def health_outcome_probability(
        self, age: int, current_health: str, stress_level: float
    ) -> dict[str, float]:
        # Simple model: higher age + stress -> worse health
        stress_factor = max(0, (stress_level - 5) * 0.03)
        age_factor = max(0, (age - 30) * 0.005)
        decline_prob = min(0.4, stress_factor + age_factor)

        health_order = ["excellent", "good", "fair", "poor"]
        idx = health_order.index(current_health)

        probs = {"excellent": 0.0, "good": 0.0, "fair": 0.0, "poor": 0.0}
        probs[current_health] = 1.0 - decline_prob - 0.05
        if idx < 3:
            probs[health_order[idx + 1]] = decline_prob
        else:
            probs["poor"] += decline_prob
        # Small chance of improvement
        if idx > 0:
            probs[health_order[idx - 1]] = 0.05
        else:
            probs["excellent"] += 0.05

        return probs

    def education_income_premium(
        self, education: str, field: str = ""
    ) -> float:
        return self.EDUCATION_PREMIUMS.get(education, 1.0)

    def _col(self, location: str) -> float:
        # Try exact match, then fuzzy match
        if location in self.COL_INDEX:
            return self.COL_INDEX[location]
        loc_lower = location.lower()
        for city, idx in self.COL_INDEX.items():
            if city.lower() in loc_lower or loc_lower in city.lower():
                return idx
        return 1.0
