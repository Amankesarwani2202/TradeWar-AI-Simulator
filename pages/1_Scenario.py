import numpy as np
import streamlit as st
from utils import (
    COUNTRIES, CATEGORIES,
    inject_css, generate_trade_data, build_trade_network,
    build_country_scenario, build_teaching_explanation, render_teaching_panel,
    apply_policy_shock_to_scenario, build_policy_shock_summary,
    render_scenario_summary_metrics, render_overview_tab,
    render_forecast_tab, render_network_tab,
)

inject_css()

np.random.seed(42)
df = generate_trade_data()
G, _, _ = build_trade_network()

# ── Scenario presets ──────────────────────────────────────────────────────────
# Format: country = EXPORTER being affected | target_partner = the tariff IMPOSER
PRESET_GROUPS = {
    "🌍 Global Trade War": {
        "US tariffs on China electronics (+25%)": {"country": "China", "category": "Electronics", "target_partner": "US", "tariff_change": 25},
        "US tariffs on China semiconductors (+20%)": {"country": "China", "category": "Semiconductors", "target_partner": "US", "tariff_change": 20},
        "EU tariffs on Vietnam textiles (+15%)": {"country": "Vietnam", "category": "Textiles", "target_partner": "EU", "tariff_change": 15},
        "US-China Phase 1 deal reversal: machinery (+20%)": {"country": "China", "category": "Machinery", "target_partner": "US", "tariff_change": 20},
        "Taiwan chip export block to China (+30%)": {"country": "Taiwan", "category": "Semiconductors", "target_partner": "China", "tariff_change": 30},
        "EU carbon border tariff on Chinese steel (+25%)": {"country": "China", "category": "Steel", "target_partner": "EU", "tariff_change": 25},
        "South Korea–Japan semiconductor rivalry (–10%)": {"country": "South Korea", "category": "Semiconductors", "target_partner": "US", "tariff_change": -10},
    },
    "🇮🇳 India Trade Scenarios": {
        "India: Atma Nirbhar — import tariff on Chinese electronics (+30%)": {"country": "China", "category": "Electronics", "target_partner": "India", "tariff_change": 30},
        "India: PLI semiconductor boost — US cuts tariffs on India (–12%)": {"country": "India", "category": "Semiconductors", "target_partner": "US", "tariff_change": -12},
        "India: Textile FTA with EU — EU cuts tariffs (–15%)": {"country": "India", "category": "Textiles", "target_partner": "EU", "tariff_change": -15},
        "India: API chemical import tariff on China (+20%)": {"country": "China", "category": "Chemicals", "target_partner": "India", "tariff_change": 20},
        "India: Steel anti-dumping tariff on China (+25%)": {"country": "China", "category": "Steel", "target_partner": "India", "tariff_change": 25},
        "India: Electronics export push to US — US lowers tariffs (–8%)": {"country": "India", "category": "Electronics", "target_partner": "US", "tariff_change": -8},
        "India: US tariffs on Indian semiconductors (+20%)": {"country": "India", "category": "Semiconductors", "target_partner": "US", "tariff_change": 20},
        "India: Dependency shift — away from Chinese electronics (–18%)": {"country": "India", "category": "Electronics", "target_partner": "China", "tariff_change": -18},
        "India: EU FTA on chemicals and pharma (–20%)": {"country": "India", "category": "Chemicals", "target_partner": "EU", "tariff_change": -20},
        "India: US tech tariff friction — machinery proxy (+10%)": {"country": "India", "category": "Machinery", "target_partner": "US", "tariff_change": 10},
        "India vs Vietnam: textiles race in EU market (+12% on India)": {"country": "India", "category": "Textiles", "target_partner": "EU", "tariff_change": 12},
        "India: Bangladesh garment competition — Bangladesh gets EU cut (–12%)": {"country": "Bangladesh", "category": "Textiles", "target_partner": "EU", "tariff_change": -12},
    },
    "🏭 Supply Chain Diversification": {
        "Vietnam gains as China loses: electronics to US": {"country": "Vietnam", "category": "Electronics", "target_partner": "US", "tariff_change": -8},
        "Bangladesh textile boom: US lowers tariffs (–20%)": {"country": "Bangladesh", "category": "Textiles", "target_partner": "US", "tariff_change": -20},
        "Thailand: auto parts & machinery boost to US (–10%)": {"country": "Thailand", "category": "Machinery", "target_partner": "US", "tariff_change": -10},
        "India replaces China in US electronics supply chain (–15%)": {"country": "India", "category": "Electronics", "target_partner": "US", "tariff_change": -15},
        "Taiwan dominant in semiconductors — US further lowers (–8%)": {"country": "Taiwan", "category": "Semiconductors", "target_partner": "US", "tariff_change": -8},
    },
    "📉 Trade War Escalations": {
        "Full escalation: US +30% on all China electronics": {"country": "China", "category": "Electronics", "target_partner": "US", "tariff_change": 30},
        "China retaliates: +25% on US machinery": {"country": "US", "category": "Machinery", "target_partner": "China", "tariff_change": 25},
        "EU–US trade friction: steel tariffs (+20%)": {"country": "EU", "category": "Steel", "target_partner": "US", "tariff_change": 20},
        "India–China border escalation: all categories (+25%)": {"country": "China", "category": "Machinery", "target_partner": "India", "tariff_change": 25},
    },
}

