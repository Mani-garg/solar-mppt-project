"""
Interactive Plotly Visualization Module for Solar PV and MPPT Analysis.
Produces clean, publication-ready engineering figures with responsive layouts.
"""

from typing import List, Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.pv_model import MPPResult


# Professional Scientific / IEEE Engineering Palette
COLOR_FUZZY = "#059669"      # Forest / Emerald Green
COLOR_PO = "#DC2626"         # Precision Red
COLOR_REF = "#0F172A"        # Slate Black
COLOR_IRR = "#D97706"        # Solar Amber
COLOR_TEMP = "#BE185D"       # Thermal Magenta
COLOR_VOUT = "#4338CA"       # Indigo
COLOR_IL = "#0E7490"         # Cyan Teal
COLOR_DUTY = "#6D28D9"       # Deep Purple

LAYOUT_COMMON = dict(
    template="plotly_white",
    font=dict(family="'IBM Plex Sans', -apple-system, sans-serif", size=11, color="#0F172A"),
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    margin=dict(l=60, r=40, t=50, b=50),
    hovermode="x unified",
)


def plot_iv_pv_curves(
    v_vec: np.ndarray,
    i_vec: np.ndarray,
    p_vec: np.ndarray,
    mpp: MPPResult,
) -> go.Figure:
    """Generate dual-panel interactive I-V and P-V characteristic curves."""
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("I-V Characteristic Curve", "P-V Characteristic Curve"),
        horizontal_spacing=0.12,
    )

    # I-V Curve
    fig.add_trace(
        go.Scatter(
            x=v_vec,
            y=i_vec,
            mode="lines",
            name="I-V Curve",
            line=dict(color="#2563EB", width=2.5),
            hovertemplate="Voltage: %{x:.2f} V<br>Current: %{y:.2f} A<extra></extra>",
        ),
        row=1,
        col=1,
    )

    # MPP Marker on I-V
    fig.add_trace(
        go.Scatter(
            x=[mpp.v_mpp],
            y=[mpp.i_mpp],
            mode="markers+text",
            name="MPP Point",
            text=[f"MPP ({mpp.v_mpp:.1f}V, {mpp.i_mpp:.2f}A)"],
            textposition="top right",
            marker=dict(color="#DC2626", size=10, symbol="diamond"),
        ),
        row=1,
        col=1,
    )

    # P-V Curve
    fig.add_trace(
        go.Scatter(
            x=v_vec,
            y=p_vec,
            mode="lines",
            name="P-V Curve",
            line=dict(color="#059669", width=2.5),
            hovertemplate="Voltage: %{x:.2f} V<br>Power: %{y:.2f} W<extra></extra>",
        ),
        row=1,
        col=2,
    )

    # MPP Marker on P-V
    fig.add_trace(
        go.Scatter(
            x=[mpp.v_mpp],
            y=[mpp.p_mpp],
            mode="markers+text",
            name="MPP Peak",
            text=[f"P_max = {mpp.p_mpp:.1f} W"],
            textposition="top center",
            marker=dict(color="#DC2626", size=10, symbol="star"),
        ),
        row=1,
        col=2,
    )

    fig.update_xaxes(title_text="PV Voltage (V)", gridcolor="#E2E8F0", row=1, col=1)
    fig.update_yaxes(title_text="PV Current (A)", gridcolor="#E2E8F0", row=1, col=1)
    fig.update_xaxes(title_text="PV Voltage (V)", gridcolor="#E2E8F0", row=1, col=2)
    fig.update_yaxes(title_text="PV Power (W)", gridcolor="#E2E8F0", row=1, col=2)

    fig.update_layout(
        **LAYOUT_COMMON,
        title_text=f"Solar PV Electrical Characteristics (Voc={mpp.v_oc:.1f}V, Isc={mpp.i_sc:.2f}A, Pmp={mpp.p_mpp:.1f}W)",
        showlegend=False,
        height=420,
    )
    return fig


