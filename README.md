# Life Simulator

A data-grounded life decision simulator. Input your current situation and a decision you're facing — the simulator explores multiple futures using real-world statistical data and AI-powered reasoning.

**How it works:** Your life state flows through a hybrid engine that combines BLS salary data, cost-of-living indices, career transition probabilities, and health statistics with Claude's reasoning to generate plausible year-by-year trajectories for each option you're considering.

## Quick Start

```bash
# Install
pip install -e .

# Set your API key
export ANTHROPIC_API_KEY='sk-ant-...'

# Interactive mode — build a scenario step by step
lifesim new

# Run a built-in example
lifesim example

# Run from a config file
lifesim simulate --config examples/career_crossroads.json

# View past simulations
lifesim history
```

## Web UI

For a visual interface with charts and downloadable reports:

```bash
pip install -e ".[web]"
streamlit run src/life_simulator/web.py
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `lifesim new` | Interactive scenario builder — walks you through setting up your situation and decision |
| `lifesim simulate -c <file>` | Run simulation from a JSON config file |
| `lifesim example` | Run the built-in career crossroads example |
| `lifesim history` | List saved simulation results |

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--steps, -s` | 5 | Years to simulate into the future |
| `--model, -m` | claude-sonnet-4 | Claude model to use |
| `--save / --no-save` | save | Save results to `~/.lifesim/results/` |

## Example Scenarios

The `examples/` directory includes ready-to-run scenarios:

- **career_crossroads.json** — 28yo engineer choosing between MBA, startup, or staying
- **relocation.json** — 32yo PM deciding whether to leave NYC, move to Austin, or go remote
- **career_pivot.json** — 35yo banker considering teaching, edtech, or pushing to MD
- **family_planning.json** — 30yo data scientist weighing family timing vs. career growth

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
    "narrative": "Your current situation in 1-2 sentences."
  },
  "decision": {
    "question": "The decision you're facing?",
    "options": [
      {
        "id": "option_a",
        "label": "Short label",
        "description": "Detailed description of this path.",
        "estimated_duration_years": 2
      }
    ],
    "context": "Additional context about your situation."
  }
}
```

## Architecture

```
src/life_simulator/
├── models/          # Pydantic data models (PersonState, Decision, SimTree)
├── data/            # Statistical grounding (BLS salaries, COL, transitions)
├── llm/             # Claude API client + prompt engineering
├── engine/          # Simulation orchestration (WorldModel, SimulationEngine)
├── viz/             # Rich terminal visualization
├── interactive.py   # Interactive scenario builder
├── export.py        # JSON + Markdown report export
├── web.py           # Streamlit web UI
└── cli.py           # Typer CLI entrypoint
```

**Data grounding** keeps predictions realistic: salary ranges are anchored to BLS OEWS data, cost-of-living uses BEA Regional Price Parities, career transitions use O*NET-derived probabilities, and health outcomes factor in age and stress.

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
ruff check src/
```
# LifeSimulator
