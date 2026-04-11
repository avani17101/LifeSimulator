from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class EducationLevel(str, Enum):
    HIGH_SCHOOL = "high_school"
    ASSOCIATES = "associates"
    BACHELORS = "bachelors"
    MASTERS = "masters"
    MBA = "mba"
    PHD = "phd"
    PROFESSIONAL = "professional"  # JD, MD


class HealthStatus(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class RelationshipStatus(str, Enum):
    SINGLE = "single"
    PARTNERED = "partnered"
    MARRIED = "married"
    DIVORCED = "divorced"


class CareerState(BaseModel):
    job_title: str
    industry: str
    years_in_role: int = 0
    years_experience: int = 0
    is_employed: bool = True


class FinancialState(BaseModel):
    annual_income: float
    savings: float
    debt: float = 0.0
    monthly_expenses: float
    investment_portfolio: float = 0.0


class PersonState(BaseModel):
    """Complete snapshot of a person at a point in time."""

    age: int
    education: EducationLevel
    location: str  # metro area
    career: CareerState
    finances: FinancialState
    health: HealthStatus = HealthStatus.GOOD
    relationship: RelationshipStatus = RelationshipStatus.SINGLE
    dependents: int = 0
    life_satisfaction: float = Field(default=7.0, ge=1.0, le=10.0)
    stress_level: float = Field(default=5.0, ge=1.0, le=10.0)
    narrative: str = ""

    @property
    def net_worth(self) -> float:
        return (
            self.finances.savings
            + self.finances.investment_portfolio
            - self.finances.debt
        )
