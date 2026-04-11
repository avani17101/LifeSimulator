# Life Simulator

**Explore branching futures for life's biggest decisions — grounded in real data, not guesswork.**

You're 28, a software engineer in SF. MBA? Startup? Stay put? Life Simulator doesn't give you one answer — it explores every branch, year by year, grounded in BLS salary data, cost-of-living indices, and career transition probabilities. Think of it as `git branch` for your life.

## What It Actually Does

You input your current life state (age, career, finances, health, location) and a decision with 2-5 options. The engine:

1. **Branches** — creates a separate simulation path for each option
2. **Steps forward** — simulates each path year by year (default: 5 years)
3. **Grounds in data** — anchors every prediction to real statistical ranges (salary, COL, career transition probability, health outcomes)
4. **Narrates** — generates a detailed narrative for each year explaining what happened and why
5. **Scores confidence** — every prediction gets a confidence score that drops when the model is corrected

The result is a **branching tree of possible futures** — not a single prediction, but a map of where each choice could lead.

## Use Cases

### "Should I get an MBA or join a startup?"

```
$ lifesim example --model ollama/llama3.1 --steps 5

Career Crossroads Example
28-year-old software engineer in San Francisco deciding between:
  1. Pursue an MBA at a top program
  2. Join an early-stage startup as co-founder
  3. Stay and grow at current company

Simulating 3 paths x 5 years...

┌─────────────── Outcome Comparison (Final Year) ────────────────┐
│ Metric          │ Pursue MBA    │ Co-found      │ Stay and grow │
├─────────────────┼───────────────┼───────────────┼───────────────┤
│ Job Title       │ Product Mgr   │ CEO           │ Eng Manager   │
│ Income          │ $185,000      │ $95,000       │ $210,000      │
│ Net Worth       │ $42,000       │ $180,000      │ $285,000      │
│ Satisfaction    │ 7.5/10        │ 8.2/10        │ 6.8/10        │
│ Stress          │ 6.0/10        │ 8.5/10        │ 5.0/10        │
│ Confidence      │ 72%           │ 45%           │ 85%           │
└─────────────────┴───────────────┴───────────────┴───────────────┘
```

The MBA path shows higher income but negative net worth from tuition debt. The startup path has highest satisfaction but lowest confidence (because startup outcomes are inherently unpredictable). Staying has the highest net worth and confidence — the safe bet, data-grounded.

### "Should we relocate from NYC?"

A 32-year-old product manager and their remote-working partner weighing:
- **Stay in NYC** — high income, high cost, strong network
- **Move to Austin** — 10% pay cut, buy a house, no state income tax
- **Go fully remote** — maximum flexibility, move to a mid-size city

```
$ lifesim simulate -c examples/relocation.json --model groq/llama-3.1-70b-versatile

Year-by-year for "Move to Austin":
  2027 | Product Manager | $168,000 | Relocated, bought a 3BR house. Partner's
       | freelance income covers most of the mortgage. Stress dropped significantly.
  2028 | Senior PM       | $178,000 | Promoted. Net worth jumped $120K from
       | home equity + lower expenses. Started thinking about kids.
  2029 | Senior PM       | $185,000 | First child born. Partner shifted to
       | part-time. Monthly expenses up but still lower than NYC rent was.
  ...
```

### "Should I leave finance for teaching?"

A burned-out 35-year-old investment banker ($280K, $770K net worth, 9.0 stress) considering:
- Push to Managing Director ($500K+ potential)
- Become a high school teacher (~$60K)
- Start an EdTech company

```
$ lifesim simulate -c examples/career_pivot.json --steps 7
```

The simulation shows teaching drops income 78% but stress goes from 9.0 to 3.5 and satisfaction from 4.5 to 8.0. The EdTech path is high-variance: confidence drops to 35% by year 3 because founder outcomes are statistically unpredictable. The "stay in finance" path shows health declining from "fair" to "poor" by year 4 — the model factors in age + sustained high stress.

### "When should we start a family?"

```
$ lifesim simulate -c examples/family_planning.json --model ollama/qwen2.5
```

Compares "family now" vs "career first (kids at 33)" vs "part-time + family." The model tracks cascading effects: childcare costs hit monthly expenses, parental leave affects promotion timeline, partner's income changes, satisfaction dynamics shift with dependents.

## Why This Is Different

**No one else combines all four of these:**

| Feature | Life Simulator | Financial Planners | Career Quizzes | AI Chatbots |
|---------|:-:|:-:|:-:|:-:|
| Multi-path branching | Yes | No (single projection) | No | No |
| Data-grounded predictions | BLS/Census/O*NET | Historical returns only | None | Vibes |
| Year-by-year narratives | Yes | No | No | Yes but no data |
| Confidence scoring | Yes (penalized on corrections) | No | No | No |
| Interdependent dimensions | Career + Finance + Health + Relationships | Finance only | Career only | Unstructured |
| Runs locally (free) | Ollama/LM Studio | No | No | No |

**The moat is the hybrid engine.** Pure LLMs hallucinate salaries. Pure statistical models can't narrate or reason about life events. This system forces LLM predictions through a statistical validation layer:

