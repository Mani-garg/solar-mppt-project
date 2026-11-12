"""
Unit and functional tests for Perturb and Observe (P&O) MPPT Controller.
"""

import pytest
import numpy as np
from src.po_controller import POController
from src.config import POControllerParams


def test_po_initialization():
    """Verify clean initialization and reset."""
    ctrl = POController()
    ctrl.reset(initial_d=0.35)
    assert ctrl.duty_cycle == 0.35
    assert ctrl.prev_v is None
    assert ctrl.prev_p is None


def test_po_perturbation_direction():
    """Verify perturbation step follows physical hill-climbing rules."""
    params = POControllerParams(delta_d_step=0.01, d_min=0.05, d_max=0.90)
    ctrl = POController(params=params)
    ctrl.reset(initial_d=0.40)

    # Initial sample
    ctrl.step(v_pv=40.0, p_pv=150.0)

    # Sample 2: V increased to 42V, P increased to 170W (Delta P > 0, Delta V > 0)
    # Voltage moving towards MPP from left -> decrease D to keep increasing V
    d, rec = ctrl.step(v_pv=42.0, p_pv=170.0)
    assert rec.perturbation_direction == -1
    assert abs(d - 0.39) < 1e-4

    # Sample 3: V increased to 44V, P decreased to 160W (Delta P < 0, Delta V > 0)
    # Passed MPP -> reverse direction: increase D
    d, rec = ctrl.step(v_pv=44.0, p_pv=160.0)
    assert rec.perturbation_direction == +1
    assert abs(d - 0.40) < 1e-4


def test_po_saturation():
    """Verify that duty cycle stays strictly within bounds."""
    params = POControllerParams(delta_d_step=0.05, d_min=0.10, d_max=0.80)
    ctrl = POController(params=params)
    ctrl.reset(initial_d=0.12)

    # Force continuous decrease
    ctrl.step(v_pv=40.0, p_pv=100.0)
    for v, p in [(42.0, 110.0), (44.0, 120.0), (46.0, 130.0), (48.0, 140.0)]:
        d, _ = ctrl.step(v, p)

    assert ctrl.duty_cycle >= params.d_min
