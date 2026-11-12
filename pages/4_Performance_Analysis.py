"""
Page 4: Deep-Dive Performance Analysis & Project Report Generation
In-depth electrical loss analysis, impedance matching dynamics, 3D Fuzzy control surfaces,
and automated academic simulation report export.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.config import PRESET_MODULES, PVArrayConfig, BoostConverterParams, SimulationConfig
from src.pv_model import SingleDiodePVModel
from src.boost_converter import BoostConverterModel
from src.fuzzy_controller import FuzzyMPPTController
from src.po_controller import POController
from src.environmental_profiles import EnvironmentalProfile
from src.simulation_engine import SimulationEngine
from src.metrics import compute_metrics, compare_controllers
from src.visualization import (
    plot_fuzzy_membership_functions,
    plot_fuzzy_control_surface,
    LAYOUT_COMMON,
)
from src.ui_helpers import (
    apply_custom_styles,
    render_header,
    render_metric_card,
    generate_markdown_report,
)

st.set_page_config(
    page_title="Performance Analysis | Solar MPPT",
    page_icon="🔬",
    layout="wide",
)

apply_custom_styles()

render_header(
    title="In-Depth Performance & Loss Analysis",
    subtitle="Semiconductor Loss Breakdown, Dynamic Impedance Matching, 3D Control Surface & Academic Report",
    badge="Advanced Electrical & Control Systems Engineering",
)

# Tabs for structured analysis
tab_losses, tab_impedance, tab_surface, tab_report = st.tabs([
    "⚡ Power & Energy Loss Analysis",
    "🔌 Dynamic Impedance Matching",
    "🧠 Fuzzy 3D Decision Surface",
    "📑 Download Academic Project Report",
])

with tab_losses:
    st.markdown("### 📉 Instantaneous & Cumulative Power Loss Analysis")
    st.write(
        """
        Energy extraction loss occurs whenever the instantaneous PV operating voltage $V_{pv}(t)$ 
        deviates from the theoretical maximum power point voltage $V_{mpp}^*(t)$.
        $$\\Delta P_{loss}(t) = P_{mpp}^*(t) - P_{pv}(t) \\ge 0$$
        $$E_{loss} = \\int_0^T \\Delta P_{loss}(t) dt$$
        """
    )

    # Run quick benchmark simulation for loss plotting
    base_module = PRESET_MODULES["Canadian Solar CS5P-220M"]
    pv_model = SingleDiodePVModel(PVArrayConfig(module_params=base_module))
    converter = BoostConverterModel(pv_model)
    profile = EnvironmentalProfile.scenario_b_irradiance_drop(t_step=0.25, g1=1000.0, g2=600.0)
    engine = SimulationEngine(pv_model, converter, profile, SimulationConfig(duration=0.5, time_step=5e-5))

    df_fuzzy = engine.run(FuzzyMPPTController(), controller_sampling_time=0.005, downsample_factor=2)
    df_po = engine.run(POController(), controller_sampling_time=0.005, downsample_factor=2)

    t = df_fuzzy["time"]
    loss_f = np.maximum(0.0, df_fuzzy["p_mpp_ref"] - df_fuzzy["p_pv"])
    loss_p = np.maximum(0.0, df_po["p_mpp_ref"] - df_po["p_pv"])

    # Trapezoid integration for cumulative energy loss (Joules)
    trapz_fn = getattr(np, "trapezoid", getattr(np, "trapz", None))
    cum_loss_f = np.array([trapz_fn(loss_f.iloc[:i+1], t.iloc[:i+1]) for i in range(len(t))]) / 3600.0
    cum_loss_p = np.array([trapz_fn(loss_p.iloc[:i+1], t.iloc[:i+1]) for i in range(len(t))]) / 3600.0

    fig_loss = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Instantaneous Tracking Power Loss (W)", "Cumulative Energy Loss (Wh)"),
        horizontal_spacing=0.10,
    )

    # 1. Instantaneous
    fig_loss.add_trace(
        go.Scatter(x=t, y=loss_f, mode="lines", name="Fuzzy Loss", line=dict(color="#10B981", width=2.0)),
        row=1, col=1
    )
    fig_loss.add_trace(
        go.Scatter(x=t, y=loss_p, mode="lines", name="P&O Loss", line=dict(color="#EF4444", width=1.8)),
        row=1, col=1
    )

    # 2. Cumulative
    fig_loss.add_trace(
        go.Scatter(x=t, y=cum_loss_f, mode="lines", name="Fuzzy Cum Loss", line=dict(color="#10B981", width=2.0)),
        row=1, col=2
    )
    fig_loss.add_trace(
        go.Scatter(x=t, y=cum_loss_p, mode="lines", name="P&O Cum Loss", line=dict(color="#EF4444", width=1.8)),
        row=1, col=2
    )

    fig_loss.update_xaxes(title_text="Time (s)", gridcolor="#E2E8F0")
    fig_loss.update_yaxes(title_text="Loss (W)", gridcolor="#E2E8F0", row=1, col=1)
    fig_loss.update_yaxes(title_text="Energy Loss (Wh)", gridcolor="#E2E8F0", row=1, col=2)
    fig_loss.update_layout(
        **LAYOUT_COMMON,
        title_text="Loss Comparison under Sudden Irradiance Step (1000 W/m² → 600 W/m² at t=0.25s)",
        height=400,
    )
    st.plotly_chart(fig_loss, use_container_width=True)

with tab_impedance:
    st.markdown("### 🔌 Dynamic Impedance Matching in DC-DC Boost Converters")
    st.write(
        """
        By Jacobi's Maximum Power Transfer Theorem, maximum electrical power transfer occurs 
        when the load impedance matches the internal source impedance:
        $$R_{opt} = R_{mpp} = \\frac{V_{mpp}}{I_{mpp}}$$
        
        For an ideal continuous-conduction boost converter connected to load $R_{load}$:
        $$R_{in}(D) = (1 - D)^2 R_{load}$$
        
        The controller operates by varying duty cycle $D$ such that:
        $$D_{mpp} = 1 - \\sqrt{\\frac{R_{mpp}}{R_{load}}}$$
        """
    )

    # Plot Rin vs Duty cycle
    r_load_val = 30.0
    d_vals = np.linspace(0.05, 0.90, 200)
    r_in_vals = ((1.0 - d_vals) ** 2.0) * r_load_val

    # Canadian Solar CS5P-220M Rmpp at STC = 48.3V / 4.55A = 10.62 Ohm
    r_mpp_stc = 48.3 / 4.55
    d_opt_stc = 1.0 - np.sqrt(r_mpp_stc / r_load_val)

    fig_imp = go.Figure()
    fig_imp.add_trace(
        go.Scatter(
            x=d_vals,
            y=r_in_vals,
            mode="lines",
            name="Converter Input Impedance R_in(D)",
            line=dict(color="#2563EB", width=2.5),
        )
    )
    fig_imp.add_hline(
        y=r_mpp_stc,
        line_dash="dash",
        line_color="#DC2626",
        annotation_text=f"Optimal PV Impedance R_mpp = {r_mpp_stc:.2f} Ω",
        annotation_position="top right",
    )
    fig_imp.add_vline(
        x=d_opt_stc,
        line_dash="dot",
        line_color="#10B981",
        annotation_text=f"Optimal Duty Cycle D* ≈ {d_opt_stc:.3f}",
        annotation_position="bottom right",
    )

    fig_imp.update_xaxes(title_text="Boost Converter Duty Cycle (D)", gridcolor="#E2E8F0")
    fig_imp.update_yaxes(title_text="Input Impedance Seen by PV (Ω)", gridcolor="#E2E8F0")
    fig_imp.update_layout(
        **LAYOUT_COMMON,
        title_text=f"Converter Impedance Characteristic (R_load = {r_load_val} Ω)",
        height=420,
    )
    st.plotly_chart(fig_imp, use_container_width=True)

with tab_surface:
    st.markdown("### 🧠 Fuzzy Logic Controller Internal Structure")
    st.write(
        """
        The 2-input, 1-output Mamdani Fuzzy Inference System evaluates Error ($E = dP/dV$) 
        and Change in Error ($CE = E(k) - E(k-1)$) using 5 linguistic terms each:
        - **NB:** Negative Big
        - **NS:** Negative Small
        - **ZE:** Zero
        - **PS:** Positive Small
        - **PB:** Positive Big
        """
    )

    # 1. Membership functions plot
    st.markdown("#### Linguistic Membership Functions (Triangular / Trapezoidal)")
    fig_mf = plot_fuzzy_membership_functions()
    st.plotly_chart(fig_mf, use_container_width=True)

    # 2. 3D Decision Surface
    st.markdown("#### 3D Mamdani Control Surface (ΔD as a function of E and CE)")
    fig_surf = plot_fuzzy_control_surface()
    st.plotly_chart(fig_surf, use_container_width=True)

with tab_report:
    st.markdown("### 📑 Generate & Download Project Report")
    st.write(
        """
        Download a complete, auto-generated academic technical report containing all mathematical 
        models, simulation configurations, verified tracking metrics, comparison tables, and 
        engineering conclusions. Suitable for academic submission and final-year evaluation.
        """
    )

    # Calculate real report data
    metrics_f = compute_metrics(df_fuzzy)
    metrics_p = compute_metrics(df_po)
    comp_df = compare_controllers(metrics_f, metrics_p)

    sim_info = {
        "module_name": base_module.name,
        "duration": 0.5,
        "time_step": 5e-5,
        "sampling_time": 0.005,
        "n_series": 1,
        "n_parallel": 1,
        "profile_name": "Scenario B: Sudden Irradiance Drop (1000 -> 600 W/m²)",
    }

    metrics_dict = {
        "fuzzy_efficiency": f"{metrics_f.tracking_efficiency_energy:.2f} %",
        "po_efficiency": f"{metrics_p.tracking_efficiency_energy:.2f} %",
        "fuzzy_settling": f"{metrics_f.settling_time_s*1000.0:.1f} ms" if metrics_f.settling_time_s else "N/A",
        "po_settling": "Continuous 3-point limit cycle",
        "fuzzy_ripple": f"{metrics_f.oscillation_amplitude_w:.3f} W",
        "po_ripple": f"{metrics_p.oscillation_amplitude_w:.3f} W",
    }

    report_content = generate_markdown_report(sim_info, metrics_dict, comp_df)

    # Download button
    st.download_button(
        label="📥 Download Full Academic Report (Markdown / Project Document)",
        data=report_content.encode("utf-8"),
        file_name="Fuzzy_Logic_Solar_MPPT_Academic_Report.md",
        mime="text/markdown",
        use_container_width=True,
    )

    with st.expander("👁️ Preview Generated Academic Report"):
        st.markdown(report_content)