- Salary must fall within BLS p25-p75 for the role/location/experience
- Career transitions must respect O*NET-derived probabilities
- Health outcomes are weighted by age and stress level
- Cost of living adjusts automatically across 23 metro areas
- Financial math is checked for consistency (savings = prev + income - expenses)
- Corrections reduce confidence — if the model needed heavy fixing, you see it

**What this means:** When the model says "you'll make $185K as a Product Manager in Austin after your MBA," that number is anchored to real BLS data for PMs in Austin with that experience level. It's not a guess. And if the model tried to say $400K, the system would clamp it and flag it with reduced confidence.

## Quick Start

```bash
# Install
pip install -e .

# Fastest: Ollama (free, local, no API key)
ollama pull llama3.1
lifesim example --model ollama/llama3.1

# Or Groq (fast, generous free tier)
export GROQ_API_KEY='gsk_...'
lifesim example --model groq/llama-3.1-70b-versatile

# Or Anthropic (highest quality)
export ANTHROPIC_API_KEY='sk-ant-...'
lifesim example

# Interactive mode — build your own scenario
lifesim new --model ollama/llama3.1

# Web UI with charts and visualizations
pip install -e ".[web]"
streamlit run src/life_simulator/web.py
```

## Supported Models

Any OpenAI-compatible API works. **10 providers built in:**

| Provider | Model | Cost | Setup |
|----------|-------|------|-------|
| **Ollama** (local) | `ollama/llama3.1` | Free | `ollama pull llama3.1` |
| **LM Studio** (local) | `lmstudio/local-model` | Free | lmstudio.ai |
| **Groq** | `groq/llama-3.1-70b-versatile` | Free tier | `GROQ_API_KEY` |
| **DeepSeek** | `deepseek/deepseek-chat` | ~$0.01/run | `DEEPSEEK_API_KEY` |
| **Together AI** | `together/meta-llama/Llama-3.1-70B-Instruct-Turbo` | ~$0.01/run | `TOGETHER_API_KEY` |
| **Fireworks** | `fireworks/accounts/fireworks/models/llama-v3p1-70b-instruct` | ~$0.01/run | `FIREWORKS_API_KEY` |
| **Anthropic** | `claude-sonnet-4-20250514` | ~$0.02/run | `ANTHROPIC_API_KEY` |
| **Mistral** | `mistral/mistral-large-latest` | ~$0.02/run | `MISTRAL_API_KEY` |
| **OpenAI** | `openai/gpt-4o` | ~$0.03/run | `OPENAI_API_KEY` |
| **OpenRouter** | `openrouter/meta-llama/llama-3.1-70b-instruct` | Varies | `OPENROUTER_API_KEY` |

## CLI

```bash
lifesim new                              # interactive scenario builder
lifesim example                          # built-in career crossroads
lifesim simulate -c scenario.json        # from config file
lifesim history                          # browse saved results

# Options
--model, -m    ollama/llama3.1           # any provider/model
--steps, -s    5                         # years to simulate
--save/--no-save                         # auto-save to ~/.lifesim/results/
```

## Web UI

Step-by-step wizard: enter your life → define your decision → see branching results with charts.

```bash
pip install -e ".[web]"
streamlit run src/life_simulator/web.py
```

Provider picker in the sidebar — Ollama (free, local) is the default.

## Config File Format

```json
{
  "person": {
    "age": 28,
    "education": "bachelors",
    "location": "San Francisco",
    "career": {
      "job_title": "Software Engineer",
      "industry": "Technology",
      "years_in_role": 3,
      "years_experience": 5
    },
    "finances": {
      "annual_income": 155000,
      "savings": 80000,
      "debt": 25000,
      "monthly_expenses": 5500,
      "investment_portfolio": 40000
    },
    "health": "good",
    "relationship": "partnered",
    "dependents": 0,
    "life_satisfaction": 6.5,
    "stress_level": 6.0,
    "narrative": "Working at a mid-size tech company, feeling ready for a change."
  },
  "decision": {
    "question": "What should I do with my career?",
    "options": [
      {
        "id": "mba",
        "label": "Pursue MBA",
        "description": "Leave job for a top-20 MBA program. 2 years, ~$150K cost.",
        "estimated_duration_years": 2
      },
      {
        "id": "startup",
        "label": "Co-found a startup",
        "description": "B2B SaaS with a college friend. Angel funding. High risk.",
        "estimated_duration_years": 3
      }
    ],
    "context": "Partner is supportive but risk-averse."
  }
}
```

## Architecture

```
src/life_simulator/
├── models/          # Pydantic models with validation
├── data/            # Statistical grounding (BLS, Census, O*NET)
├── llm/             # Multi-provider client (10+) with 3x retry
├── engine/          # WorldModel + SimulationEngine
├── viz/             # Rich terminal rendering
├── interactive.py   # CLI scenario builder
├── export.py        # JSON + Markdown reports
├── web.py           # Streamlit web UI
└── cli.py           # Typer CLI
```

**Engine pipeline:** `PersonState + Decision` → statistical context gathered → prompt built with data anchors → LLM generates next year → output validated/clamped → confidence adjusted → repeat for N years × M options → branching tree returned.

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v     # 30 tests
ruff check src/
```
