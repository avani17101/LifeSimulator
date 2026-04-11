"""Prompt templates for LLM-powered state transitions."""

from life_simulator.models.person_state import PersonState
from life_simulator.models.decision import DecisionOption


def build_transition_prompt(
    current_state: PersonState,
    action: DecisionOption,
    statistical_context: dict,
    year_delta: int = 1,
) -> str:
    state_json = current_state.model_dump_json(indent=2)

    return f"""You are a life trajectory simulator. Given a person's current state and a decision, predict their state {year_delta} year(s) later.

CURRENT STATE:
{state_json}

DECISION TAKEN:
{action.label}: {action.description}

STATISTICAL CONTEXT (use as anchors — stay within these ranges):
- Salary range for likely role: ${statistical_context['salary_p25']:,.0f} – ${statistical_context['salary_p75']:,.0f} (median ${statistical_context['salary_median']:,.0f})
- Career transition probability: {statistical_context['transition_prob']:.0%}
- Cost of living index: {statistical_context['col_index']:.2f}x national average
- Health outcome probabilities: {statistical_context['health_probs']}
- Education income premium: {statistical_context['education_premium']:.2f}x

RULES:
1. Salary MUST fall within the p25–p75 range provided. Only exceed if you provide a strong justification.
2. Career transitions should respect the probability. Low-probability transitions need a compelling narrative.
3. Health, stress, and life_satisfaction changes should be incremental (max ±2 per year) unless a major life event occurs.
4. Financial math must be consistent: savings ≈ previous_savings + (annual_income - 12*monthly_expenses) ± life events.
5. Age must increment by {year_delta}.
6. Write a 2-3 sentence "narrative" field describing what happened this year.
7. Include a "confidence" field (0.0–1.0) indicating prediction confidence.

Return ONLY a JSON object with these exact fields:
{{
  "age": <int>,
  "education": "<education_level>",
  "location": "<city>",
  "career": {{
    "job_title": "<title>",
    "industry": "<industry>",
    "years_in_role": <int>,
    "years_experience": <int>,
    "is_employed": <bool>
  }},
  "finances": {{
    "annual_income": <float>,
    "savings": <float>,
    "debt": <float>,
    "monthly_expenses": <float>,
    "investment_portfolio": <float>
  }},
  "health": "<excellent|good|fair|poor>",
  "relationship": "<single|partnered|married|divorced>",
  "dependents": <int>,
  "life_satisfaction": <float 1-10>,
  "stress_level": <float 1-10>,
  "narrative": "<what happened this year>",
  "confidence": <float 0-1>
}}"""


def build_narrative_prompt(
    path: list[dict],
    decision_label: str,
) -> str:
    """Build a prompt to generate a summary narrative for an entire path."""
    years_summary = "\n".join(
        f"- Year {s['year']}: {s['narrative']}" for s in path
    )
    return f"""Summarize this {len(path)}-year life trajectory in 3-4 sentences. The person chose to: {decision_label}.

Year-by-year events:
{years_summary}

Write a compelling, concise summary that captures the arc of this path — the key turning points, trade-offs, and where they ended up. Be specific with numbers (income, net worth) where impactful."""
