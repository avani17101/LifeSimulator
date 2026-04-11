from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


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
    job_title: str = Field(min_length=1, max_length=100)
    industry: str = Field(min_length=1, max_length=100)
    years_in_role: int = Field(default=0, ge=0, le=50)
    years_experience: int = Field(default=0, ge=0, le=60)
    is_employed: bool = True


class FinancialState(BaseModel):
    annual_income: float = Field(ge=0, le=10_000_000)
    savings: float = Field(ge=-1_000_000, le=100_000_000)
    debt: float = Field(default=0.0, ge=0, le=10_000_000)
    monthly_expenses: float = Field(ge=0, le=500_000)
    investment_portfolio: float = Field(default=0.0, ge=-1_000_000, le=100_000_000)


class PersonState(BaseModel):
    """Complete snapshot of a person at a point in time."""

    age: int = Field(ge=16, le=120)
    education: EducationLevel
    location: str = Field(min_length=1, max_length=100)
    career: CareerState
    finances: FinancialState
    health: HealthStatus = HealthStatus.GOOD
    relationship: RelationshipStatus = RelationshipStatus.SINGLE
    dependents: int = Field(default=0, ge=0, le=20)
    life_satisfaction: float = Field(default=7.0, ge=1.0, le=10.0)
    stress_level: float = Field(default=5.0, ge=1.0, le=10.0)
    narrative: str = ""

    @field_validator("location")
    @classmethod
    def location_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Location cannot be empty")
        return v.strip()

    @model_validator(mode="after")
    def check_experience_consistency(self) -> PersonState:
        if self.career.years_in_role > self.career.years_experience:
            self.career.years_in_role = self.career.years_experience
        return self

    @property
    def net_worth(self) -> float:
        return (
            self.finances.savings
            + self.finances.investment_portfolio
            - self.finances.debt
        )
