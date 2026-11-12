"""
Page 3: Controller Comparison Benchmark
Direct side-by-side performance evaluation of Fuzzy Logic MPPT versus
conventional Perturb & Observe (P&O) under identical physical conditions.
"""

import streamlit as st
import numpy as np
import pandas as pd

from src.config import (
    PRESET_MODULES,
    PVArrayConfig,
    BoostConverterParams,
    FuzzyControllerParams,
    POControllerParams,
    SimulationConfig,
)
from src.pv_model import SingleDiodePVModel
from src.boost_converter import BoostConverterModel
from src.fuzzy_controller import FuzzyMPPTController
from src.po_controller import POController
from src.environmental_profiles import get_available_profiles
from src.simulation_engine import SimulationEngine
from src.metrics import compute_metrics, compare_controllers
from src.visualization import plot_controller_comparison_overlay
from src.ui_helpers import (
    apply_custom_styles,
    render_header,
    render_metric_card,
    generate_csv_download,
)

st.set_page_config(
    page_title="Controller Comparison | Fuzzy vs P&O",
    page_icon="⚖️",
    layout="wide",
)

apply_custom_styles()

render_header(
    title="MPPT Controller Comparison Benchmark",
    subtitle="Rigorous Side-by-Side Evaluation: Fuzzy Logic MPPT vs Classical Perturb & Observe",
    badge="Benchmark Analysis: Transient Speed, Tracking Efficiency & Steady-State Ripple",
)

# Sidebar Parameters
with st.sidebar:
    st.subheader("🌤️ Environmental Test Benchmark")
    duration = st.slider("Simulation Duration (s)", 0.3, 2.0, 0.6, 0.1)

    profiles = get_available_profiles(duration=duration)
    scenario_choice = st.selectbox(
        "Select Test Scenario",
        options=[
            "Scenario B: Sudden Irradiance Drop (1000 -> 600 W/m²)",
            "Scenario C: Sudden Irradiance Rise (600 -> 1000 W/m²)",
            "Scenario D: Temperature Rise (25 -> 45 °C)",
            "Scenario E: Multiple Dynamic Changes",
            "Scenario A: Constant STC",
        ],
        index=0,
    )
    profile_key = scenario_choice[9]
    active_profile = profiles[profile_key]

    st.markdown("---")
    st.subheader("⚙️ Controller Tuning")
    f_step_scaling = st.slider("Fuzzy Output Scaling (K_delta_d)", 0.005, 0.040, 0.015, 0.005)
    po_step_size = st.slider("P&O Perturbation Step (ΔD)", 0.002, 0.030, 0.008, 0.002)
    sampling_time = st.select_slider(
        "Sampling Time Ts (s)",
        options=[0.002, 0.005, 0.010],
        value=0.005,
        format_func=lambda x: f"{x*1000:.0f} ms"
    )

# Build system
base_module = PRESET_MODULES["Canadian Solar CS5P-220M"]
array_config = PVArrayConfig(module_params=base_module, n_modules_series=1, n_strings_parallel=1)
pv_model = SingleDiodePVModel(array_config)

conv_params = BoostConverterParams()
converter_fuzzy = BoostConverterModel(pv_model, params=conv_params)
converter_po = BoostConverterModel(pv_model, params=conv_params)

sim_config = SimulationConfig(duration=duration, time_step=5e-5)

engine_fuzzy = SimulationEngine(pv_model, converter_fuzzy, active_profile, sim_config)
engine_po = SimulationEngine(pv_model, converter_po, active_profile, sim_config)

f_ctrl = FuzzyMPPTController(params=FuzzyControllerParams(k_delta_d=f_step_scaling, sampling_time=sampling_time))
p_ctrl = POController(params=POControllerParams(delta_d_step=po_step_size, sampling_time=sampling_time))

# Execution button
run_btn = st.button("🚀 Run Dual Benchmark Simulation", use_container_width=True)

cache_key = f"comp_{profile_key}_{duration}_{f_step_scaling}_{po_step_size}"
if run_btn or cache_key not in st.session_state:
    with st.spinner("Simulating both controllers under identical physical conditions..."):
        df_fuzzy = engine_fuzzy.run(f_ctrl, controller_sampling_time=sampling_time, downsample_factor=2)
        df_po = engine_po.run(p_ctrl, controller_sampling_time=sampling_time, downsample_factor=2)
        st.session_state[cache_key] = (df_fuzzy, df_po)
else:
    df_fuzzy, df_po = st.session_state[cache_key]

