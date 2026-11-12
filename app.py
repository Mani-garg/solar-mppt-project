"""
Fuzzy Logic-Based MPPT Controller for Solar PV Systems
Main Application & Project Overview Dashboard.
"""

import streamlit as st
import numpy as np

from src.config import PRESET_MODULES, BoostConverterParams
from src.pv_model import SingleDiodePVModel
from src.ui_helpers import apply_custom_styles, render_header, render_metric_card

st.set_page_config(
    page_title="Solar MPPT Simulator | Fuzzy Logic vs P&O",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_styles()

render_header(
    title="Fuzzy Logic-Based MPPT Controller for Solar PV Systems",
    subtitle="Intelligent Renewable Energy Control & Electrical Engineering Simulation Platform",
    badge="B.Tech Electrical Engineering Final-Year Project Demonstration",
)

# Sidebar System Specs
with st.sidebar:
    st.subheader("⚡ System Quick Reference")
    st.markdown("""
    **Reference Module:**  
    Canadian Solar CS5P-220M
    - **P_mp:** 220.0 W
    - **V_mp:** 48.3 V
    - **I_mp:** 4.55 A
    - **V_oc:** 59.2 V
    - **I_sc:** 5.09 A
    
    ---
    **Converter Type:**  
    Averaged CCM Boost Converter
    - **Inductance L:** 2.5 mH
    - **PV Capacitor C_pv:** 220 µF
    - **Output Capacitor C_out:** 470 µF
    - **Load Resistor R_load:** 30.0 Ω
    
    ---
    **Controllers:**  
    - 5x5 Mamdani Fuzzy Logic Controller
    - Perturb & Observe (P&O) Benchmark
    """)

# Introduction & Core Principle
col1, col2 = st.columns([3, 2])

with col1:
    st.markdown("### 🎯 Project Overview & Engineering Motivation")
    st.write(
        """
        Photovoltaic (PV) power systems exhibit a distinctly non-linear current-voltage ($I-V$) 
        and power-voltage ($P-V$) characteristic. Under any given environmental condition of 
        solar irradiance ($G$) and cell temperature ($T$), there exists a unique operating point 
        where the solar array produces its theoretical maximum electrical power, known as the 
        **Maximum Power Point (MPP)**.
        
        Because solar irradiance and cell temperature fluctuate dynamically throughout the day 
        due to cloud cover, passing shadows, and thermal ambient shifts, a fixed operating point 
        results in severe energy losses. A **Maximum Power Point Tracking (MPPT)** controller 
        continuously senses the panel electrical voltage and current, dynamically modulating the 
        pulse-width duty cycle ($D$) of a DC-DC boost converter to impedance-match the PV array 
        to its load ($R_{in} = (1-D)^2 R_{load}$), driving the PV panel to operate precisely at $dP/dV = 0$.
        """
    )
    
    st.markdown("#### 🚀 Why Fuzzy Logic MPPT?")
    st.write(
        """
        Conventional **Perturb & Observe (P&O)** algorithms rely on a fixed step size $\\Delta D$, 
        introducing an inherent engineering dilemma:
        - **Large step size:** Fast tracking during transients, but large limit-cycle oscillations around MPP at steady state, wasting power.
        - **Small step size:** Reduced steady-state ripple, but sluggish response to sudden irradiance changes, causing dynamic tracking drift.
        
        The **Fuzzy Logic Controller (FLC)** eliminates this trade-off through non-linear linguistic 
        reasoning. By calculating both Error ($E = dP/dV$) and Change in Error ($CE$), the controller 
        applies aggressive duty steps ($PB/NB$) when far from MPP, and micro-fine adjustments ($PS/NS/ZE$) 
        near the peak, achieving rapid settling without steady-state power oscillations.
        """
    )

with col2:
    st.markdown("### 📐 System Block Diagram")
    
    # SVG-based clean electrical system block diagram
    diagram_svg = """
    <svg viewBox="0 0 540 310" xmlns="http://www.w3.org/2000/svg" style="width:100%; height:auto; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px; padding:10px;">
        <!-- PV Array -->
        <rect x="20" y="30" width="110" height="90" rx="8" fill="#EFF6FF" stroke="#3B82F6" stroke-width="2"/>
        <text x="75" y="65" font-family="Segoe UI, sans-serif" font-size="12" font-weight="bold" fill="#1E3A8A" text-anchor="middle">Solar PV Array</text>
        <text x="75" y="85" font-family="Segoe UI, sans-serif" font-size="10" fill="#3B82F6" text-anchor="middle">Single-Diode Model</text>
        <text x="75" y="102" font-family="Segoe UI, sans-serif" font-size="9" fill="#64748B" text-anchor="middle">G (W/m²), T (°C)</text>

        <!-- Connecting Wire 1 -->
        <line x1="130" y1="75" x2="190" y2="75" stroke="#0F172A" stroke-width="2.5" marker-end="url(#arrow)"/>
        <text x="160" y="65" font-family="Segoe UI, sans-serif" font-size="10" fill="#0F172A" font-weight="bold" text-anchor="middle">V_pv, I_pv</text>

        <!-- Boost Converter -->
        <rect x="190" y="30" width="160" height="90" rx="8" fill="#ECFDF5" stroke="#10B981" stroke-width="2"/>
        <text x="270" y="60" font-family="Segoe UI, sans-serif" font-size="12" font-weight="bold" fill="#065F46" text-anchor="middle">DC-DC Boost Converter</text>
        <text x="270" y="78" font-family="Segoe UI, sans-serif" font-size="10" fill="#059669" text-anchor="middle">L=2.5mH, C=470µF</text>
        <text x="270" y="95" font-family="Segoe UI, sans-serif" font-size="9" fill="#047857" text-anchor="middle">R_in = (1-D)² R_load</text>

        <!-- Connecting Wire 2 -->
        <line x1="350" y1="75" x2="410" y2="75" stroke="#0F172A" stroke-width="2.5"/>
        <text x="380" y="65" font-family="Segoe UI, sans-serif" font-size="10" fill="#0F172A" font-weight="bold" text-anchor="middle">V_out</text>

        <!-- DC Load -->
        <rect x="410" y="30" width="105" height="90" rx="8" fill="#F8FAFC" stroke="#64748B" stroke-width="2"/>
        <text x="462" y="68" font-family="Segoe UI, sans-serif" font-size="12" font-weight="bold" fill="#334155" text-anchor="middle">Resistive Load</text>
        <text x="462" y="88" font-family="Segoe UI, sans-serif" font-size="10" fill="#64748B" text-anchor="middle">R_load = 30 Ω</text>

        <!-- Feedback Senses to Controller -->
        <line x1="160" y1="75" x2="160" y2="200" stroke="#64748B" stroke-width="1.8" stroke-dasharray="4,4"/>
        <line x1="160" y1="200" x2="200" y2="200" stroke="#64748B" stroke-width="1.8" stroke-dasharray="4,4"/>

        <!-- MPPT Controller Box -->
        <rect x="200" y="160" width="140" height="85" rx="8" fill="#FFFBEB" stroke="#F59E0B" stroke-width="2"/>
        <text x="270" y="190" font-family="Segoe UI, sans-serif" font-size="12" font-weight="bold" fill="#92400E" text-anchor="middle">MPPT Controller</text>
        <text x="270" y="208" font-family="Segoe UI, sans-serif" font-size="10" fill="#B45309" text-anchor="middle">Fuzzy Logic / P&O</text>
        <text x="270" y="225" font-family="Segoe UI, sans-serif" font-size="9" fill="#78350F" text-anchor="middle">E = dP/dV, CE</text>

        <!-- Duty Cycle Control Line -->
        <line x1="270" y1="160" x2="270" y2="120" stroke="#DC2626" stroke-width="2.2" marker-end="url(#arrow-red)"/>
        <text x="290" y="145" font-family="Segoe UI, sans-serif" font-size="11" font-weight="bold" fill="#DC2626">Duty (D)</text>
    </svg>
    """
    st.markdown(diagram_svg, unsafe_allow_html=True)
    st.caption("Coupled Electro-Mechanical Closed-Loop MPPT System Architecture")

st.markdown("---")

# Key STC Reference Metrics Grid
st.markdown("### 📊 STC Standard Test Reference Specifications (1000 W/m², 25°C)")
m_cols = st.columns(5)
with m_cols[0]:
    render_metric_card("Rated Max Power (Pmp)", "220.0 W", "Reference module rating")
with m_cols[1]:
    render_metric_card("MPP Voltage (Vmp)", "48.3 V", "Nominal optimum voltage")
with m_cols[2]:
    render_metric_card("MPP Current (Imp)", "4.55 A", "Nominal optimum current")
with m_cols[3]:
    render_metric_card("Open-Circuit (Voc)", "59.2 V", "At zero load current")
with m_cols[4]:
    render_metric_card("Short-Circuit (Isc)", "5.09 A", "At zero terminal voltage")

st.markdown("---")

# Navigation Section
st.markdown("### 🧭 Platform Navigation")
p_cols = st.columns(5)

with p_cols[0]:
    st.markdown("""
    #### 1. PV Panel Simulator
    Explore the single-diode physical model, adjust irradiance and temperature sliders, and inspect real-time I-V and P-V characteristic curves.
    """)
    if st.button("Open PV Simulator →"):
        st.switch_page("pages/1_PV_Panel_Simulator.py")

with p_cols[1]:
    st.markdown("""
    #### 2. MPPT Simulation
    Run discrete-continuous time-domain simulations with Fuzzy Logic or P&O under dynamic environmental scenarios.
    """)
    if st.button("Launch Simulation →"):
        st.switch_page("pages/2_MPPT_Simulation.py")

with p_cols[2]:
    st.markdown("""
    #### 3. Controller Comparison
    Direct side-by-side benchmark comparing Fuzzy Logic MPPT vs P&O under identical conditions with tracking efficiency & ripple analysis.
    """)
    if st.button("Compare Controllers →"):
        st.switch_page("pages/3_Controller_Comparison.py")

with p_cols[3]:
    st.markdown("""
    #### 4. Performance Analysis
    In-depth electrical analysis, 3D Fuzzy decision surfaces, power loss distributions, and automated project report generation.
    """)
    if st.button("View Analysis →"):
        st.switch_page("pages/4_Performance_Analysis.py")

with p_cols[4]:
    st.markdown("""
    #### 5. Documentation
    Full academic report with mathematical derivations, single-diode equations, Mamdani rule base, and boost converter physics.
    """)
    if st.button("Read Docs →"):
        st.switch_page("pages/5_Documentation.py")