def plot_single_mppt_response(
    df: pd.DataFrame,
    transition_times: Optional[List[float]] = None,
) -> go.Figure:
    """Multi-panel time-domain response of a single MPPT controller simulation."""
    fig = make_subplots(
        rows=3,
        cols=2,
        subplot_titles=(
            "PV Power vs Time",
            "PV Voltage vs Time",
            "PV Current vs Time",
            "Duty Cycle (D) vs Time",
            "Boost Converter Output Voltage vs Time",
            "Inductor Current vs Time",
        ),
        vertical_spacing=0.10,
        horizontal_spacing=0.10,
    )

    ctrl_name = df["controller_type"].iloc[0] if "controller_type" in df.columns else "MPPT"
    c_color = COLOR_FUZZY if "Fuzzy" in ctrl_name else COLOR_PO

    # 1. Power
    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["p_mpp_ref"],
            mode="lines",
            name="Theoretical P_mpp",
            line=dict(color=COLOR_REF, width=1.8, dash="dash"),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["p_pv"],
            mode="lines",
            name="Tracked P_pv",
            line=dict(color=c_color, width=2.0),
        ),
        row=1,
        col=1,
    )

    # 2. Voltage
    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["v_mpp_ref"],
            mode="lines",
            name="Ref V_mpp",
            line=dict(color=COLOR_REF, width=1.5, dash="dash"),
        ),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["v_pv"],
            mode="lines",
            name="PV Voltage",
            line=dict(color="#2563EB", width=2.0),
        ),
        row=1,
        col=2,
    )

    # 3. Current
    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["i_pv"],
            mode="lines",
            name="PV Current",
            line=dict(color="#0D9488", width=2.0),
        ),
        row=2,
        col=1,
    )

    # 4. Duty cycle
    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["duty_cycle"],
            mode="lines",
            name="Duty Cycle (D)",
            line=dict(color=COLOR_DUTY, width=2.0),
        ),
        row=2,
        col=2,
    )

    # 5. Output voltage
    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["v_out"],
            mode="lines",
            name="V_out",
            line=dict(color=COLOR_VOUT, width=2.0),
        ),
        row=3,
        col=1,
    )

    # 6. Inductor current
    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["i_inductor"],
            mode="lines",
            name="I_L",
            line=dict(color=COLOR_IL, width=2.0),
        ),
        row=3,
        col=2,
    )

    # Mark transitions if any
    if transition_times:
        for t_trans in transition_times:
            for r in range(1, 4):
                for c in range(1, 3):
                    fig.add_vline(
                        x=t_trans,
                        line_width=1.2,
                        line_dash="dot",
                        line_color="#94A3B8",
                        row=r,
                        col=c,
                    )

    # Axes titles
    fig.update_xaxes(title_text="Time (s)", gridcolor="#E2E8F0")
    fig.update_yaxes(gridcolor="#E2E8F0")
    fig.update_yaxes(title_text="Power (W)", row=1, col=1)
    fig.update_yaxes(title_text="Voltage (V)", row=1, col=2)
    fig.update_yaxes(title_text="Current (A)", row=2, col=1)
    fig.update_yaxes(title_text="Duty Cycle", row=2, col=2)
    fig.update_yaxes(title_text="V_out (V)", row=3, col=1)
    fig.update_yaxes(title_text="I_L (A)", row=3, col=2)

    fig.update_layout(
        **LAYOUT_COMMON,
        title_text=f"Dynamic Response: {ctrl_name}",
        showlegend=False,
        height=800,
    )
    return fig


