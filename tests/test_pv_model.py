"""
Unit and physical validation tests for Photovoltaic Single-Diode Model.
"""

import pytest
import numpy as np
from src.config import PVModuleParams, PVArrayConfig
from src.pv_model import SingleDiodePVModel, MPPResult


def test_pv_stc_mpp_values():
    """Verify STC reference values for Canadian Solar CS5P-220M."""
    model = SingleDiodePVModel()
    mpp = model.compute_reference_mpp(irradiance=1000.0, temperature_c=25.0)

    # Physical checks
    assert 55.0 <= mpp.v_oc <= 65.0, f"Voc ({mpp.v_oc:.1f}V) outside expected range"
    assert 4.8 <= mpp.i_sc <= 5.4, f"Isc ({mpp.i_sc:.2f}A) outside expected range"
    assert 44.0 <= mpp.v_mpp <= 52.0, f"Vmpp ({mpp.v_mpp:.1f}V) outside expected range"
    assert 4.3 <= mpp.i_mpp <= 4.9, f"Impp ({mpp.i_mpp:.2f}A) outside expected range"
    assert 210.0 <= mpp.p_mpp <= 230.0, f"Pmpp ({mpp.p_mpp:.1f}W) outside expected range"


def test_pv_irradiance_dependency():
    """Verify that power scales monotonically with irradiance."""
    model = SingleDiodePVModel()
    mpp_1000 = model.compute_reference_mpp(irradiance=1000.0, temperature_c=25.0)
    mpp_600 = model.compute_reference_mpp(irradiance=600.0, temperature_c=25.0)
    mpp_300 = model.compute_reference_mpp(irradiance=300.0, temperature_c=25.0)

    assert mpp_1000.p_mpp > mpp_600.p_mpp > mpp_300.p_mpp
    # Photocurrent scales approximately linearly with G
    assert abs((mpp_600.i_sc / mpp_1000.i_sc) - 0.6) < 0.05


def test_pv_temperature_dependency():
    """Verify negative temperature coefficient for voltage."""
    model = SingleDiodePVModel()
    mpp_25 = model.compute_reference_mpp(irradiance=1000.0, temperature_c=25.0)
    mpp_50 = model.compute_reference_mpp(irradiance=1000.0, temperature_c=50.0)

    # Voc and Vmpp must decrease as temperature rises
    assert mpp_50.v_oc < mpp_25.v_oc
    assert mpp_50.v_mpp < mpp_25.v_mpp
    assert mpp_50.p_mpp < mpp_25.p_mpp  # Higher temperature decreases efficiency


def test_pv_characteristic_curves_consistency():
    """Verify mathematical consistency between I-V and P-V vectors."""
    model = SingleDiodePVModel()
    v_vec, i_vec, p_vec, mpp = model.generate_characteristic_curves(1000.0, 25.0, num_points=100)

    assert len(v_vec) == 100
    assert np.all(i_vec >= 0.0), "PV current must be non-negative in 1st quadrant"
    assert np.all(p_vec >= 0.0), "PV power must be non-negative"

    # P(V) must equal V * I(V) everywhere
    np.testing.assert_allclose(p_vec, v_vec * i_vec, rtol=1e-5)

    # Curve peak should be very close to numerical MPP
    assert abs(np.max(p_vec) - mpp.p_mpp) < 0.5


def test_pv_array_scaling():
    """Verify series and parallel array multiplier scaling."""
    mod = PVModuleParams()
    single_model = SingleDiodePVModel(PVArrayConfig(module_params=mod, n_modules_series=1, n_strings_parallel=1))
    array_model = SingleDiodePVModel(PVArrayConfig(module_params=mod, n_modules_series=3, n_strings_parallel=2))

    mpp_single = single_model.compute_reference_mpp(1000.0, 25.0)
    mpp_array = array_model.compute_reference_mpp(1000.0, 25.0)

    # Series scales voltage by 3x
    assert abs((mpp_array.v_oc / mpp_single.v_oc) - 3.0) < 0.02
    assert abs((mpp_array.v_mpp / mpp_single.v_mpp) - 3.0) < 0.02

    # Parallel scales current by 2x
    assert abs((mpp_array.i_sc / mpp_single.i_sc) - 2.0) < 0.02
    assert abs((mpp_array.i_mpp / mpp_single.i_mpp) - 2.0) < 0.02

    # Total power scales by 6x
    assert abs((mpp_array.p_mpp / mpp_single.p_mpp) - 6.0) < 0.05
