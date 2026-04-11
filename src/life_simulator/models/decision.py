from pydantic import BaseModel


class DecisionOption(BaseModel):
    """A single choice a person can make."""

    id: str
    label: str
    description: str
    estimated_duration_years: float = 1.0
    tags: list[str] = []


class Decision(BaseModel):
    """A decision point with available options."""

    question: str
    options: list[DecisionOption]
    context: str = ""