def plot_controller_comparison_overlay(
    df_fuzzy: pd.DataFrame,
    df_po: pd.DataFrame,
    transition_times: Optional[List[float]] = None,
) -> go.Figure:
    """Direct comparison overlay of Fuzzy Logic vs P&O MPPT."""
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        subplot_titles=(
            "PV Power Tracking: Fuzzy Logic vs P&O vs True MPP",
            "PV Operating Voltage Tracking",
            "Converter Duty Cycle Adjustment",
        ),
        vertical_spacing=0.08,
    )

    # 1. Power Tracking
    fig.add_trace(
        go.Scatter(
            x=df_fuzzy["time"],
            y=df_fuzzy["p_mpp_ref"],
            mode="lines",
            name="Reference MPP",
            line=dict(color=COLOR_REF, width=2.0, dash="dash"),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df_fuzzy["time"],
            y=df_fuzzy["p_pv"],
            mode="lines",
            name="Fuzzy Logic MPPT",
            line=dict(color=COLOR_FUZZY, width=2.2),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df_po["time"],
            y=df_po["p_pv"],
            mode="lines",
            name="P&O MPPT",
            line=dict(color=COLOR_PO, width=1.8),
        ),
        row=1,
        col=1,
    )

    # 2. Voltage Tracking
    fig.add_trace(
        go.Scatter(
            x=df_fuzzy["time"],
            y=df_fuzzy["v_mpp_ref"],
            mode="lines",
            name="Ref V_mpp",
            line=dict(color=COLOR_REF, width=1.5, dash="dash"),
            showlegend=False,
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df_fuzzy["time"],
            y=df_fuzzy["v_pv"],
            mode="lines",
            name="Fuzzy Voltage",
            line=dict(color=COLOR_FUZZY, width=2.0),
            showlegend=False,
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df_po["time"],
            y=df_po["v_pv"],
            mode="lines",
            name="P&O Voltage",
            line=dict(color=COLOR_PO, width=1.8),
            showlegend=False,
        ),
        row=2,
        col=1,
    )

    # 3. Duty Cycle
    fig.add_trace(
        go.Scatter(
            x=df_fuzzy["time"],
            y=df_fuzzy["duty_cycle"],
            mode="lines",
            name="Fuzzy Duty Cycle",
            line=dict(color=COLOR_FUZZY, width=2.0),
            showlegend=False,
        ),
        row=3,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df_po["time"],
            y=df_po["duty_cycle"],
            mode="lines",
            name="P&O Duty Cycle",
            line=dict(color=COLOR_PO, width=1.8),
            showlegend=False,
        ),
        row=3,
        col=1,
    )

    # Transitions
    if transition_times:
        for t_trans in transition_times:
            for r in range(1, 4):
                fig.add_vline(
                    x=t_trans,
                    line_width=1.2,
                    line_dash="dot",
                    line_color="#94A3B8",
                    row=r,
                    col=1,
                )

    fig.update_xaxes(gridcolor="#E2E8F0")
    fig.update_xaxes(title_text="Time (s)", row=3, col=1)
    fig.update_yaxes(title_text="Power (W)", gridcolor="#E2E8F0", row=1, col=1)
    fig.update_yaxes(title_text="Voltage (V)", gridcolor="#E2E8F0", row=2, col=1)
    fig.update_yaxes(title_text="Duty Cycle (D)", gridcolor="#E2E8F0", row=3, col=1)

    fig.update_layout(
        **LAYOUT_COMMON,
        title_text="Performance Comparison: Fuzzy Logic MPPT vs Classical P&O",
        height=720,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0),
    )
    return fig


