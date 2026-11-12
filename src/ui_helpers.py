"""
UI Helpers, Custom CSS, and Data Export Utilities for Streamlit Application.
Provides styling and export capabilities (CSV, JSON, Markdown/HTML project report).
"""

import json
from typing import Dict, Any, Optional
import pandas as pd
import streamlit as st

CUSTOM_CSS = """
<style>
    /* Google Fonts & Base Typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #0F172A;
    }
    
    /* Main Content Background */
    .stApp {
        background-color: #FAFAFA;
    }
    
    /* Clean Top Header Card */
    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        color: #FFFFFF;
        padding: 1.8rem 2.2rem;
        border-radius: 12px;
        margin-bottom: 1.8rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    .main-header h1 {
        color: #FFFFFF;
        font-size: 1.85rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
        letter-spacing: -0.02em;
    }
    .main-header p {
        color: #94A3B8;
        font-size: 0.95rem;
        margin-bottom: 0px;
    }
    .main-header .badge {
        display: inline-block;
        background: #10B981;
        color: #FFFFFF;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.6rem;
    }
    
    /* Modern Metric Cards */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.1rem 1.3rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
    }
    .metric-title {
        color: #64748B;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.3rem;
    }
    .metric-value {
        color: #0F172A;
        font-size: 1.6rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .metric-sub {
        color: #10B981;
        font-size: 0.8rem;
        font-weight: 500;
        margin-top: 0.2rem;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #F8FAFC;
        border-right: 1px solid #E2E8F0;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #10B981;
        color: #FFFFFF;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.2rem;
        transition: background-color 0.15s ease;
    }
    .stButton>button:hover {
        background-color: #059669;
        color: #FFFFFF;
    }
    
    /* Table Styling */
    .dataframe {
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        font-size: 0.9rem !important;
    }
</style>
"""


def apply_custom_styles() -> None:
    """Inject custom CSS into the Streamlit session."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_header(
    title: str,
    subtitle: str,
    badge: str = "B.Tech Electrical Engineering Final-Year Project",
) -> None:
    """Render consistent modern top header."""
    html = f"""
    <div class="main-header">
        <div class="badge">{badge}</div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_metric_card(title: str, value: str, sub: str = "") -> None:
    """Render custom KPI card."""
    sub_html = f'<div class="metric-sub">{sub}</div>' if sub else ""
    html = f"""
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        {sub_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def generate_csv_download(df: pd.DataFrame, filename: str = "simulation_data.csv") -> bytes:
    """Serialize DataFrame to downloadable CSV format."""
    return df.to_csv(index=False).encode("utf-8")


def generate_json_download(data: Dict[str, Any], filename: str = "simulation_metadata.json") -> str:
    """Serialize metadata dictionary to formatted JSON string."""
    return json.dumps(data, indent=2)


def generate_markdown_report(
    sim_settings: Dict[str, Any],
    metrics_summary: Dict[str, Any],
    comparison_df: Optional[pd.DataFrame] = None,
) -> str:
    """Generate professional academic simulation report in Markdown format."""
    report = f"""# Maximum Power Point Tracking (MPPT) Simulation Report
**Project:** Fuzzy Logic-Based MPPT Controller for Solar Photovoltaic Systems  
**Domain:** Electrical Engineering / Renewable Energy Systems  
**Reference Module:** {sim_settings.get("module_name", "Canadian Solar CS5P-220M")}  

---

## 1. Executive Summary
This academic simulation investigated maximum power point extraction from a photovoltaic solar array under variable environmental conditions. An intelligent Mamdani Fuzzy Logic Controller (FLC) was implemented to adjust the duty cycle of a DC-DC boost converter and compared directly against a classical Perturb and Observe (P&O) MPPT baseline.

### Key Simulation Settings
- **Total Duration:** {sim_settings.get("duration", 0.5):.2f} seconds
- **Converter Integration Step (dt):** {sim_settings.get("time_step", 5e-5):.1e} seconds
- **Controller Sampling Time (Ts):** {sim_settings.get("sampling_time", 0.005) * 1000.0:.1f} ms
- **PV Array Configuration:** {sim_settings.get("n_series", 1)} Series Module(s) × {sim_settings.get("n_parallel", 1)} Parallel String(s)
- **Environmental Profile:** {sim_settings.get("profile_name", "Scenario A: Constant STC")}

---

## 2. Quantitative Performance Results

### Summary Metrics
- **Fuzzy MPPT Energy Tracking Efficiency (η_MPPT):** {metrics_summary.get("fuzzy_efficiency", "N/A")}
- **P&O MPPT Energy Tracking Efficiency (η_MPPT):** {metrics_summary.get("po_efficiency", "N/A")}
- **Fuzzy Settling Time:** {metrics_summary.get("fuzzy_settling", "N/A")}
- **P&O Settling Time:** {metrics_summary.get("po_settling", "N/A")}
- **Steady-State Power Ripple (Fuzzy vs P&O):** {metrics_summary.get("fuzzy_ripple", "N/A")} vs {metrics_summary.get("po_ripple", "N/A")}

---

## 3. Comparative Benchmark Table
"""
    if comparison_df is not None:
        report += "\n" + comparison_df.to_markdown(index=False) + "\n\n"

    report += """
---

## 4. Engineering Findings & Conclusions
1. **Steady-State Oscillation Reduction:** The Fuzzy Logic Controller smoothly reduces duty cycle step adjustments as the operating point approaches $dP/dV = 0$, virtually eliminating steady-state limit-cycle power oscillations observed in fixed-step P&O.
2. **Transient Tracking Speed:** During rapid irradiance disturbances, the normalized linguistic rule base ($NB, NS, ZE, PS, PB$) applies aggressive duty steps ($PB/NB$), reaching the new MPP significantly faster than incremental P&O.
3. **Energy Yield:** The combined benefits of fast tracking and ripple elimination yield higher total energy extraction over dynamic environmental cycles.

---
*Report generated automatically by the Solar MPPT Simulation Platform.*
"""
    return report
