"""
Fuzzy Logic-Based MPPT Controller for Solar Photovoltaic Systems
Main Dashboard & Control Architecture Overview.
"""

import streamlit as st
import streamlit.components.v1 as components
import numpy as np

from src.config import PRESET_MODULES, BoostConverterParams
from src.pv_model import SingleDiodePVModel
from src.ui_helpers import apply_custom_styles, render_header, render_metric_card

st.set_page_config(
    page_title="PV MPPT Simulation Suite | Control Engineering Lab",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_styles()

render_header(
    title="Photovoltaic Maximum Power Point Tracking (MPPT) Simulation Suite",
    subtitle="Discrete-Continuous Hybrid Simulation of Fuzzy Logic and Conventional P&O Algorithms",
    badge="Department of Electrical Engineering | Power Electronics & Renewable Energy Systems",
    system_status="Solver: Lambert-W (Exact) | Core Online",
)

# Sidebar System Specs
with st.sidebar:
    st.markdown("### Active Module Specification")
    st.markdown("""
    **Module:** Canadian Solar CS5P-220M  
    **Cell Type:** Monocrystalline (96 in series)
    
    | Parameter | Value | Unit |
    |:---|---:|:---:|
    | Nominal Power $P_{mp}$ | 220.0 | W |
    | Voltage at MPP $V_{mp}$ | 48.3 | V |
    | Current at MPP $I_{mp}$ | 4.55 | A |
    | Open-Circuit $V_{oc}$ | 59.2 | V |
    | Short-Circuit $I_{sc}$ | 5.09 | A |
    | Temp. Coeff. $\\alpha_{sc}$ | +0.065 | %/K |
    | Temp. Coeff. $\\beta_{voc}$ | -0.334 | %/K |
    """)

    st.markdown("---")
    st.markdown("### Converter Component Ratings")
    st.markdown("""
    **Topology:** Averaged CCM Boost Converter  
    - **Inductor $L$:** $2.5\\text{ mH}$ ($r_L = 0.05\\ \\Omega$)
    - **Filter Cap $C_{pv}$:** $220\\ \\mu\\text{F}$
    - **DC-Link Cap $C_{out}$:** $470\\ \\mu\\text{F}$
    - **DC Load $R_{load}$:** $30.0\\ \\Omega$
    - **Switching Range $D$:** $0.05 - 0.90$
    - **Sampling Rate $f_s$:** $200\\text{ Hz}$ ($T_s = 5\\text{ ms}$)
    - **ODE Time Step $\\Delta t$:** $50\\ \\mu\\text{s}$ (RK4)
    """)

# Section 1 & Section 2
col1, col2 = st.columns([13, 11])

with col1:
    st.markdown("### 1. System Overview & Problem Formulation")
    st.write(
        """
        Photovoltaic (PV) cells exhibit an inherently non-linear current-voltage (**I-V**) 
        relationship governed by semiconductor p-n junction physics. Under varying ambient 
        irradiance ($G$) and junction temperature ($T$), there exists a unique operating point 
        where the extracted power reaches its global optimum: the **Maximum Power Point (MPP)**.
        
        Because solar irradiance and operating temperatures vary dynamically due to cloud transients 
        and ambient atmospheric shifts, direct connection between the PV array and a static electrical 
        load results in severe impedance mismatch and lost generation capacity. Maximum Power Point 
        Tracking (MPPT) solves this by dynamically modulating the switching duty cycle ($D$) of an 
        interfacing DC-DC boost converter:
        $$R_{in}(D) = (1 - D)^2 R_{load}$$
        
        The controller continually shifts $R_{in}$ to equal the internal dynamic source impedance 
        $R_{mpp} = V_{mpp} / I_{mpp}$, ensuring operation at the maximum power derivative condition:
        $$\\frac{dP}{dV} = 0$$
        """
    )
    
    st.markdown("### 2. Adaptive Fuzzy Control vs. Fixed-Step P&O")
    st.write(
        """
        conventional **Perturb and Observe (P&O)** algorithms rely on a static perturbation step 
        ($\\Delta D$), creating an unavoidable design trade-off:
        - **Large $\\Delta D$:** Rapid dynamic tracking during irradiance steps, but severe steady-state limit-cycle power ripple ($\\Delta P_{p-p}$), causing continuous energy loss.
        - **Small $\\Delta D$:** Lower steady-state ripple, but sluggish transient response and vulnerability to tracking divergence during rapid cloud shadows.
        
        The **Mamdani Fuzzy Logic Controller (FLC)** eliminates this compromise through non-linear 
        linguistic mapping. By observing both normalized Error ($E = dP/dV$) and Change in Error ($CE$), 
        the controller applies aggressive duty adjustments ($PB/NB$) when far from the MPP, and 
        dynamically throttles down to minute increments ($PS/NS/ZE$) near the peak, achieving rapid 
        settling with near-zero steady-state limit-cycle oscillation.
        """
    )

with col2:
    st.markdown("### Circuit Schematic & Control Architecture")
    
    # Authentic electrical engineering schematic diagram
    schematic_html = """
    <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:4px; padding:12px; box-sizing:border-box;">
        <svg viewBox="0 0 540 320" xmlns="http://www.w3.org/2000/svg" style="width:100%; height:auto; display:block; font-family:'IBM Plex Sans', sans-serif;">
            <defs>
                <marker id="sch-arrow" viewBox="0 0 8 8" refX="5" refY="4" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                    <path d="M 0 1 L 7 4 L 0 7 z" fill="#1E293B"/>
                </marker>
                <marker id="ctrl-arrow" viewBox="0 0 8 8" refX="5" refY="4" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                    <path d="M 0 1 L 7 4 L 0 7 z" fill="#B91C1C"/>
                </marker>
            </defs>

            <!-- Background Grid Pattern -->
            <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#F1F5F9" stroke-width="1"/>
            </pattern>
            <rect width="540" height="320" fill="url(#grid)" />

            <!-- Power Rails Top and Bottom -->
            <!-- Top Rail -->
            <line x1="80" y1="50" x2="440" y2="50" stroke="#0F172A" stroke-width="2.5"/>
            <!-- Bottom Ground Rail -->
            <line x1="80" y1="170" x2="440" y2="170" stroke="#0F172A" stroke-width="2.5"/>
            <!-- Ground Symbol -->
            <line x1="260" y1="170" x2="260" y2="185" stroke="#0F172A" stroke-width="2"/>
            <line x1="250" y1="185" x2="270" y2="185" stroke="#0F172A" stroke-width="2"/>
            <line x1="254" y1="189" x2="266" y2="189" stroke="#0F172A" stroke-width="1.5"/>
            <line x1="258" y1="193" x2="262" y2="193" stroke="#0F172A" stroke-width="1"/>

            <!-- PV Generator Block -->
            <rect x="25" y="45" width="55" height="130" rx="3" fill="#F8FAFC" stroke="#0F172A" stroke-width="1.8"/>
            <circle cx="52" cy="90" r="16" fill="#EFF6FF" stroke="#2563EB" stroke-width="1.5"/>
            <line x1="52" y1="80" x2="52" y2="100" stroke="#2563EB" stroke-width="2"/>
            <line x1="42" y1="90" x2="62" y2="90" stroke="#2563EB" stroke-width="2"/>
            <!-- Photon rays -->
            <line x1="30" y1="65" x2="42" y2="77" stroke="#D97706" stroke-width="1.5" marker-end="url(#sch-arrow)"/>
            <line x1="36" y1="60" x2="48" y2="72" stroke="#D97706" stroke-width="1.5" marker-end="url(#sch-arrow)"/>
            <text x="52" y="125" font-size="10" font-weight="600" fill="#0F172A" text-anchor="middle">PV ARRAY</text>
            <text x="52" y="140" font-size="8.5" fill="#475569" text-anchor="middle">CS5P-220M</text>
            <text x="52" y="153" font-size="8" fill="#64748B" text-anchor="middle">G, T</text>

            <!-- Input Cap C_pv -->
            <line x1="110" y1="50" x2="110" y2="100" stroke="#0F172A" stroke-width="1.5"/>
            <line x1="100" y1="100" x2="120" y2="100" stroke="#0F172A" stroke-width="2.5"/>
            <line x1="100" y1="108" x2="120" y2="108" stroke="#0F172A" stroke-width="2.5"/>
            <line x1="110" y1="108" x2="110" y2="170" stroke="#0F172A" stroke-width="1.5"/>
            <text x="126" y="107" font-size="9" font-weight="600" fill="#334155">C_pv</text>

            <!-- Current Sensor LEM -->
            <rect x="145" y="40" width="28" height="20" fill="#FFFFFF" stroke="#0F172A" stroke-width="1.5"/>
            <text x="159" y="54" font-size="8.5" font-weight="600" fill="#0F172A" text-anchor="middle">LEM</text>
            <text x="159" y="32" font-size="9" font-weight="600" fill="#2563EB" text-anchor="middle">I_pv</text>

            <!-- Boost Inductor L -->
            <!-- Coil arcs -->
            <path d="M 195 50 Q 205 32 215 50 Q 225 32 235 50 Q 245 32 255 50 Q 265 32 275 50" fill="none" stroke="#0F172A" stroke-width="2.5"/>
            <text x="235" y="28" font-size="9.5" font-weight="600" fill="#0F172A" text-anchor="middle">L = 2.5 mH</text>

            <!-- Switching Node & MOSFET Q1 -->
            <circle cx="285" cy="50" r="3" fill="#0F172A"/>
            <line x1="285" y1="50" x2="285" y2="85" stroke="#0F172A" stroke-width="2"/>
            <!-- MOSFET symbol -->
            <rect x="272" y="85" width="26" height="40" fill="#FFFFFF" stroke="#0F172A" stroke-width="1.5"/>
            <line x1="277" y1="92" x2="277" y2="118" stroke="#0F172A" stroke-width="2"/>
            <line x1="285" y1="92" x2="285" y2="118" stroke="#0F172A" stroke-width="2" stroke-dasharray="3,3"/>
            <text x="312" y="108" font-size="9" font-weight="600" fill="#0F172A">Q1</text>
            <line x1="285" y1="125" x2="285" y2="170" stroke="#0F172A" stroke-width="2"/>

            <!-- Fast Recovery Diode D1 -->
            <!-- Triangle and bar -->
            <polygon points="320,40 320,60 340,50" fill="#0F172A"/>
            <line x1="340" y1="40" x2="340" y2="60" stroke="#0F172A" stroke-width="2.5"/>
            <line x1="310" y1="50" x2="320" y2="50" stroke="#0F172A" stroke-width="2"/>
            <line x1="340" y1="50" x2="360" y2="50" stroke="#0F172A" stroke-width="2"/>
            <text x="330" y="32" font-size="9.5" font-weight="600" fill="#0F172A" text-anchor="middle">D1</text>

            <!-- Output Cap C_out -->
            <line x1="375" y1="50" x2="375" y2="100" stroke="#0F172A" stroke-width="1.5"/>
            <line x1="365" y1="100" x2="385" y2="100" stroke="#0F172A" stroke-width="2.5"/>
            <line x1="365" y1="108" x2="385" y2="108" stroke="#0F172A" stroke-width="2.5"/>
            <line x1="375" y1="108" x2="375" y2="170" stroke="#0F172A" stroke-width="1.5"/>
            <text x="392" y="107" font-size="9" font-weight="600" fill="#334155">C_o</text>

            <!-- Load Resistor R_L -->
            <path d="M 440 50 L 440 85 L 433 90 L 447 98 L 433 106 L 447 114 L 433 122 L 447 130 L 440 135 L 440 170" fill="none" stroke="#0F172A" stroke-width="2"/>
            <text x="462" y="112" font-size="9.5" font-weight="600" fill="#0F172A">R_load</text>
            <text x="462" y="125" font-size="8.5" fill="#64748B">30.0 Ω</text>
            <text x="415" y="42" font-size="9" font-weight="600" fill="#2563EB">V_out</text>

            <!-- Control Loop & Microcontroller Unit -->
            <rect x="130" y="215" width="280" height="90" rx="4" fill="#F8FAFC" stroke="#1E3A8A" stroke-width="1.8"/>
            <text x="145" y="235" font-size="10" font-weight="700" fill="#1E3A8A">DIGITAL SIGNAL CONTROLLER (DSP / MCU)</text>

            <!-- Microcontroller Sub-blocks -->
            <rect x="142" y="246" width="55" height="46" rx="2" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1"/>
            <text x="169" y="265" font-size="8.5" font-weight="600" fill="#334155" text-anchor="middle">12-bit ADC</text>
            <text x="169" y="278" font-size="7.5" fill="#64748B" text-anchor="middle">V_pv, I_pv</text>

            <rect x="207" y="246" width="125" height="46" rx="2" fill="#EFF6FF" stroke="#3B82F6" stroke-width="1"/>
            <text x="269" y="263" font-size="8.5" font-weight="600" fill="#1E3A8A" text-anchor="middle">MAMDANI FIS CORE</text>
            <text x="269" y="275" font-size="7.5" fill="#2563EB" text-anchor="middle">E = dP/dV, CE</text>
            <text x="269" y="286" font-size="7.5" fill="#475569" text-anchor="middle">5x5 Rule Base Matrix</text>

            <rect x="342" y="246" width="58" height="46" rx="2" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1"/>
            <text x="371" y="265" font-size="8.5" font-weight="600" fill="#334155" text-anchor="middle">PWM GEN</text>
            <text x="371" y="278" font-size="7.5" fill="#64748B" text-anchor="middle">20 kHz (D)</text>

            <!-- Connecting Sensing Lines -->
            <line x1="159" y1="60" x2="159" y2="246" stroke="#2563EB" stroke-width="1.2" stroke-dasharray="3,3" marker-end="url(#sch-arrow)"/>
            <line x1="105" y1="50" x2="105" y2="260" stroke="#2563EB" stroke-width="1.2" stroke-dasharray="3,3"/>
            <line x1="105" y1="260" x2="142" y2="260" stroke="#2563EB" stroke-width="1.2" stroke-dasharray="3,3" marker-end="url(#sch-arrow)"/>

            <!-- Gate Drive Command Line -->
            <line x1="371" y1="246" x2="371" y2="105" stroke="#B91C1C" stroke-width="1.5" stroke-dasharray="4,2"/>
            <line x1="371" y1="105" x2="298" y2="105" stroke="#B91C1C" stroke-width="1.5" stroke-dasharray="4,2" marker-end="url(#ctrl-arrow)"/>
            <text x="350" y="125" font-size="8.5" font-weight="600" fill="#B91C1C">Gate PWM (D)</text>
        </svg>
    </div>
    """
    components.html(schematic_html, height=340)
    st.caption("Figure 1: Complete Power Stage Schematic and Closed-Loop Control Architecture.")

st.markdown("---")

# Baseline Parameter Readouts
st.markdown("### Standard Test Conditions (STC) Baseline Specifications (1000 W/m², 25°C)")
m_cols = st.columns(5)
with m_cols[0]:
    render_metric_card("Rated Max Power (Pmp)", "220.00 W", "Reference STC output")
with m_cols[1]:
    render_metric_card("MPP Voltage (Vmp)", "48.30 V", "81.6% of Voc")
with m_cols[2]:
    render_metric_card("MPP Current (Imp)", "4.55 A", "89.4% of Isc")
with m_cols[3]:
    render_metric_card("Open-Circuit Voltage (Voc)", "59.20 V", "Zero terminal current")
with m_cols[4]:
    render_metric_card("Short-Circuit Current (Isc)", "5.09 A", "Zero terminal voltage")

st.markdown("---")

# Navigation Hub
st.markdown("### Simulation Modules & Subsystems")
p_cols = st.columns(5)

with p_cols[0]:
    st.markdown("""
    **Module 1: PV Characterization**  
    Analyze single-diode physics, variable irradiance/temperature response, and theoretical $I-V$ & $P-V$ curves.
    """)
    if st.button("Launch PV Simulator"):
        st.switch_page("pages/1_PV_Panel_Simulator.py")

with p_cols[1]:
    st.markdown("""
    **Module 2: MPPT Simulation**  
    Execute discrete-continuous closed-loop simulation under dynamic disturbance scenarios (cloud shadows, heating).
    """)
    if st.button("Launch Simulation"):
        st.switch_page("pages/2_MPPT_Simulation.py")

with p_cols[2]:
    st.markdown("""
    **Module 3: Benchmark Comparison**  
    Direct side-by-side performance evaluation: Fuzzy Logic MPPT vs. Classical P&O under identical conditions.
    """)
    if st.button("Open Comparison"):
        st.switch_page("pages/3_Controller_Comparison.py")

with p_cols[3]:
    st.markdown("""
    **Module 4: Performance Analysis**  
    Semiconductor loss breakdown, dynamic impedance matching ($R_{in}$ vs $D$), 3D Fuzzy surface, and report export.
    """)
    if st.button("Open Analysis"):
        st.switch_page("pages/4_Performance_Analysis.py")

with p_cols[4]:
    st.markdown("""
    **Module 5: Technical Documentation**  
    Complete mathematical derivations, Lambert-W formulation, Mamdani FIS design, and differential equations.
    """)
    if st.button("Read Documentation"):
        st.switch_page("pages/5_Documentation.py")