def plot_environmental_conditions(
    df: pd.DataFrame,
    transition_times: Optional[List[float]] = None,
) -> go.Figure:
    """Plot irradiance and cell temperature over time on secondary axes."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["irradiance"],
            mode="lines",
            name="Irradiance (W/m²)",
            line=dict(color=COLOR_IRR, width=2.5),
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=df["time"],
            y=df["temperature"],
            mode="lines",
            name="Cell Temp (°C)",
            line=dict(color=COLOR_TEMP, width=2.5),
        ),
        secondary_y=True,
    )

    if transition_times:
        for t_trans in transition_times:
            fig.add_vline(
                x=t_trans,
                line_width=1.2,
                line_dash="dot",
                line_color="#94A3B8",
            )

    fig.update_xaxes(title_text="Time (s)", gridcolor="#E2E8F0")
    fig.update_yaxes(title_text="Irradiance (W/m²)", color=COLOR_IRR, gridcolor="#E2E8F0", secondary_y=False)
    fig.update_yaxes(title_text="Cell Temperature (°C)", color=COLOR_TEMP, secondary_y=True)

    fig.update_layout(
        **LAYOUT_COMMON,
        title_text="Environmental Profile (Solar Irradiance and Cell Temperature)",
        height=350,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0),
    )
    return fig


def plot_fuzzy_membership_functions() -> go.Figure:
    """Generate interactive plots of the Fuzzy Controller Membership Functions."""
    fig = make_subplots(
        rows=1,
        cols=3,
        subplot_titles=(
            "Input 1: Error E (Normalized)",
            "Input 2: Change in Error CE (Normalized)",
            "Output: Duty Cycle Delta D (Normalized)",
        ),
        horizontal_spacing=0.08,
    )

    x = np.linspace(-1.0, 1.0, 201)
    colors = {
        "NB": "#EF4444",
        "NS": "#F97316",
        "ZE": "#10B981",
        "PS": "#06B6D4",
        "PB": "#3B82F6",
    }

    # Evaluate membership curves
    from src.fuzzy_controller import FuzzyMPPTController
    f_dummy = FuzzyMPPTController()

    for term in ["NB", "NS", "ZE", "PS", "PB"]:
        y_vals = [f_dummy.compute_membership(val)[term] for val in x]
        # E
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y_vals,
                mode="lines",
                name=term,
                line=dict(color=colors[term], width=2.0),
                legendgroup=term,
            ),
            row=1,
            col=1,
        )
        # CE
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y_vals,
                mode="lines",
                name=term,
                line=dict(color=colors[term], width=2.0),
                legendgroup=term,
                showlegend=False,
            ),
            row=1,
            col=2,
        )
        # Delta D
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y_vals,
                mode="lines",
                name=term,
                line=dict(color=colors[term], width=2.0),
                legendgroup=term,
                showlegend=False,
            ),
            row=1,
            col=3,
        )

    fig.update_xaxes(title_text="Normalized Input E", gridcolor="#E2E8F0", row=1, col=1)
    fig.update_xaxes(title_text="Normalized Input CE", gridcolor="#E2E8F0", row=1, col=2)
    fig.update_xaxes(title_text="Normalized Output ΔD", gridcolor="#E2E8F0", row=1, col=3)
    fig.update_yaxes(title_text="Membership Degree μ", gridcolor="#E2E8F0", range=[-0.05, 1.05])

    fig.update_layout(
        **LAYOUT_COMMON,
        title_text="Fuzzy Logic Controller: 5-Level Linguistic Membership Functions",
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0),
    )
    return fig


def plot_fuzzy_control_surface() -> go.Figure:
    """Generate 3D surface plot of the Fuzzy Logic Controller."""
    from src.fuzzy_controller import FuzzyMPPTController
    f_ctrl = FuzzyMPPTController()

    e_grid = np.linspace(-1.0, 1.0, 31)
    ce_grid = np.linspace(-1.0, 1.0, 31)
    e_mesh, ce_mesh = np.meshgrid(e_grid, ce_grid)

    z_surf = np.zeros_like(e_mesh)
    for i in range(e_mesh.shape[0]):
        for j in range(e_mesh.shape[1]):
            z_surf[i, j] = f_ctrl.evaluate(e_mesh[i, j], ce_mesh[i, j])

    fig = go.Figure(
        data=[
            go.Surface(
                x=e_mesh,
                y=ce_mesh,
                z=z_surf,
                colorscale="Viridis",
                colorbar=dict(title="Normalized ΔD"),
            )
        ]
    )

    fig.update_layout(
        template="plotly_white",
        title="Fuzzy Logic MPPT 3D Decision Surface (ΔD vs E and CE)",
        scene=dict(
            xaxis=dict(title="Error E (Normalized)"),
            yaxis=dict(title="Change in Error CE"),
            zaxis=dict(title="Output ΔD (Normalized)"),
        ),
        margin=dict(l=40, r=40, t=50, b=40),
        height=480,
    )
    return fig
