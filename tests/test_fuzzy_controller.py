"""
Unit and functional tests for Fuzzy Logic MPPT Controller.
"""

import pytest
import numpy as np
from src.fuzzy_controller import FuzzyMPPTController
from src.config import FuzzyControllerParams


def test_fuzzy_membership_completeness():
    """Verify that membership functions partition the universe of discourse."""
    ctrl = FuzzyMPPTController()
    test_points = np.linspace(-1.0, 1.0, 21)

    for pt in test_points:
        mem = ctrl.compute_membership(pt)
        assert len(mem) == 5
        # Total membership sum across fuzzy partition should be ~ 1.0 (Ruspini condition)
        total_deg = sum(mem.values())
        assert 0.8 <= total_deg <= 1.2, f"Membership sum {total_deg} at {pt} outside partition tolerance"


def test_fuzzy_zero_error_behavior():
    """Verify that zero error produces zero duty cycle perturbation."""
    ctrl = FuzzyMPPTController()
    out = ctrl.evaluate(0.0, 0.0)
    assert abs(out) < 1e-3, f"Expected 0.0 output at (0, 0), got {out}"


def test_fuzzy_physical_direction_symmetry():
    """Verify that controller perturbation direction matches converter physics."""
    ctrl = FuzzyMPPTController()

    # Left of MPP (E > 0): V is too low -> need to decrease D -> Delta D must be NEGATIVE
    out_pos_e = ctrl.evaluate(e_norm=0.8, ce_norm=0.0)
    assert out_pos_e < -0.3, f"Expected negative Delta D for positive error, got {out_pos_e}"

    # Right of MPP (E < 0): V is too high -> need to increase D -> Delta D must be POSITIVE
    out_neg_e = ctrl.evaluate(e_norm=-0.8, ce_norm=0.0)
    assert out_neg_e > 0.3, f"Expected positive Delta D for negative error, got {out_neg_e}"

    # Antisymmetry: f(-E, -CE) = -f(E, CE)
    assert abs(out_pos_e + out_neg_e) < 1e-4, "FLC output should be antisymmetric"


def test_fuzzy_duty_cycle_saturation():
    """Verify that duty cycle stays strictly within [d_min, d_max]."""
    params = FuzzyControllerParams(d_min=0.10, d_max=0.85, k_delta_d=0.05)
    ctrl = FuzzyMPPTController(params=params)

    # Force continuous positive error (decrease D towards lower bound)
    ctrl.reset(initial_d=0.20)
    for _ in range(50):
        # Supply increasing V and decreasing P (dP/dV < 0, but let's test extreme steps)
        ctrl.step(v_pv=40.0, p_pv=100.0)
        ctrl.step(v_pv=45.0, p_pv=150.0)  # E > 0 -> D decreases

    assert ctrl.duty_cycle >= params.d_min

    # Force continuous negative error (increase D towards upper bound)
    ctrl.reset(initial_d=0.75)
    for _ in range(50):
        ctrl.step(v_pv=55.0, p_pv=150.0)
        ctrl.step(v_pv=50.0, p_pv=100.0)  # E < 0 -> D increases

    assert ctrl.duty_cycle <= params.d_max


def test_fuzzy_no_nan_or_infinities():
    """Verify safe handling of zero voltage differences and extreme inputs."""
    ctrl = FuzzyMPPTController()
    ctrl.reset(initial_d=0.50)

    # Repeated identical voltage and power (delta V = 0)
    for _ in range(10):
        d, rec = ctrl.step(v_pv=48.0, p_pv=200.0)
        assert not np.isnan(d)
        assert not np.isinf(d)
        assert not np.isnan(rec.e_raw)
        assert not np.isnan(rec.delta_d)
