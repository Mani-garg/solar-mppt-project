"""
Page 1: Photovoltaic (PV) Panel & Array Simulator
Interactive exploration of single-diode physical modeling, I-V / P-V curves,
and true theoretical Maximum Power Point (MPP) extraction.
"""

import streamlit as st
import numpy as np
import pandas as pd

from src.config import PRESET_MODULES, PVModuleParams, PVArrayConfig
from src.pv_model import SingleDiodePVModel
from src.visualization import plot_iv_pv_curves
from src.ui_helpers import apply_custom_styles, render_header, render_metric_card, generate_csv_download

st.set_page_config(
    page_title="PV Panel Simulator | Solar MPPT",
    page_icon="☀️",
    layout="wide",
)

apply_custom_styles()

render_header(
    title="Photovoltaic (PV) Semiconductor Array Simulator",
    subtitle="Five-Parameter Single-Diode Model Characterization and Numerical Reference MPP Extraction",
    badge="Module 1: Photovoltaic Generator Characterization",
)

# Sidebar Parameters
with st.sidebar:
    st.markdown("### Environmental Conditions")
    irradiance = st.slider(
        "Solar Irradiance G (W/m²)",
        min_value=100.0,
        max_value=1500.0,
        value=1000.0,
        step=50.0,
        help="Standard Test Condition (STC) irradiance is 1000 W/m²."
    )
    temperature_c = st.slider(
        "Cell Junction Temperature T (°C)",
        min_value=-10.0,
        max_value=85.0,
        value=25.0,
        step=1.0,
        help="Standard Test Condition (STC) cell temperature is 25°C."
    )

    st.markdown("---")
    st.markdown("### Array Configuration")
    module_choice = st.selectbox(
        "PV Module Specification",
        options=list(PRESET_MODULES.keys()),
        index=0,
    )
    base_module = PRESET_MODULES[module_choice]

    n_series = st.number_input(
        "Series Modules (Ns)",
        min_value=1,
        max_value=20,
        value=1,
        step=1,
        help="Increases total string voltage: V_array = Ns * V_module"
    )
    n_parallel = st.number_input(
        "Parallel Strings (Np)",
        min_value=1,
        max_value=20,
        value=1,
        step=1,
        help="Increases total string current: I_array = Np * I_module"
    )

    with st.expander("Single-Diode Circuit Parameters"):
        r_s_custom = st.number_input("Series Resistance Rs (Ω)", value=float(base_module.r_s), step=0.05, format="%.3f")
        r_sh_custom = st.number_input("Shunt Resistance Rsh (Ω)", value=float(base_module.r_sh), step=10.0, format="%.1f")
        n_custom = st.number_input("Ideality Factor n", value=float(base_module.ideality_n), step=0.01, format="%.2f")

# Build array model
custom_params = PVModuleParams(
    name=base_module.name,
    n_series_cells=base_module.n_series_cells,
    p_mp=base_module.p_mp,
    v_mp=base_module.v_mp,
    i_mp=base_module.i_mp,
    v_oc=base_module.v_oc,
    i_sc=base_module.i_sc,
    alpha_sc=base_module.alpha_sc,
    beta_voc=base_module.beta_voc,
    r_s=r_s_custom,
    r_sh=r_sh_custom,
    ideality_n=n_custom,
    i_0_ref=base_module.i_0_ref,
)

array_config = PVArrayConfig(
    module_params=custom_params,
    n_modules_series=int(n_series),
    n_strings_parallel=int(n_parallel),
)

pv_model = SingleDiodePVModel(array_config)

# Compute curves and theoretical MPP
v_vec, i_vec, p_vec, mpp = pv_model.generate_characteristic_curves(
    irradiance=irradiance,
    temperature_c=temperature_c,
    num_points=150,
)

# Fill Factor (FF)
ff = (mpp.p_mpp / (mpp.v_oc * mpp.i_sc)) if (mpp.v_oc * mpp.i_sc) > 1e-3 else 0.0

# Display Key Metrics
kpi_cols = st.columns(6)
with kpi_cols[0]:
    render_metric_card("Max Power (Pmp)", f"{mpp.p_mpp:.1f} W", f"{array_config.total_modules} module(s)")
with kpi_cols[1]:
    render_metric_card("MPP Voltage (Vmp)", f"{mpp.v_mpp:.2f} V", f"{mpp.v_mpp/mpp.v_oc*100:.1f}% of Voc")
with kpi_cols[2]:
    render_metric_card("MPP Current (Imp)", f"{mpp.i_mpp:.2f} A", f"{mpp.i_mpp/mpp.i_sc*100:.1f}% of Isc")
with kpi_cols[3]:
    render_metric_card("Open-Circuit (Voc)", f"{mpp.v_oc:.2f} V", f"T = {temperature_c:.1f}°C")
with kpi_cols[4]:
    render_metric_card("Short-Circuit (Isc)", f"{mpp.i_sc:.2f} A", f"G = {irradiance:.0f} W/m²")
with kpi_cols[5]:
    render_metric_card("Fill Factor (FF)", f"{ff:.3f}", f"{ff*100:.1f}% quality")

st.markdown("---")

# Characteristic Curves Plot
st.markdown("### Characteristic Output Curves (I-V and P-V)")
fig = plot_iv_pv_curves(v_vec, i_vec, p_vec, mpp)
st.plotly_chart(fig, use_container_width=True)

# Technical Interpretation & Export
exp_col1, exp_col2 = st.columns([3, 1])

with exp_col1:
    st.markdown("#### Parameter Sensitivity & Physical Behavior")
    st.markdown(
        f"""
        - **Irradiance Dependency:** At **{irradiance:.0f} W/m²**, short-circuit current is 
          **{mpp.i_sc:.2f} A**. Short-circuit current $I_{{sc}}$ varies linearly with incident photon flux 
          ($I_{{ph}} \\propto G$). Series and shunt resistances cause the curve shoulder to round slightly.
        - **Temperature Dependency:** At **{temperature_c:.1f}°C**, open-circuit voltage is 
          **{mpp.v_oc:.2f} V**. As temperature increases, semiconductor bandgap narrowing elevates the 
          intrinsic carrier concentration $n_i(T)$ and reverse saturation current $I_0(T)$, decreasing 
          $V_{{oc}}$ at **{base_module.beta_voc:.3f} V/°C**.
        - **Optimal Operating Knee:** The theoretical Maximum Power Point occurs at 
          $V_{{mpp}} = \\mathbf{{{mpp.v_mpp:.2f}\\text{{ V}}}}$ and $I_{{mpp}} = \\mathbf{{{mpp.i_mpp:.2f}\\text{{ A}}}}$, 
          yielding $P_{{mpp}} = \\mathbf{{{mpp.p_mpp:.1f}\\text{{ W}}}}$. The MPPT controller modulates 
          boost converter duty cycle $D$ to match this voltage dynamically.
        """
    )

with exp_col2:
    st.markdown("#### Data Export")
    df_curves = pd.DataFrame({
        "voltage_v": v_vec,
        "current_a": i_vec,
        "power_w": p_vec,
    })
    csv_bytes = generate_csv_download(df_curves, "pv_characteristic_curves.csv")
    st.download_button(
        label="Download I-V / P-V Data (CSV)",
        data=csv_bytes,
        file_name=f"pv_curves_G{int(irradiance)}_T{int(temperature_c)}.csv",
        mime="text/csv",
    )
    st.caption("Sampled 150 points across [0, Voc].")
