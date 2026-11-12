"""
UI Helpers, Custom Engineering CSS, and Data Export Utilities for Streamlit Application.
Provides authentic academic/engineering styling, telemetry cards, and report generators.
"""

import json
import textwrap
from typing import Dict, Any, Optional
import pandas as pd
import streamlit as st

ENGINEERING_CSS = """
<style>
    /* Technical & Monospace Typography */
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #0F172A;
    }
    
    /* Institutional Page Canvas */
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* Engineering Lab Header Bar */
    .lab-header {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-left: 5px solid #1E3A8A;
        border-radius: 4px;
        padding: 1.25rem 1.75rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    .lab-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #E2E8F0;
        padding-bottom: 0.5rem;
        margin-bottom: 0.75rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .lab-meta .status-pill {
        background: #ECFDF5;
        color: #065F46;
        border: 1px solid #A7F3D0;
        padding: 0.15rem 0.5rem;
        border-radius: 3px;
        font-weight: 600;
    }
    .lab-title {
        color: #0F172A;
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        margin: 0;
        line-height: 1.25;
    }
    .lab-subtitle {
        color: #334155;
        font-size: 0.9rem;
        margin-top: 0.35rem;
        margin-bottom: 0;
    }
    
    /* Telemetry Digital Readout Panel */
    .telemetry-card {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 4px;
        padding: 0.85rem 1rem;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
        position: relative;
    }
    .telemetry-card:hover {
        border-color: #94A3B8;
    }
    .telemetry-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.25rem;
    }
    .telemetry-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.45rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }
    .telemetry-sub {
        font-size: 0.75rem;
        color: #475569;
        margin-top: 0.3rem;
        font-family: 'IBM Plex Sans', sans-serif;
    }
    
    /* Clean Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #CBD5E1;
    }
    
    /* Buttons - Lab Instrument Style */
    .stButton>button {
        background-color: #1E3A8A;
        color: #FFFFFF;
        font-family: 'IBM Plex Sans', sans-serif;
        font-weight: 600;
        font-size: 0.85rem;
        border: 1px solid #1E3A8A;
        border-radius: 4px;
        padding: 0.45rem 1.1rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        transition: all 0.15s ease;
    }
    .stButton>button:hover {
        background-color: #1D4ED8;
        border-color: #1D4ED8;
        color: #FFFFFF;
    }
    
    /* Technical Data Tables */
    .dataframe {
        border: 1px solid #CBD5E1 !important;
        border-radius: 4px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.82rem !important;
    }
    
    /* Expander Panels */
    .streamlit-expanderHeader {
        font-family: 'IBM Plex Sans', sans-serif;
        font-weight: 600;
        font-size: 0.88rem;
        color: #334155;
    }
</style>
"""


def apply_custom_styles() -> None:
    """Inject engineering stylesheet into the Streamlit session."""
    st.markdown(ENGINEERING_CSS, unsafe_allow_html=True)


