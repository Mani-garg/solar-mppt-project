"""
Unit and dynamic stability tests for DC-DC Boost Converter Model.
"""

import pytest
import numpy as np
from src.pv_model import SingleDiodePVModel
from src.boost_converter import BoostConverterModel, BoostConverterState
from src.config import BoostConverterParams


def test_converter_initial_state():
    """Verify state initialization."""
    pv = SingleDiodePVModel()
    conv = BoostConverterModel(pv)
    assert conv.v_pv > 0.0
    assert conv.i_l >= 0.0
    assert conv.v_out > 0.0
    assert 0.0 < conv.duty_cycle < 1.0


def test_converter_derivatives_finite():
    """Verify that state derivatives remain finite."""
    pv = SingleDiodePVModel()
    conv = BoostConverterModel(pv)
    dv, di, dvo = conv.derivatives(
        v_pv=45.0,
        i_l=3.0,
        v_out=70.0,
        duty_cycle=0.40,
        irradiance=1000.0,
        temperature_c=25.0,
    )

    assert np.isfinite(dv)
    assert np.isfinite(di)
    assert np.isfinite(dvo)


def test_converter_inductor_current_non_negative():
    """Verify that inductor current never reverses under diode conduction constraint."""
    pv = SingleDiodePVModel()
    conv = BoostConverterModel(pv)
    conv.reset(v_pv=20.0, i_l=0.0, v_out=80.0, duty_cycle=0.1)

    # Even with reverse electromotive force (V_pv < (1-D)*V_out), current cannot reverse
    dv, di, dvo = conv.derivatives(
        v_pv=20.0,
        i_l=0.0,
        v_out=80.0,
        duty_cycle=0.1,
        irradiance=100.0,
        temperature_c=25.0,
    )
    assert di >= 0.0, "Diode should block negative inductor current derivative when i_L = 0"


def test_converter_rk4_step_stability():
    """Verify numerical convergence of RK4 integration step."""
    pv = SingleDiodePVModel()
    conv = BoostConverterModel(pv)
    conv.reset(v_pv=45.0, i_l=3.0, v_out=60.0, duty_cycle=0.35)

    dt = 5e-5
    for _ in range(500):  # 25 ms simulation
        state = conv.step_rk4(dt, irradiance=1000.0, temperature_c=25.0)
        assert np.isfinite(state.v_pv)
        assert np.isfinite(state.i_inductor)
        assert np.isfinite(state.v_out)
        assert state.i_inductor >= 0.0
        assert state.v_pv > 0.0
        assert state.v_out > 0.0
