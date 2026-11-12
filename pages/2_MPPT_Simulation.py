"""
Page 2: Time-Domain MPPT Simulation & Electrical Dynamic Response
Interactive closed-loop simulation of the solar PV array, continuous-conduction
DC-DC boost converter, and MPPT controllers (Fuzzy Logic or P&O).
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
from src.environmental_profiles import EnvironmentalProfile, get_available_profiles
from src.simulation_engine import SimulationEngine
from src.metrics import compute_metrics
from src.visualization import plot_single_mppt_response, plot_environmental_conditions
from src.ui_helpers import (
    apply_custom_styles,
    render_header,
    render_metric_card,
    generate_csv_download,
    generate_json_download,
)

st.set_page_config(
    page_title="MPPT Simulation | Solar PV Systems",
    page_icon="⚡",
    layout="wide",
)

apply_custom_styles()

render_header(
    title="Time-Domain MPPT Simulation",
    subtitle="Closed-Loop Dynamic Analysis of Boost Converter States and Real-Time Tracking Response",
    badge="Subsystem 2 & 3: Converter Dynamics & Intelligent MPPT Tracking",
)

# Sidebar Controls
with st.sidebar:
    st.subheader("🎮 Controller Selection")
    ctrl_type = st.radio(
        "Active MPPT Algorithm",
        options=["Fuzzy Logic MPPT", "Perturb and Observe (P&O)"],
        index=0,
        help="Select the intelligent fuzzy controller or the classical P&O baseline."
    )

    st.markdown("---")
    st.subheader("🌤️ Environmental Scenario")
    duration = st.slider("Simulation Duration (s)", min_value=0.2, max_value=2.0, value=0.5, step=0.1)

    profiles = get_available_profiles(duration=duration)
    scenario_choice = st.selectbox(
        "Environmental Profile",
        options=[
            "Scenario A: Constant STC",
            "Scenario B: Sudden Irradiance Drop",
            "Scenario C: Sudden Irradiance Rise",
            "Scenario D: Temperature Rise",
            "Scenario E: Multiple Dynamic Changes",
        ],
        index=1,
    )
    profile_key = scenario_choice.split(":")[0][-1]
    active_profile = profiles[profile_key]

    st.markdown("---")
    st.subheader("⚙️ Simulation Settings")
    time_step = st.select_slider(
        "Numerical Time Step dt (s)",
        options=[2.5e-5, 5e-5, 1e-4],
        value=5e-5,
        format_func=lambda x: f"{x*1e6:.0f} µs"
    )
    sampling_time = st.select_slider(
        "Controller Sampling Time Ts (s)",
        options=[0.002, 0.005, 0.010],
        value=0.005,
        format_func=lambda x: f"{x*1000:.0f} ms"
    )

    with st.expander("🛠️ Advanced Tuning & Converter Limits"):
        d_min = st.slider("Min Duty Cycle D_min", 0.01, 0.20, 0.05, 0.01)
        d_max = st.slider("Max Duty Cycle D_max", 0.70, 0.99, 0.90, 0.01)
        initial_d = st.slider("Initial Duty Cycle D_init", d_min, d_max, 0.30, 0.05)

        if "Fuzzy" in ctrl_type:
            ke = st.number_input("Error Normalization Ke", value=10.0, step=1.0)
            kce = st.number_input("Change in Error Normalization Kce", value=100.0, step=10.0)
            k_delta_d = st.number_input("Duty Cycle Step Scaling K_delta_d", value=0.015, step=0.005, format="%.3f")
        else:
            po_step = st.number_input("P&O Perturbation Step ΔD", value=0.008, step=0.002, format="%.3f")

        load_r = st.number_input("Load Resistor R_load (Ω)", value=30.0, step=5.0)

# Build physical models
base_module = PRESET_MODULES["Canadian Solar CS5P-220M"]
array_config = PVArrayConfig(module_params=base_module, n_modules_series=1, n_strings_parallel=1)
pv_model = SingleDiodePVModel(array_config)

conv_params = BoostConverterParams(
    load_r=load_r,
    initial_d=initial_d,
)
converter = BoostConverterModel(pv_model, params=conv_params)

sim_config = SimulationConfig(
    duration=duration,
    time_step=time_step,
)

engine = SimulationEngine(
    pv_model=pv_model,
    converter=converter,
    profile=active_profile,
    sim_config=sim_config,
)

# Instantiate selected controller
if "Fuzzy" in ctrl_type:
    f_params = FuzzyControllerParams(
        ke=ke,
        kce=kce,
        k_delta_d=k_delta_d,
        d_min=d_min,
        d_max=d_max,
        sampling_time=sampling_time,
    )
    controller = FuzzyMPPTController(params=f_params)
else:
    po_params = POControllerParams(
        delta_d_step=po_step,
        d_min=d_min,
        d_max=d_max,
        sampling_time=sampling_time,
    )
    controller = POController(params=po_params)

# Run Simulation Action
col_run, col_status = st.columns([1, 4])
with col_run:
    run_btn = st.button("🚀 Run MPPT Simulation", use_container_width=True)

# Session state persistence for simulation results
state_key = f"sim_res_{ctrl_type}_{profile_key}_{duration}"
if run_btn or state_key not in st.session_state:
    with st.spinner(f"Integrating continuous boost dynamics with {ctrl_type}..."):
        df_sim = engine.run(
            controller=controller,
            controller_sampling_time=sampling_time,
            downsample_factor=2,  # Efficient rendering
        )
        st.session_state[state_key] = df_sim
else:
    df_sim = st.session_state[state_key]

# Compute quantitative metrics
metrics = compute_metrics(
    df_sim,
    settling_tolerance_pct=2.0,
    transition_times=active_profile.transition_times,
)

# Display Key Performance Indicator (KPI) Cards
kpi_cols = st.columns(6)
with kpi_cols[0]:
    render_metric_card("Tracking Efficiency (η)", f"{metrics.tracking_efficiency_energy:.2f} %", "Energy-based extraction")
with kpi_cols[1]:
    render_metric_card("Total Energy (Wh)", f"{metrics.energy_extracted_wh:.4f} Wh", f"Loss: {metrics.energy_loss_wh:.4f} Wh")
with kpi_cols[2]:
    render_metric_card("Average PV Power", f"{metrics.avg_pv_power:.1f} W", f"Peak: {metrics.peak_pv_power:.1f} W")
with kpi_cols[3]:
    st_str = f"{metrics.settling_time_s * 1000.0:.1f} ms" if metrics.settling_time_s is not None else "Oscillating"
    render_metric_card("Settling Time", st_str, "Within ±2% band")
with kpi_cols[4]:
    render_metric_card("Steady-State Ripple (ΔP)", f"{metrics.oscillation_amplitude_w:.3f} W", f"Std Dev: {metrics.oscillation_std_w:.3f} W")
with kpi_cols[5]:
    render_metric_card("Converter Efficiency", f"{metrics.converter_avg_efficiency:.1f} %", f"P_load / P_pv (R={load_r}Ω)")

st.markdown("---")

# Environmental Condition Timeline
st.markdown("### ☀️ Environmental Disturbance Profile")
fig_env = plot_environmental_conditions(df_sim, active_profile.transition_times)
st.plotly_chart(fig_env, use_container_width=True)

# Real-Time Telemetry Graphs
st.markdown(f"### 📊 Dynamic Response: {ctrl_type}")
fig_sim = plot_single_mppt_response(df_sim, active_profile.transition_times)
st.plotly_chart(fig_sim, use_container_width=True)

# Telemetry Data Export Section
st.markdown("---")
st.markdown("### 💾 Export Simulation Telemetry")
d_col1, d_col2 = st.columns(2)

with d_col1:
    csv_data = generate_csv_download(df_sim, "mppt_simulation_telemetry.csv")
    st.download_button(
        label="📥 Download Telemetry Time-Series (CSV)",
        data=csv_data,
        file_name=f"mppt_{ctrl_type.replace(' ', '_').lower()}_{profile_key}.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.caption("Contains columns: time, irradiance, temperature, v_pv, i_pv, p_pv, p_mpp_ref, duty_cycle, v_out, i_inductor, p_out.")

with d_col2:
    meta_dict = {
        "controller": ctrl_type,
        "profile": active_profile.name,
        "duration": duration,
        "time_step": time_step,
        "sampling_time": sampling_time,
        "metrics": {
            "tracking_efficiency_energy": metrics.tracking_efficiency_energy,
            "energy_extracted_wh": metrics.energy_extracted_wh,
            "energy_loss_wh": metrics.energy_loss_wh,
            "avg_pv_power": metrics.avg_pv_power,
            "settling_time_s": metrics.settling_time_s,
            "oscillation_amplitude_w": metrics.oscillation_amplitude_w,
        }
    }
    json_str = generate_json_download(meta_dict, "mppt_config_and_metrics.json")
    st.download_button(
        label="📥 Download Run Metadata & Metrics (JSON)",
        data=json_str,
        file_name=f"mppt_metadata_{ctrl_type.replace(' ', '_').lower()}.json",
        mime="application/json",
        use_container_width=True,
    )
    st.caption("Machine-readable JSON export of all physical constants, settings, and verified performance metrics.")
