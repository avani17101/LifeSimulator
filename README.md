# Life Simulator

A data-grounded life decision simulator. Input your current situation and a decision you're facing — the simulator explores multiple futures using real-world statistical data and AI-powered reasoning.

**How it works:** Your life state flows through a hybrid engine that combines BLS salary data, cost-of-living indices, career transition probabilities, and health statistics with LLM reasoning to generate plausible year-by-year trajectories for each option you're considering.

## Quick Start

```bash
# Install
pip install -e .

# Fastest: use Ollama (free, local, no API key)
ollama pull llama3.1
lifesim example --model ollama/llama3.1

# Or use Groq (fast, free tier)
export GROQ_API_KEY='gsk_...'
lifesim example --model groq/llama-3.1-70b-versatile

# Or use Anthropic
export ANTHROPIC_API_KEY='sk-ant-...'
lifesim example

# Interactive mode
lifesim new --model ollama/llama3.1

# Web UI
pip install -e ".[web]"
streamlit run src/life_simulator/web.py
```

## Supported Models

Works with **10+ providers** — any OpenAI-compatible API works out of the box.

| Provider | Model Example | Cost | Setup |
|----------|--------------|------|-------|
| **Ollama** (local) | `ollama/llama3.1` | Free | `ollama pull llama3.1` |
| **LM Studio** (local) | `lmstudio/local-model` | Free | Download from lmstudio.ai |
| **Groq** | `groq/llama-3.1-70b-versatile` | Free tier | `GROQ_API_KEY` |
| **Anthropic** | `claude-sonnet-4-20250514` | ~$0.02/run | `ANTHROPIC_API_KEY` |
| **OpenAI** | `openai/gpt-4o` | ~$0.03/run | `OPENAI_API_KEY` |
| **Together AI** | `together/meta-llama/Llama-3.1-70B-Instruct-Turbo` | ~$0.01/run | `TOGETHER_API_KEY` |
| **Mistral** | `mistral/mistral-large-latest` | ~$0.02/run | `MISTRAL_API_KEY` |
| **DeepSeek** | `deepseek/deepseek-chat` | ~$0.01/run | `DEEPSEEK_API_KEY` |
| **Fireworks AI** | `fireworks/accounts/fireworks/models/llama-v3p1-70b-instruct` | ~$0.01/run | `FIREWORKS_API_KEY` |
| **OpenRouter** | `openrouter/meta-llama/llama-3.1-70b-instruct` | Varies | `OPENROUTER_API_KEY` |

## CLI Commands

| Command | Description |
|---------|-------------|
| `lifesim new` | Interactive scenario builder |
| `lifesim simulate -c <file>` | Run from a JSON config file |
| `lifesim example` | Run the built-in career crossroads example |
| `lifesim history` | List saved simulation results |

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--model, -m` | claude-sonnet-4 | Model to use (see table above) |
| `--steps, -s` | 5 | Years to simulate |
| `--save / --no-save` | save | Save results to `~/.lifesim/results/` |

## Web UI

The web UI has a step-by-step wizard with provider selection in the sidebar:

```bash
pip install -e ".[web]"
streamlit run src/life_simulator/web.py
```

Select your provider (Ollama is first/default), enter your details, define your decision options, and get results with comparison charts, metric cards, and year-by-year timelines.

## Example Scenarios

The `examples/` directory includes ready-to-run scenarios:

- **career_crossroads.json** — 28yo engineer: MBA vs startup vs staying
- **relocation.json** — 32yo PM: NYC vs Austin vs remote
- **career_pivot.json** — 35yo banker: finance vs teaching vs edtech
- **family_planning.json** — 30yo data scientist: family timing vs career

```bash
lifesim simulate -c examples/relocation.json --model ollama/llama3.1
```

## Architecture

```
src/life_simulator/
├── models/          # Pydantic models with validation (PersonState, Decision, SimTree)
├── data/            # Statistical grounding (BLS salaries, COL, career transitions)
├── llm/             # Multi-provider client with retry logic + prompt engineering
├── engine/          # WorldModel (state transitions) + SimulationEngine (orchestration)
├── viz/             # Rich terminal visualization
├── interactive.py   # CLI scenario builder
├── export.py        # JSON + Markdown report export
├── web.py           # Streamlit web UI
└── cli.py           # Typer CLI entrypoint
```

**Data grounding** keeps predictions realistic: salary ranges from BLS OEWS, cost-of-living from BEA Regional Price Parities, career transitions from O*NET, health outcomes from age/stress models.

**Reliability:** LLM calls have 3x retry with exponential backoff, graceful fallback on parse failures, input validation, prompt injection sanitization, and confidence scoring that penalizes corrected outputs.

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v     # 30 tests
ruff check src/
```