# Flatten into a single selectbox list with group labels
PRESET_FLAT = {"— Custom (set your own below) —": {"country": "China", "category": "Electronics", "target_partner": "US", "tariff_change": 10}}
for group_label, presets in PRESET_GROUPS.items():
    for k, v in presets.items():
        PRESET_FLAT[f"{group_label} › {k}"] = v

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.markdown("<h2 style='font-size:1.3rem;color:#1f2937;margin-bottom:0.75rem;'>⚙️ Build Your Scenario</h2>", unsafe_allow_html=True)
st.sidebar.caption("**Step 1:** Choose a preset or build your own. **Step 2:** Fine-tune below.")

preset_key = st.sidebar.selectbox(
    "Scenario preset",
    list(PRESET_FLAT.keys()),
    help="Pre-configured scenarios that reflect real-world trade policy situations",
)
selected = PRESET_FLAT[preset_key]

st.sidebar.divider()
st.sidebar.markdown("**Step 2 — Fine-tune the scenario parameters**")

country = st.sidebar.selectbox(
    "Affected exporter",
    COUNTRIES,
    index=COUNTRIES.index(selected["country"]),
    help="Which country's exports are being hit by the tariff? This is the seller.",
)
category = st.sidebar.selectbox(
    "Product category",
    ["Electronics", "Textiles", "Semiconductors", "Machinery", "Chemicals", "Steel"],
    index=["Electronics", "Textiles", "Semiconductors", "Machinery", "Chemicals", "Steel"].index(selected["category"]),
    help="The type of good being taxed. Different goods have different price sensitivities.",
)
target_partner = st.sidebar.selectbox(
    "Tariff imposer (importer)",
    ["US", "EU", "China", "India", "Japan", "South Korea"],
    index=["US", "EU", "China", "India", "Japan", "South Korea"].index(
        selected["target_partner"] if selected["target_partner"] in ["US", "EU", "China", "India", "Japan", "South Korea"] else "US"
    ),
    help="Which country is imposing the tariff? This is the buyer who sets the barrier.",
)
tariff_change = st.sidebar.slider(
    "Tariff change (%)",
    min_value=-30, max_value=30, value=selected["tariff_change"], step=1,
    help="Positive = tariff INCREASE (exports fall). Negative = tariff REDUCTION (exports rise).",
)
forecast_steps = st.sidebar.slider("Forecast horizon (years)", min_value=1, max_value=5, value=3, step=1)

if tariff_change > 0:
    direction_hint = "Tariff increase — exporter loses"
    hint_color = "#ef4444"
elif tariff_change < 0:
    direction_hint = "Tariff reduction — exporter gains"
    hint_color = "#16a34a"
else:
    direction_hint = "No change from baseline"
    hint_color = "#6b7280"
st.sidebar.markdown(
    f'<div style="background:#f8fafc;padding:0.5rem 0.75rem;border-radius:0.4rem;border-left:3px solid {hint_color};">'
    f'<p style="margin:0;font-size:0.82rem;font-weight:600;color:{hint_color};">{direction_hint}</p>'
    f"</div>",
    unsafe_allow_html=True,
)

st.sidebar.divider()
st.sidebar.markdown("**Optional: Historical shock overlay**")
st.sidebar.caption("Combine the tariff scenario with a historical event to see compounding effects.")
historical_event = st.sidebar.selectbox(
    "Historical policy shock",
    ["None", "Post-9/11 US financial stabilization", "COVID-19 trade disruption", "India 2016 demonetization shock"],
)
shock_pct = st.sidebar.slider("Shock intensity (%)", min_value=-20, max_value=20, value=5, step=1)

