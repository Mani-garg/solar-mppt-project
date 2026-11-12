"""
Unit tests for Performance Metrics and Benchmark Calculations.
"""

import pytest
import numpy as np
import pandas as pd
from src.metrics import compute_metrics, compare_controllers, MPPTPerformanceMetrics


def test_compute_metrics_calculations():
    """Verify energy integration and efficiency bounds."""
    t = np.linspace(0.0, 1.0, 1001)
    # Synthetic ideal tracking
    p_mpp = 200.0 * np.ones_like(t)
    p_pv = 196.0 * np.ones_like(t)  # 98% efficiency
    p_out = 186.2 * np.ones_like(t)  # 95% converter efficiency

    df = pd.DataFrame({
        "time": t,
        "p_pv": p_pv,
        "p_mpp_ref": p_mpp,
        "p_out": p_out,
        "instantaneous_efficiency": (p_pv / p_mpp) * 100.0,
        "controller_type": "Fuzzy Logic MPPT",
    })

    metrics = compute_metrics(df, settling_tolerance_pct=2.0)

    assert abs(metrics.tracking_efficiency_energy - 98.0) < 0.2
    assert abs(metrics.tracking_efficiency_mean - 98.0) < 0.2
    assert metrics.energy_loss_wh > 0.0
    assert abs(metrics.converter_avg_efficiency - 95.0) < 0.2
    assert metrics.settling_time_s is not None


def test_compare_controllers_table():
    """Verify side-by-side comparison dataframe creation."""
    m_f = MPPTPerformanceMetrics(
        controller_name="Fuzzy Logic MPPT",
        tracking_efficiency_energy=98.5,
        tracking_efficiency_mean=98.2,
        energy_extracted_joules=98500.0,
        energy_extracted_wh=27.36,
        energy_reference_wh=27.78,
        energy_loss_wh=0.42,
        avg_pv_power=197.0,
        peak_pv_power=205.0,
        avg_output_power=187.0,
        converter_avg_efficiency=94.9,
        settling_time_s=0.035,
        oscillation_amplitude_w=0.45,
        oscillation_std_w=0.12,
        duration_s=1.0,
    )
    m_p = MPPTPerformanceMetrics(
        controller_name="P&O MPPT",
        tracking_efficiency_energy=96.1,
        tracking_efficiency_mean=95.8,
        energy_extracted_joules=96100.0,
        energy_extracted_wh=26.69,
        energy_reference_wh=27.78,
        energy_loss_wh=1.09,
        avg_pv_power=192.2,
        peak_pv_power=203.0,
        avg_output_power=182.5,
        converter_avg_efficiency=94.9,
        settling_time_s=None,
        oscillation_amplitude_w=2.85,
        oscillation_std_w=0.95,
        duration_s=1.0,
    )

    df_comp = compare_controllers(m_f, m_p)
    assert len(df_comp) >= 8
    assert "Fuzzy Logic MPPT" in df_comp.columns
    assert "P&O MPPT" in df_comp.columns