def render_header(
    title: str,
    subtitle: str,
    badge: str = "B.Tech Final-Year Project | Electrical Engineering",
    system_status: Optional[str] = None,
) -> None:
    """Render clean institutional laboratory header without Markdown indentation conflicts."""
    status_html = f'<span class="status-pill">{system_status}</span>' if system_status else ""
    html = (
        f'<div class="lab-header">'
        f'<div class="lab-meta"><span>{badge}</span>{status_html}</div>'
        f'<div class="lab-title">{title}</div>'
        f'<div class="lab-subtitle">{subtitle}</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_metric_card(title: str, value: str, sub: str = "") -> None:
    """Render technical digital readout card without Markdown indentation conflicts."""
    sub_html = f'<div class="telemetry-sub">{sub}</div>' if sub else ""
    html = (
        f'<div class="telemetry-card">'
        f'<div class="telemetry-label">{title}</div>'
        f'<div class="telemetry-val">{value}</div>'
        f'{sub_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def generate_csv_download(df: pd.DataFrame, filename: str = "simulation_data.csv") -> bytes:
    """Serialize DataFrame to downloadable CSV format."""
    return df.to_csv(index=False).encode("utf-8")


def generate_json_download(data: Dict[str, Any], filename: str = "simulation_metadata.json") -> str:
    """Serialize metadata dictionary to formatted JSON string."""
    return json.dumps(data, indent=2)


def df_to_markdown_table(df: pd.DataFrame) -> str:
    """Format DataFrame as an academic Markdown table without requiring external tabulate dependency."""
    headers = [str(c) for c in df.columns]
    header_line = "| " + " | ".join(headers) + " |"
    sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    row_lines = []
    for _, row in df.iterrows():
        row_str = "| " + " | ".join(str(val) for val in row) + " |"
        row_lines.append(row_str)
    return "\n".join([header_line, sep_line] + row_lines)


def generate_markdown_report(
    sim_settings: Dict[str, Any],
    metrics_summary: Dict[str, Any],
    comparison_df: Optional[pd.DataFrame] = None,
) -> str:
    """Generate technical academic simulation report in standard engineering format."""
    report = f"""# Maximum Power Point Tracking (MPPT) Simulation Report
**Investigation:** Discrete-Continuous Simulation of Fuzzy Logic and P&O Controllers for Solar PV Systems  
**Laboratory:** Power Electronics & Renewable Energy Systems  
**Reference Module:** {sim_settings.get("module_name", "Canadian Solar CS5P-220M")}  
**Model Formulation:** 5-Parameter Single-Diode Model solved via Lambert W function  

---

## 1. Operating Parameters & Setup
- **Simulation Duration:** {sim_settings.get("duration", 0.5):.2f} s
- **Numerical Solver Time Step (dt):** {sim_settings.get("time_step", 5e-5):.1e} s (Classical 4th-Order Runge-Kutta)
- **Digital Controller Sampling Period (Ts):** {sim_settings.get("sampling_time", 0.005) * 1000.0:.1f} ms (fs = {1.0/sim_settings.get("sampling_time", 0.005):.0f} Hz)
- **Photovoltaic Array Dimension:** {sim_settings.get("n_series", 1)} Series Module(s) x {sim_settings.get("n_parallel", 1)} Parallel String(s)
- **Environmental Disturbance Profile:** {sim_settings.get("profile_name", "Scenario B: Sudden Irradiance Drop")}

---

## 2. Experimental Telemetry & Figures of Merit
- **Fuzzy Logic MPPT Energy Tracking Factor (η_MPPT):** {metrics_summary.get("fuzzy_efficiency", "N/A")}
- **Perturb & Observe Baseline Efficiency (η_MPPT):** {metrics_summary.get("po_efficiency", "N/A")}
- **Fuzzy Dynamic Settling Time (ts, ±2% criterion):** {metrics_summary.get("fuzzy_settling", "N/A")}
- **Perturb & Observe Settling Behavior:** {metrics_summary.get("po_settling", "N/A")}
- **Steady-State Power Ripple Amplitude (ΔP):** Fuzzy: {metrics_summary.get("fuzzy_ripple", "N/A")} | P&O: {metrics_summary.get("po_ripple", "N/A")}

---

## 3. Side-by-Side Performance Matrix
"""
    if comparison_df is not None:
        report += "\n" + df_to_markdown_table(comparison_df) + "\n\n"

    report += """
---

## 4. Technical Analysis & Observations
1. **Steady-State Limit Cycle Suppression:** The Mamdani Fuzzy Inference System automatically reduces the duty cycle perturbation magnitude as the operating point enters the vicinity of $dP/dV = 0$. This eliminates the persistent 3-point limit-cycle oscillation characteristic of conventional fixed-step P&O.
2. **Transient Tracking Agility:** During abrupt solar irradiance transients, the normalized error derivative $E = dP/dV$ activates the outer linguistic membership functions ($PB$ or $NB$), applying larger duty cycle increments to rapidly adjust converter input impedance ($R_{in} = (1-D)^2 R_{load}$).
3. **Total Conversion Energy:** Reduction in steady-state power ripple combined with rapid transition settling produces a higher net energy yield ($Wh$) over dynamic operating schedules.

---
*Generated by the Solar MPPT Numerical Simulation Engine.*
"""
    return report