# ── Main content ─────────────────────────────────────────────────────────────
st.title("⚙️ Custom Scenario Simulator")
st.markdown(
    '<p style="font-size:1.05rem;color:#6b7280;margin-top:-0.75rem;margin-bottom:1.5rem;">'
    "Model how tariff changes ripple through supply chains, forecasts, and trade networks — with step-by-step economic explanations"
    "</p>",
    unsafe_allow_html=True,
)

# Context banner
tariff_direction_word = "increase" if tariff_change > 0 else "reduction" if tariff_change < 0 else "no change"
_ctx_border = "#ef4444" if tariff_change > 0 else "#16a34a" if tariff_change < 0 else "#6b7280"
st.markdown(
    f'<div style="background:#f8fafc;padding:1rem 1.25rem;border-radius:0.5rem;border:1px solid #e2e8f0;border-left:4px solid {_ctx_border};margin-bottom:1.5rem;">'
    f'<p style="margin:0;font-size:0.95rem;font-weight:600;color:#0f172a;">'
    f'{abs(tariff_change)}% tariff {tariff_direction_word} &nbsp;·&nbsp; {country} → {target_partner} &nbsp;·&nbsp; {category}'
    f'</p>'
    f'<p style="margin:0.3rem 0 0 0;font-size:0.82rem;color:#64748b;">'
    f'{target_partner} {"raises" if tariff_change > 0 else "cuts" if tariff_change < 0 else "keeps"} tariffs on {country}\'s {category} by {abs(tariff_change)}%. '
    f'Trade elasticity applied across all 10 economies.'
    f'</p>'
    f'</div>',
    unsafe_allow_html=True,
)

# Compute scenario
from utils import TRADE_ELASTICITY
scenario = build_country_scenario(df, country, category, tariff_change, target_partner, projection_horizon=forecast_steps)
scenario = apply_policy_shock_to_scenario(scenario, historical_event, shock_pct)
teaching = build_teaching_explanation(scenario, tariff_change)

# ── Summary metrics ───────────────────────────────────────────────────────────
st.markdown("### 📊 Scenario Summary")
render_scenario_summary_metrics(scenario)

# Outcome box
st.markdown("<br/>", unsafe_allow_html=True)
emoji = "📉" if tariff_change > 0 else "📈" if tariff_change < 0 else "➡️"
_border = "#ef4444" if tariff_change > 0 else "#16a34a" if tariff_change < 0 else "#6b7280"
st.markdown(
    f'<div style="background:#f8fafc;padding:1.25rem 1.5rem;border-radius:0.5rem;border:1px solid #e2e8f0;border-left:4px solid {_border};">'
    f'<p style="margin:0;font-size:0.88rem;color:#374151;">'
    f'<strong>{abs(tariff_change)}% tariff {tariff_direction_word}</strong> on '
    f'<strong>{country}\'s {category}</strong> exports to <strong>{target_partner}</strong>'
    f'</p>'
    f'<p style="margin:0.6rem 0 0 0;font-size:1.1rem;font-weight:700;color:#0f172a;">'
    f'{emoji} Predicted exports: '
    f'<span style="color:#64748b;">${scenario["baseline_export_bn"]:.1f}B</span> → '
    f'<span style="color:#0f172a;">${scenario["predicted_export_bn"]:.1f}B</span>'
    f'<span style="font-size:0.85rem;font-weight:400;color:#64748b;"> ({scenario["trade_change_pct"]:+.1f}% | ${scenario["trade_delta_bn"]:+.1f}B)</span>'
    f'</p>'
    f'</div>',
    unsafe_allow_html=True,
)

if historical_event != "None":
    st.info(f"⚙️ **Historical shock also applied:** {build_policy_shock_summary(historical_event, shock_pct)}")

# ── Who benefits? ─────────────────────────────────────────────────────────────
st.markdown("### 🎯 Who benefits in this scenario?")
b_type = scenario.get("beneficiary_type", "none")
col_ben1, col_ben2 = st.columns(2, gap="medium")

