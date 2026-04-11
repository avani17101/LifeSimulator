"""Streamlit web UI for Life Simulator."""

import json
import os
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Life Simulator",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Global */
    .block-container { padding-top: 2rem; max-width: 1200px; }

    /* Hero */
    .hero {
        text-align: center;
        padding: 3rem 1rem 2rem;
    }
    .hero h1 {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .hero p {
        font-size: 1.15rem;
        color: #6b7280;
        max-width: 600px;
        margin: 0 auto;
    }

    /* Step indicator */
    .step-bar {
        display: flex;
        justify-content: center;
        gap: 0;
        margin: 2rem auto 2.5rem;
        max-width: 500px;
    }
    .step-item {
        flex: 1;
        text-align: center;
        position: relative;
        font-size: 0.85rem;
        font-weight: 600;
        color: #9ca3af;
        padding-bottom: 12px;
    }
    .step-item.active {
        color: #667eea;
    }
    .step-item.done {
        color: #10b981;
    }
    .step-item::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 10%;
        width: 80%;
        height: 4px;
        border-radius: 2px;
        background: #e5e7eb;
    }
    .step-item.active::after { background: #667eea; }
    .step-item.done::after { background: #10b981; }

    /* Section cards */
    .section-label {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #667eea;
        margin-bottom: 0.25rem;
    }

    /* Metric cards */
    .metric-row {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
    }
    .metric-card {
        flex: 1;
        min-width: 140px;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        text-align: center;
    }
    .metric-card .label {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94a3b8;
        margin-bottom: 4px;
    }
    .metric-card .value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1e293b;
    }
    .metric-card.winner { border-color: #667eea; background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%); }
    .metric-card.winner .value { color: #667eea; }

    /* Timeline */
    .timeline-node {
        position: relative;
        padding-left: 2.5rem;
        padding-bottom: 1.5rem;
        border-left: 3px solid #e2e8f0;
        margin-left: 0.75rem;
    }
    .timeline-node:last-child { border-left-color: transparent; }
    .timeline-node::before {
        content: '';
        position: absolute;
        left: -8px;
        top: 4px;
        width: 13px;
        height: 13px;
        border-radius: 50%;
        background: #667eea;
        border: 3px solid #eef2ff;
    }
    .timeline-node.low-conf::before { background: #f59e0b; }
    .timeline-node.very-low-conf::before { background: #ef4444; }
    .timeline-year {
        font-size: 0.8rem;
        font-weight: 700;
        color: #667eea;
        margin-bottom: 2px;
    }
    .timeline-title {
        font-size: 1rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 4px;
    }
    .timeline-stats {
        font-size: 0.8rem;
        color: #64748b;
        margin-bottom: 4px;
    }
    .timeline-narrative {
        font-size: 0.9rem;
        color: #475569;
        line-height: 1.5;
        background: #f8fafc;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        border-left: 3px solid #e2e8f0;
    }

    /* Path header cards */
    .path-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.5rem;
    }
    .path-header h3 {
        margin: 0 0 0.25rem;
        font-size: 1.3rem;
        color: white;
    }
    .path-header p {
        margin: 0;
        opacity: 0.85;
        font-size: 0.9rem;
    }

    /* Confidence badge */
    .conf-badge {
        display: inline-block;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 10px;
        margin-left: 6px;
    }
    .conf-high { background: #dcfce7; color: #166534; }
    .conf-mid { background: #fef3c7; color: #92400e; }
    .conf-low { background: #fee2e2; color: #991b1b; }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Button overrides */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        font-weight: 600;
        padding: 0.6rem 2rem;
        font-size: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# =====================================================================
# Helper functions (defined first so they're available in the flow)
# =====================================================================

def _go(step: int):
    st.session_state.step = step


def _render_steps(current: int):
    labels = ["Welcome", "About You", "Decision", "Results"]
    items = ""
    for i, label in enumerate(labels):
        cls = "done" if i < current else "active" if i == current else ""
        items += f'<div class="step-item {cls}">{label}</div>'
    st.markdown(f'<div class="step-bar">{items}</div>', unsafe_allow_html=True)


def _load_example(name: str | None) -> dict:
    """Load example scenario data."""
    if not name:
        return {}
    examples_dir = Path(__file__).parent.parent.parent / "examples"
    path = examples_dir / f"{name}.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    p = data["person"]
    d = data["decision"]
    return {
        "age": p["age"],
        "location": p["location"],
        "education": p["education"],
        "job_title": p["career"]["job_title"],
        "industry": p["career"]["industry"],
        "years_in_role": p["career"].get("years_in_role", 2),
        "years_exp": p["career"].get("years_experience", 5),
        "income": int(p["finances"]["annual_income"]),
        "savings": int(p["finances"]["savings"]),
        "debt": int(p["finances"]["debt"]),
        "expenses": int(p["finances"]["monthly_expenses"]),
        "investments": int(p["finances"].get("investment_portfolio", 0)),
        "health": p.get("health", "good"),
        "relationship": p.get("relationship", "single"),
        "dependents": p.get("dependents", 0),
        "satisfaction": p.get("life_satisfaction", 7.0),
        "stress": p.get("stress_level", 5.0),
        "narrative": p.get("narrative", ""),
        "decision": {
            "question": d["question"],
            "context": d.get("context", ""),
            "options": [
                {
                    "label": o["label"],
                    "description": o["description"],
                    "duration": float(o.get("estimated_duration_years", 1.0)),
                }
                for o in d["options"]
            ],
        },
    }


def _run_simulation(person: dict, decision: dict, model_name: str, num_steps: int, api_key: str | None = None):
    """Build models and run the simulation with progress."""
    from life_simulator.data.distributions import MockGrounding
    from life_simulator.engine.simulation import _INERTIA
    from life_simulator.engine.world_model import WorldModel
    from life_simulator.llm.client import LLMClient, LLMAuthError, LLMModelError, LLMConnectionError
    from life_simulator.models.decision import Decision, DecisionOption
    from life_simulator.models.person_state import (
        CareerState,
        EducationLevel,
        FinancialState,
        PersonState,
    )
    from life_simulator.models.simulation_tree import SimNode, SimTree

    state = PersonState(
        age=person["age"],
        education=EducationLevel(person["education"]),
        location=person["location"],
        career=CareerState(
            job_title=person["job_title"],
            industry=person["industry"],
            years_in_role=person["years_in_role"],
            years_experience=person["years_experience"],
        ),
        finances=FinancialState(
            annual_income=person["income"],
            savings=person["savings"],
            debt=person["debt"],
            monthly_expenses=person["expenses"],
            investment_portfolio=person["investments"],
        ),
        health=person["health"],
        relationship=person["relationship"],
        dependents=person["dependents"],
        life_satisfaction=person["satisfaction"],
        stress_level=person["stress"],
        narrative=person["narrative"],
    )

    options = [
        DecisionOption(
            id=o["label"].lower().replace(" ", "_")[:20],
            label=o["label"],
            description=o["description"],
            estimated_duration_years=o["duration"],
        )
        for o in decision["options"]
    ]
    dec = Decision(question=decision["question"], options=options, context=decision["context"])

    progress_bar = st.progress(0, text="Initializing...")
    status_text = st.empty()
    total_calls = len(options) * num_steps
    call_count = 0

    try:
        grounding = MockGrounding()
        llm = LLMClient(model=model_name, api_key=api_key if api_key != "no-key-needed" else None)
        world_model = WorldModel(grounding=grounding, llm=llm)

        root = SimNode(year=2026, state=state)

        for option in options:
            current = state
            nodes = []

            for step_idx in range(num_steps):
                year = 2026 + step_idx + 1
                action = option if step_idx == 0 else _INERTIA
                call_count += 1
                progress_bar.progress(
                    call_count / total_calls,
                    text=f"Simulating **{option.label}** — Year {year}",
                )
                status_text.caption(f"Calling {llm.display_name} to predict outcomes...")

                new_state, confidence = world_model.transition(current, action, year_delta=1)
                node = SimNode(
                    year=year,
                    state=new_state,
                    action_taken=option.id if step_idx == 0 else "continue",
                    confidence=confidence,
                )
                nodes.append(node)
                current = new_state

            for i in range(len(nodes) - 1):
                nodes[i].children = [nodes[i + 1]]
            root.children.append(nodes[0])

        result = SimTree(root=root, decision=dec)
        progress_bar.progress(1.0, text="Done!")
        status_text.empty()

        st.session_state.sim_result = result
        st.session_state.sim_llm = llm

    except LLMAuthError as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Authentication failed: {e}")
        st.info("Check your API key in the sidebar.")
    except LLMModelError as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Model not found: {e}")
        st.info("Check the model name. For Ollama, make sure you've run `ollama pull <model>`.")
    except LLMConnectionError as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Connection failed: {e}")
        st.info("For Ollama/LM Studio, make sure the server is running. For cloud providers, check your network.")
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Simulation failed: {e}")
        st.info("Check your settings and try again.")


def _path_label(sim_tree, path):
    if len(path) < 2:
        return "?"
    option_id = path[1].action_taken
    for opt in sim_tree.decision.options:
        if opt.id == option_id:
            return opt.label
    return option_id or "?"


def _plot_metric(sim_tree, paths, labels, extractor):
    """Plot a metric over time using Streamlit line chart."""
    import pandas as pd

    data = {}
    for path, label in zip(paths, labels):
        years = [sim_tree.root.year] + [n.year for n in path[1:]]
        values = [extractor(sim_tree.root.state)] + [extractor(n.state) for n in path[1:]]
        data[label] = pd.Series(values, index=years)

    df = pd.DataFrame(data)
    st.line_chart(df)


def _display_results(sim_tree, llm):
    """Render beautiful simulation results."""
    paths = sim_tree.all_paths()
    if not paths:
        st.warning("No results to display.")
        return

    labels = [_path_label(sim_tree, p) for p in paths]
    root_state = sim_tree.root.state

    # --- Hero summary ---
    st.markdown(
        '<div class="hero" style="padding:1.5rem 0 0.5rem;">'
        '<h1 style="font-size:2rem;">Your Simulated Futures</h1>'
        f'<p>{sim_tree.decision.question}</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    if llm:
        st.caption(
            f"Model: **{llm.model}** | "
            f"Cost: ${llm.estimated_cost:.3f} "
            f"({llm.total_input_tokens:,} in / {llm.total_output_tokens:,} out tokens)"
        )

    # --- Winner highlight ---
    final_states = [(labels[i], paths[i][-1].state, paths[i][-1].confidence) for i in range(len(paths))]

    best_income = max(final_states, key=lambda x: x[1].finances.annual_income)
    best_wealth = max(final_states, key=lambda x: x[1].net_worth)
    best_happy = max(final_states, key=lambda x: x[1].life_satisfaction)
    lowest_stress = min(final_states, key=lambda x: x[1].stress_level)

    cards_html = '<div class="metric-row">'
    for title, winner_label, value in [
        ("Highest Income", best_income[0], f"${best_income[1].finances.annual_income:,.0f}"),
        ("Highest Net Worth", best_wealth[0], f"${best_wealth[1].net_worth:,.0f}"),
        ("Happiest", best_happy[0], f"{best_happy[1].life_satisfaction:.1f}/10"),
        ("Least Stressed", lowest_stress[0], f"{lowest_stress[1].stress_level:.1f}/10"),
    ]:
        cards_html += (
            f'<div class="metric-card winner">'
            f'<div class="label">{title}</div>'
            f'<div class="value">{value}</div>'
            f'<div style="font-size:0.75rem;color:#667eea;margin-top:2px;">{winner_label}</div>'
            f"</div>"
        )
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

    # --- Side-by-side outcome comparison ---
    st.markdown("### Outcome Comparison")
    outcome_cols = st.columns(len(paths))
    for col, path, label in zip(outcome_cols, paths, labels):
        final = path[-1].state
        conf = path[-1].confidence
        conf_cls = "conf-high" if conf >= 0.7 else "conf-mid" if conf >= 0.4 else "conf-low"
        conf_label = "High" if conf >= 0.7 else "Medium" if conf >= 0.4 else "Low"

        with col:
            st.markdown(
                f'<div class="path-header">'
                f"<h3>{label}</h3>"
                f"<p>{final.career.job_title} in {final.location}"
                f'<span class="conf-badge {conf_cls}">{conf:.0%} {conf_label}</span></p>'
                f"</div>",
                unsafe_allow_html=True,
            )

            income_delta = final.finances.annual_income - root_state.finances.annual_income
            nw_delta = final.net_worth - root_state.net_worth
            sat_delta = final.life_satisfaction - root_state.life_satisfaction

            st.metric("Income", f"${final.finances.annual_income:,.0f}", f"{income_delta:+,.0f}")
            st.metric("Net Worth", f"${final.net_worth:,.0f}", f"{nw_delta:+,.0f}")
            st.metric("Satisfaction", f"{final.life_satisfaction:.1f}/10", f"{sat_delta:+.1f}")
            st.metric("Stress", f"{final.stress_level:.1f}/10",
                       f"{final.stress_level - root_state.stress_level:+.1f}",
                       delta_color="inverse")
            st.caption(
                f"**Health:** {final.health.value.title()} · "
                f"**Relationship:** {final.relationship.value.replace('_', ' ').title()}"
            )

    # --- Charts ---
    st.markdown("### Trajectories Over Time")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("**Income**")
        _plot_metric(sim_tree, paths, labels, lambda s: s.finances.annual_income)
    with chart_col2:
        st.markdown("**Net Worth**")
        _plot_metric(sim_tree, paths, labels, lambda s: s.net_worth)

    chart_col3, chart_col4 = st.columns(2)
    with chart_col3:
        st.markdown("**Life Satisfaction**")
        _plot_metric(sim_tree, paths, labels, lambda s: s.life_satisfaction)
    with chart_col4:
        st.markdown("**Stress Level**")
        _plot_metric(sim_tree, paths, labels, lambda s: s.stress_level)

    # --- Year-by-year timelines ---
    st.markdown("### Detailed Year-by-Year Timelines")
    tabs = st.tabs(labels)

    for tab, path, label in zip(tabs, paths, labels):
        with tab:
            for node in path[1:]:
                s = node.state
                conf = node.confidence
                conf_cls = "" if conf >= 0.7 else " low-conf" if conf >= 0.4 else " very-low-conf"
                conf_badge_cls = "conf-high" if conf >= 0.7 else "conf-mid" if conf >= 0.4 else "conf-low"

                income_str = f"${s.finances.annual_income:,.0f}"
                nw_str = f"${s.net_worth:,.0f}"

                st.markdown(
                    f'<div class="timeline-node{conf_cls}">'
                    f'<div class="timeline-year">{node.year} '
                    f'<span class="conf-badge {conf_badge_cls}">{conf:.0%} confidence</span></div>'
                    f'<div class="timeline-title">{s.career.job_title} — {income_str}/yr</div>'
                    f'<div class="timeline-stats">'
                    f"Net Worth: {nw_str} · "
                    f"Health: {s.health.value.title()} · "
                    f"Satisfaction: {s.life_satisfaction:.1f}/10 · "
                    f"Stress: {s.stress_level:.1f}/10"
                    f"</div>"
                    f'<div class="timeline-narrative">{s.narrative}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

    # --- Export ---
    st.markdown("---")
    from life_simulator.export import export_json, export_markdown

    output_dir = Path.home() / ".lifesim" / "results"
    export_json(sim_tree, output_dir)
    md_path = export_markdown(sim_tree, output_dir)

    col_dl1, col_dl2 = st.columns([3, 1])
    with col_dl1:
        st.success(f"Results auto-saved to `{output_dir}`")
    with col_dl2:
        with open(md_path) as f:
            st.download_button(
                "Download Report",
                f.read(),
                file_name=md_path.name,
                mime="text/markdown",
                use_container_width=True,
            )


# =====================================================================
# Session state defaults
# =====================================================================
if "step" not in st.session_state:
    st.session_state.step = 0

if "sim_result" not in st.session_state:
    st.session_state.sim_result = None
    st.session_state.sim_llm = None


# =====================================================================
# Sidebar (always visible)
# =====================================================================
with st.sidebar:
    st.markdown("### Settings")

    _PROVIDERS = {
        "Ollama (local, free)": {"prefix": "ollama", "needs_key": False, "default_model": "llama3.1"},
        "Groq (free tier)": {"prefix": "groq", "needs_key": True, "env": "GROQ_API_KEY", "default_model": "llama-3.1-70b-versatile"},
        "Anthropic": {"prefix": "anthropic", "needs_key": True, "env": "ANTHROPIC_API_KEY", "default_model": "claude-sonnet-4-20250514"},
        "OpenAI": {"prefix": "openai", "needs_key": True, "env": "OPENAI_API_KEY", "default_model": "gpt-4o"},
        "Together AI": {"prefix": "together", "needs_key": True, "env": "TOGETHER_API_KEY", "default_model": "meta-llama/Llama-3.1-70B-Instruct-Turbo"},
        "Mistral": {"prefix": "mistral", "needs_key": True, "env": "MISTRAL_API_KEY", "default_model": "mistral-large-latest"},
        "DeepSeek": {"prefix": "deepseek", "needs_key": True, "env": "DEEPSEEK_API_KEY", "default_model": "deepseek-chat"},
        "OpenRouter": {"prefix": "openrouter", "needs_key": True, "env": "OPENROUTER_API_KEY", "default_model": "meta-llama/llama-3.1-70b-instruct"},
        "Fireworks AI": {"prefix": "fireworks", "needs_key": True, "env": "FIREWORKS_API_KEY", "default_model": "accounts/fireworks/models/llama-v3p1-70b-instruct"},
        "LM Studio (local)": {"prefix": "lmstudio", "needs_key": False, "default_model": "local-model"},
    }

    provider = st.selectbox(
        "Provider",
        list(_PROVIDERS.keys()),
        help="Ollama & LM Studio run locally (free). Groq has a generous free tier.",
    )
    prov_config = _PROVIDERS[provider]
    prefix = prov_config["prefix"]

    # API key (stored in session state, NOT os.environ)
    api_key_input = None
    if prov_config["needs_key"]:
        env_var = prov_config["env"]
        api_key_input = st.text_input(
            f"{provider} API Key",
            value=os.environ.get(env_var, ""),
            type="password",
            help=f"Set via {env_var} env var or paste here.",
        )
    else:
        api_key_input = "no-key-needed"

    # Model selection
    if prefix == "anthropic":
        model = st.selectbox(
            "Model",
            ["claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"],
            help="Sonnet 4 = more capable | Haiku 4.5 = faster & cheaper",
        )
    elif prefix in ("ollama", "lmstudio"):
        local_model = st.text_input(
            "Model",
            value=prov_config["default_model"],
            help="Any model you've pulled locally.",
        )
        model = f"{prefix}/{local_model}"
    else:
        cloud_model = st.text_input("Model", value=prov_config["default_model"])
        model = f"{prefix}/{cloud_model}"

    steps = st.slider("Years to simulate", 1, 10, 5)

    st.divider()
    st.markdown(
        "<div style='font-size:0.75rem; color:#94a3b8;'>"
        "Powered by LLMs + BLS/Census data<br>"
        "Predictions are illustrative, not financial advice."
        "</div>",
        unsafe_allow_html=True,
    )


# =====================================================================
# STEP 0 — Welcome
# =====================================================================
if st.session_state.step == 0:
    st.markdown(
        '<div class="hero">'
        "<h1>Life Simulator</h1>"
        "<p>See how different decisions could shape your future — "
        "powered by AI reasoning grounded in real-world salary, "
        "cost-of-living, and career data.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    _render_steps(0)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("")
        if st.button("Start Your Simulation", type="primary", use_container_width=True):
            _go(1)
            st.rerun()

        st.markdown("")
        with st.expander("Or load an example scenario"):
            ex = st.selectbox(
                "Choose example",
                [
                    "Career Crossroads — 28yo engineer: MBA vs startup vs stay",
                    "Relocation — 32yo PM: NYC vs Austin vs remote",
                    "Career Pivot — 35yo banker: finance vs teaching vs edtech",
                    "Family Planning — 30yo DS: family now vs career first vs balance",
                ],
                label_visibility="collapsed",
            )
            if st.button("Load & Go", use_container_width=True):
                example_names = ["career_crossroads", "relocation", "career_pivot", "family_planning"]
                prefixes = ["Career Crossroads", "Relocation", "Career Pivot", "Family Planning"]
                idx = prefixes.index(ex.split(" —")[0])
                st.session_state.example = example_names[idx]
                _go(1)
                st.rerun()


# =====================================================================
# STEP 1 — About You
# =====================================================================
elif st.session_state.step == 1:
    _render_steps(1)

    example_data = _load_example(st.session_state.get("example"))

    st.markdown('<div class="section-label">Your Current Life</div>', unsafe_allow_html=True)
    st.markdown("#### Tell us about yourself")

    col1, col2, col3 = st.columns(3)
    with col1:
        age = st.number_input("Age", 16, 80, value=example_data.get("age", 28))
        location = st.text_input("City / Metro", value=example_data.get("location", "San Francisco"))
        education = st.selectbox(
            "Education",
            ["high_school", "associates", "bachelors", "masters", "mba", "phd", "professional"],
            index=["high_school", "associates", "bachelors", "masters", "mba", "phd", "professional"].index(
                example_data.get("education", "bachelors")
            ),
            format_func=lambda x: x.replace("_", " ").title(),
        )
    with col2:
        job_title = st.text_input("Job Title", value=example_data.get("job_title", "Software Engineer"))
        industry = st.text_input("Industry", value=example_data.get("industry", "Technology"))
        years_experience = st.number_input("Years of Experience", 0, 50, value=example_data.get("years_exp", 5))
    with col3:
        health = st.selectbox(
            "Health", ["excellent", "good", "fair", "poor"],
            index=["excellent", "good", "fair", "poor"].index(example_data.get("health", "good")),
            format_func=str.title,
        )
        relationship = st.selectbox(
            "Relationship",
            ["single", "partnered", "married", "divorced"],
            index=["single", "partnered", "married", "divorced"].index(
                example_data.get("relationship", "single")
            ),
            format_func=lambda x: x.replace("_", " ").title(),
        )
        dependents = st.number_input("Dependents", 0, 10, value=example_data.get("dependents", 0))

    st.markdown("---")
    st.markdown("#### Finances")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        annual_income = st.number_input("Income ($)", 0, step=5000, value=example_data.get("income", 100_000))
    with c2:
        savings = st.number_input("Savings ($)", 0, step=5000, value=example_data.get("savings", 50_000))
    with c3:
        debt = st.number_input("Debt ($)", 0, step=1000, value=example_data.get("debt", 0))
    with c4:
        monthly_expenses = st.number_input("Monthly Exp ($)", 0, step=500, value=example_data.get("expenses", 4_000))
    with c5:
        investments = st.number_input("Investments ($)", 0, step=5000, value=example_data.get("investments", 20_000))

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        satisfaction = st.slider("Life Satisfaction", 1.0, 10.0, example_data.get("satisfaction", 7.0), 0.5)
    with c2:
        stress = st.slider("Stress Level", 1.0, 10.0, example_data.get("stress", 5.0), 0.5)

    narrative = st.text_area(
        "Describe your current situation",
        value=example_data.get("narrative", ""),
        height=80,
        placeholder="E.g., Working at a mid-size tech company, feeling ready for a change...",
    )

    col_l, col_r = st.columns([4, 1])
    with col_r:
        if st.button("Next →", type="primary", use_container_width=True):
            st.session_state.person = {
                "age": age, "location": location, "education": education,
                "job_title": job_title, "industry": industry,
                "years_in_role": example_data.get("years_in_role", max(1, years_experience // 2)),
                "years_experience": years_experience,
                "income": annual_income, "savings": savings, "debt": debt,
                "expenses": monthly_expenses, "investments": investments,
                "health": health, "relationship": relationship, "dependents": dependents,
                "satisfaction": satisfaction, "stress": stress, "narrative": narrative,
            }
            _go(2)
            st.rerun()
    with col_l:
        if st.button("← Back"):
            _go(0)
            st.rerun()


# =====================================================================
# STEP 2 — Decision
# =====================================================================
elif st.session_state.step == 2:
    _render_steps(2)

    example_data = _load_example(st.session_state.get("example"))
    dec_data = example_data.get("decision", {})

    st.markdown('<div class="section-label">The Crossroads</div>', unsafe_allow_html=True)
    st.markdown("#### What decision are you facing?")

    question = st.text_input(
        "Decision",
        value=dec_data.get("question", "What should I do next?"),
        label_visibility="collapsed",
        placeholder="E.g., Should I change careers? Should we relocate?",
    )
    context = st.text_area(
        "Additional context (optional)",
        value=dec_data.get("context", ""),
        height=60,
        placeholder="Any extra details that would help the simulation...",
    )

    st.markdown("---")
    st.markdown("#### Your Options")
    default_opts = dec_data.get("options", [])
    num_options = st.radio(
        "How many paths?", [2, 3, 4, 5],
        index=min(max(len(default_opts) - 2, 0), 3),
        horizontal=True,
    )

    options_data = []
    cols = st.columns(num_options)
    for i, col in enumerate(cols):
        with col:
            defaults = default_opts[i] if i < len(default_opts) else {}
            st.markdown(
                f'<div style="background:linear-gradient(135deg,#667eea,#764ba2);'
                f'color:white;border-radius:8px;padding:0.4rem 0.8rem;'
                f'font-weight:700;font-size:0.9rem;margin-bottom:0.5rem;">'
                f'Path {i + 1}</div>',
                unsafe_allow_html=True,
            )
            label = st.text_input("Label", key=f"opt_label_{i}", value=defaults.get("label", f"Option {i + 1}"))
            desc = st.text_area(
                "What does this path look like?",
                key=f"opt_desc_{i}",
                value=defaults.get("description", ""),
                height=100,
            )
            duration = st.number_input(
                "Duration (years)", key=f"opt_dur_{i}",
                min_value=0.5, max_value=10.0,
                value=float(defaults.get("duration", 1.0)),
                step=0.5,
            )
            options_data.append({"label": label, "description": desc, "duration": duration})

    st.markdown("---")
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_l:
        if st.button("← Back"):
            _go(1)
            st.rerun()
    with col_m:
        has_key = bool(api_key_input) or not prov_config["needs_key"]
        can_run = has_key and all(o["label"] and o["description"] for o in options_data)
        if not has_key:
            st.warning("Enter your API key in the sidebar, or switch to a local provider (Ollama, LM Studio).")
        if st.button(
            "Simulate My Future",
            type="primary",
            use_container_width=True,
            disabled=not can_run,
        ):
            st.session_state.decision = {
                "question": question, "context": context, "options": options_data,
            }
            st.session_state.sim_result = None
            st.session_state.sim_llm = None
            _go(3)
            st.rerun()


# =====================================================================
# STEP 3 — Results
# =====================================================================
elif st.session_state.step == 3:
    _render_steps(3)

    # Guard: ensure prerequisites exist
    if "person" not in st.session_state or "decision" not in st.session_state:
        st.warning("Missing scenario data. Please start over.")
        _go(0)
        st.rerun()

    if st.session_state.sim_result is None:
        _run_simulation(
            st.session_state.person,
            st.session_state.decision,
            model,
            steps,
            api_key=api_key_input if api_key_input != "no-key-needed" else None,
        )

    if st.session_state.sim_result is not None:
        _display_results(st.session_state.sim_result, st.session_state.sim_llm)

    if st.button("← Start Over"):
        st.session_state.step = 0
        st.session_state.sim_result = None
        st.session_state.sim_llm = None
        st.session_state.pop("example", None)
        st.rerun()