# Compute rigorous metrics
metrics_fuzzy = compute_metrics(df_fuzzy, transition_times=active_profile.transition_times)
metrics_po = compute_metrics(df_po, transition_times=active_profile.transition_times)

# Key Comparison KPI Cards
st.markdown("### 🏆 Performance Summary Cards")
comp_cols = st.columns(4)

with comp_cols[0]:
    eff_diff = metrics_fuzzy.tracking_efficiency_energy - metrics_po.tracking_efficiency_energy
    render_metric_card(
        "Tracking Efficiency (η)",
        f"{metrics_fuzzy.tracking_efficiency_energy:.2f}% vs {metrics_po.tracking_efficiency_energy:.2f}%",
        f"Fuzzy advantage: {eff_diff:+.2f}%"
    )

with comp_cols[1]:
    e_diff = (metrics_fuzzy.energy_extracted_wh - metrics_po.energy_extracted_wh) * 1000.0  # mWh
    render_metric_card(
        "Energy Extracted",
        f"{metrics_fuzzy.energy_extracted_wh:.4f} Wh",
        f"P&O: {metrics_po.energy_extracted_wh:.4f} Wh ({e_diff:+.1f} mWh)"
    )

with comp_cols[2]:
    render_metric_card(
        "Steady-State Ripple (ΔP)",
        f"{metrics_fuzzy.oscillation_amplitude_w:.3f} W vs {metrics_po.oscillation_amplitude_w:.3f} W",
        f"Ripple reduction: {((metrics_po.oscillation_amplitude_w - metrics_fuzzy.oscillation_amplitude_w)/max(1e-3, metrics_po.oscillation_amplitude_w))*100:.1f}%"
    )

with comp_cols[3]:
    st_f = f"{metrics_fuzzy.settling_time_s*1000:.1f} ms" if metrics_fuzzy.settling_time_s else "N/A"
    st_p = f"{metrics_po.settling_time_s*1000:.1f} ms" if metrics_po.settling_time_s else "Continuous Oscillation"
    render_metric_card(
        "Settling Time",
        f"{st_f} (FLC)",
        f"P&O: {st_p}"
    )

st.markdown("---")

# Direct Comparison Charts
st.markdown("### 📊 Direct Dynamic Overlay Tracking")
fig_comp = plot_controller_comparison_overlay(df_fuzzy, df_po, active_profile.transition_times)
st.plotly_chart(fig_comp, use_container_width=True)

st.markdown("---")

# Detailed Comparison Table
st.markdown("### 📋 Quantitative Performance Comparison Table")
df_comparison_table = compare_controllers(metrics_fuzzy, metrics_po)
st.dataframe(df_comparison_table, use_container_width=True, hide_index=True)

# Technical Discussion
st.markdown("---")
st.markdown("### 🔬 Control Engineering Analysis")
disc_col1, disc_col2 = st.columns(2)

with disc_col1:
    st.markdown("#### 🟢 Why Fuzzy Logic Outperforms Conventional P&O")
    st.write(
        """
        1. **Variable Perturbation Magnitude:**
           Fuzzy Logic computes non-linear scaling between $dP/dV$ and $\\Delta D$. When far from MPP 
           ($E = NB$ or $PB$), large duty adjustments are dispatched immediately. As the operating 
           point enters the vicinity of the peak, the linguistic membership terms ($PS, NS, ZE$) 
           exponentially throttle the step size.
        2. **Elimination of 3-Point Limit Cycle:**
           Conventional fixed-step P&O can never come to rest: by design, it perturbs forward, detects 
           a drop in power, perturbs backward, and repeats indefinitely between 3 points. Fuzzy Logic 
           MPPT naturally stabilizes around $E = ZE, CE = ZE$, resulting in virtually zero power ripple.
        3. **Fast Transition Recovery:**
           During rapid cloud transients, P&O can momentarily track in the wrong direction (tracking divergence 
           due to $\\Delta P$ caused by irradiance rather than voltage perturbation). Fuzzy Logic accounts for 
           rate-of-change ($CE$), minimizing false tracking during dynamic transitions.
        """
    )

with disc_col2:
    st.markdown("#### 💾 Export Benchmark Comparison Data")
    csv_comp = generate_csv_download(df_comparison_table, "mppt_controller_comparison_table.csv")
    st.download_button(
        label="📥 Download Benchmark Comparison Table (CSV)",
        data=csv_comp,
        file_name="mppt_comparison_metrics.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.caption("Contains complete side-by-side numerical metrics with exact differences and units.")