with col_ben1:
    beneficiaries = scenario["likely_beneficiaries"]
    if beneficiaries and b_type == "diversion":
        label = f"Alternative suppliers capturing trade diverted away from {country}"
        st.markdown(
            f'<div style="background:#f0f9ff;padding:1.2rem;border-radius:0.5rem;border-left:4px solid #06b6d4;">'
            f'<p style="margin:0;font-size:0.8rem;color:#0e7490;font-weight:600;margin-bottom:0.3rem;">🚀 Trade diversion beneficiaries</p>'
            f'<p style="margin:0;font-size:1rem;font-weight:700;color:#0369a1;">{", ".join(beneficiaries)}</p>'
            f'<p style="margin:0.3rem 0 0 0;font-size:0.8rem;color:#6b7280;">{label}</p>'
            f"</div>",
            unsafe_allow_html=True,
        )
    elif beneficiaries and b_type == "gain":
        label = f"Countries benefiting from {country}'s improved access to {target_partner}"
        st.markdown(
            f'<div style="background:#f0fdf4;padding:1.2rem;border-radius:0.5rem;border-left:4px solid #22c55e;">'
            f'<p style="margin:0;font-size:0.8rem;color:#15803d;font-weight:600;margin-bottom:0.3rem;">🏆 Beneficiaries of lower tariffs</p>'
            f'<p style="margin:0;font-size:1rem;font-weight:700;color:#166534;">{", ".join(beneficiaries)}</p>'
            f'<p style="margin:0.3rem 0 0 0;font-size:0.8rem;color:#6b7280;">{label}</p>'
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="background:#f3f4f6;padding:1.2rem;border-radius:0.5rem;border-left:4px solid #9ca3af;">'
            '<p style="margin:0;font-size:0.9rem;color:#6b7280;">📊 No significant beneficiaries at this tariff magnitude</p>'
            "</div>",
            unsafe_allow_html=True,
        )

with col_ben2:
    diversion_pool = sum(scenario["trade_diversion"].values())
    if diversion_pool > 0:
        pool_label = "Estimated trade diverted to alternatives" if b_type == "diversion" else "Estimated export revenue gain"
        st.markdown(
            f'<div style="background:#fef3c7;padding:1.2rem;border-radius:0.5rem;border-left:4px solid #f59e0b;">'
            f'<p style="margin:0;font-size:0.8rem;color:#92400e;font-weight:600;margin-bottom:0.3rem;">💱 {pool_label}</p>'
            f'<p style="margin:0;font-size:1.5rem;font-weight:800;color:#d97706;">${diversion_pool:.1f}B</p>'
            f'<p style="margin:0.25rem 0 0 0;font-size:0.75rem;color:#b45309;">Per year, over the forecast horizon</p>'
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="background:#f3f4f6;padding:1.2rem;border-radius:0.5rem;border-left:4px solid #9ca3af;">'
            '<p style="margin:0;font-size:0.9rem;color:#6b7280;">Trade flows remain near equilibrium — no significant diversion pool</p>'
            "</div>",
            unsafe_allow_html=True,
        )

# ── Teaching explanation ───────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🎓 Economics Explanation")
st.caption("Understand *why* these outputs are predicted — the mechanism behind the numbers.")
render_teaching_panel(teaching)

# ── Analysis tabs ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📈 Deep-Dive Analysis")
overview_tab, forecast_tab, network_tab = st.tabs(["📊 Overview & Impact", "🔮 Forecast & Scenarios", "🕸️ Trade Network"])

with overview_tab:
    render_overview_tab(scenario, scenario["impact_df"])

with forecast_tab:
    render_forecast_tab(df, country, category, tariff_change, forecast_steps)

with network_tab:
    render_network_tab(G, country, category, tariff_change, target_partner)

# ── About ─────────────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("📚 How this simulator works", expanded=False):
    from utils import TRADE_ELASTICITY as TE
    elasticity_val = TE.get(category, -0.7)
    st.markdown(
        f"""
        **Core formula**: Export change (%) = Trade elasticity × Tariff change (%)

        - Selected category: **{category}** | Elasticity: **{elasticity_val:.1f}**
        - Applied tariff: **{tariff_change:+.0f}%**
        - Predicted trade response: **{elasticity_val * tariff_change:.1f}%** (before horizon adjustment)

        **Elasticity values by category:**
        | Category | Elasticity | Meaning |
        |---|---|---|
        | Semiconductors | -0.9 | Very sensitive — small tariff = large trade impact |
        | Electronics | -0.8 | Highly sensitive |
        | Machinery | -0.7 | Moderate sensitivity |
        | Steel | -0.7 | Moderate sensitivity |
        | Textiles | -0.6 | Somewhat sensitive |
        | Chemicals | -0.5 | Less sensitive — harder to substitute |

        **Trade network**: Uses category-specific bilateral multipliers so import dependency, export reach,
        and bridge scores reflect the actual topology of that product's supply chain — not overall trade.

        **Beneficiary threshold**: Only shown if the estimated trade diversion exceeds $0.5B per year.
        Small tariff changes show no beneficiaries because the diversion is economically negligible.
        """
    )
