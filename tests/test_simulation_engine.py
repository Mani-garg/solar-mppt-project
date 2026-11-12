"""
Integration tests for SimulationEngine with multi-rate controllers.
"""

import pytest
import numpy as np
import pandas as pd
from src.pv_model import SingleDiodePVModel
from src.boost_converter import BoostConverterModel
from src.fuzzy_controller import FuzzyMPPTController
from src.po_controller import POController
from src.environmental_profiles import EnvironmentalProfile
from src.simulation_engine import SimulationEngine
from src.config import SimulationConfig


def test_simulation_runs_and_returns_dataframe():
    """Verify end-to-end execution and output DataFrame structure."""
    pv = SingleDiodePVModel()
    conv = BoostConverterModel(pv)
    prof = EnvironmentalProfile.scenario_a_constant()
    engine = SimulationEngine(pv, conv, prof, SimulationConfig(duration=0.1, time_step=1e-4))

    df = engine.run(FuzzyMPPTController(), controller_sampling_time=0.005)

    required_cols = [
        "time", "irradiance", "temperature", "v_pv", "i_pv", "p_pv",
        "v_mpp_ref", "i_mpp_ref", "p_mpp_ref", "duty_cycle",
        "v_out", "i_inductor", "p_out", "instantaneous_efficiency", "controller_type"
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"

    assert len(df) > 10
    assert df["time"].iloc[-1] <= 0.10 + 1e-4
    assert np.all(np.isfinite(df["p_pv"]))
    assert np.all(np.isfinite(df["duty_cycle"]))


def test_simulation_environmental_change_applied():
    """Verify that irradiance step change is correctly reflected in telemetry."""
    pv = SingleDiodePVModel()
    conv = BoostConverterModel(pv)
    prof = EnvironmentalProfile.scenario_b_irradiance_drop(t_step=0.05, g1=1000.0, g2=600.0)
    engine = SimulationEngine(pv, conv, prof, SimulationConfig(duration=0.1, time_step=1e-4))

    df = engine.run(POController(), controller_sampling_time=0.005)

    # Before 0.05s, irradiance must be 1000
    df_early = df[df["time"] < 0.045]
    assert np.all(df_early["irradiance"] == 1000.0)

    # After 0.05s, irradiance must be 600
    df_late = df[df["time"] > 0.055]
    assert np.all(df_late["irradiance"] == 600.0)

    # Reference MPP power must drop accordingly
    assert df_early["p_mpp_ref"].iloc[0] > df_late["p_mpp_ref"].iloc[-1]
