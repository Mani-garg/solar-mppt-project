"""
Photovoltaic (PV) Module and Array Single-Diode Model.
Implements the 5-parameter single-diode physical equations, analytical Lambert W
solutions, pvlib integration, I-V / P-V curve extraction, and independent reference
MPP computation.
"""

from dataclasses import dataclass
from typing import Tuple, Optional, Union
import numpy as np
from scipy.special import lambertw
from scipy.optimize import minimize_scalar

from src.config import (
    PVModuleParams,
    PVArrayConfig,
    BOLTZMANN_K,
    ELEMENTARY_Q,
    T_STC_KELVIN,
    G_STC,
    EG_SILICON,
)


@dataclass
class MPPResult:
    """True Reference Maximum Power Point values."""
    v_mpp: float  # Voltage at MPP (V)
    i_mpp: float  # Current at MPP (A)
    p_mpp: float  # Power at MPP (W)
    v_oc: float   # Open-circuit voltage (V)
    i_sc: float   # Short-circuit current (A)


class SingleDiodePVModel:
    """
    Physical single-diode photovoltaic model supporting individual modules
    and scalable PV arrays under arbitrary irradiance and cell temperature.
    """

    def __init__(self, array_config: Optional[PVArrayConfig] = None):
        if array_config is None:
            self.config = PVArrayConfig()
        else:
            self.config = array_config

    @property
    def module(self) -> PVModuleParams:
        return self.config.module_params

    @property
    def n_series(self) -> int:
        return max(1, self.config.n_modules_series)

    @property
    def n_parallel(self) -> int:
        return max(1, self.config.n_strings_parallel)

    def calculate_diode_parameters(
        self, irradiance: float, temperature_c: float
    ) -> dict:
        """
        Calculate temperature and irradiance adjusted single-diode parameters
        for a single module.
        """
        g = max(1.0, float(irradiance))
        t_c = float(temperature_c)
        t_k = t_c + 273.15

        # Thermal voltage per cell and total modified diode voltage
        vt_cell = (BOLTZMANN_K * t_k) / ELEMENTARY_Q
        a = self.module.ideality_n * self.module.n_series_cells * vt_cell

        # Temperature-adjusted bandgap energy Eg(T)
        delta_t = t_k - T_STC_KELVIN
        eg_t = EG_SILICON * (1.0 - 0.0002677 * delta_t)

        # Photocurrent I_ph (A)
        i_ph = (g / G_STC) * (
            self.module.i_sc + self.module.alpha_sc * delta_t
        )
        i_ph = max(1e-4, i_ph)

        # Reverse saturation current I_0 (A)
        # Ratio of T/T_stc cubed * exp(Eg / n*k * (1/T_stc - 1/T))
        t_ratio = t_k / T_STC_KELVIN
        exp_arg = (ELEMENTARY_Q * EG_SILICON / (self.module.ideality_n * BOLTZMANN_K)) * (
            (1.0 / T_STC_KELVIN) - (1.0 / t_k)
        )
        exp_arg = np.clip(exp_arg, -50.0, 50.0)
        i_0 = self.module.i_0_ref * (t_ratio ** 3.0) * np.exp(exp_arg)
        i_0 = max(1e-14, i_0)

        # Series resistance (assumed constant or slight temp adjustment)
        r_s = max(1e-4, self.module.r_s)

        # Shunt resistance inversely proportional to irradiance
        r_sh = self.module.r_sh * (G_STC / g)
        r_sh = max(1.0, min(1e6, r_sh))

        return {
            "i_ph": i_ph,
            "i_0": i_0,
            "r_s": r_s,
            "r_sh": r_sh,
            "a": a,
            "t_k": t_k,
        }

    def module_current(
        self,
        v_module: Union[float, np.ndarray],
        irradiance: float,
        temperature_c: float,
    ) -> Union[float, np.ndarray]:
        """
        Compute output current I for given module voltage V using the exact
        analytical Lambert W solution of the single-diode equation.
        """
        p = self.calculate_diode_parameters(irradiance, temperature_c)
        i_ph = p["i_ph"]
        i_0 = p["i_0"]
        r_s = p["r_s"]
        r_sh = p["r_sh"]
        a = p["a"]

        v = np.asarray(v_module, dtype=np.float64)
        scalar_input = v.ndim == 0
        v = np.atleast_1d(v)

        # Single-diode analytical solution via Lambert W
        # I = (R_sh*(I_ph + I_0) - V)/(R_s + R_sh) - (a/R_s) * W0(z)
        r_sum = r_s + r_sh
        theta = (r_s * r_sh) / r_sum

        exp_exponent = (r_sh * (v + r_s * (i_ph + i_0))) / (a * r_sum)
        # Protect against overflow in exponent
        exp_exponent = np.clip(exp_exponent, -100.0, 70.0)

        z = (theta * i_0 / a) * np.exp(exp_exponent)
        # Evaluate principal branch of Lambert W
        w = np.real(lambertw(z))

        i_calc = (r_sh * (i_ph + i_0) - v) / r_sum - (a / r_s) * w

        # Physical boundary: module current cannot be negative in 1st quadrant
        i_calc = np.maximum(0.0, i_calc)

        if scalar_input:
            return float(i_calc[0])
        return i_calc

    def array_current(
        self,
        v_array: Union[float, np.ndarray],
        irradiance: float,
        temperature_c: float,
    ) -> Union[float, np.ndarray]:
        """
        Compute total array current I_arr for a given array voltage V_arr.
        V_module = V_array / n_series
        I_array = n_parallel * I_module(V_module)
        """
        v_arr = np.asarray(v_array, dtype=np.float64)
        scalar_input = v_arr.ndim == 0
        v_arr = np.atleast_1d(v_arr)

        v_mod = v_arr / float(self.n_series)
        i_mod = self.module_current(v_mod, irradiance, temperature_c)
        i_arr = float(self.n_parallel) * i_mod

        if scalar_input:
            return float(i_arr[0] if isinstance(i_arr, np.ndarray) else i_arr)
        return i_arr

    def array_power(
        self,
        v_array: Union[float, np.ndarray],
        irradiance: float,
        temperature_c: float,
    ) -> Union[float, np.ndarray]:
        """Compute total array electrical power P_arr = V_arr * I_arr."""
        v = np.asarray(v_array, dtype=np.float64)
        i = self.array_current(v, irradiance, temperature_c)
        return v * i

    def calculate_open_circuit_voltage(
        self, irradiance: float, temperature_c: float
    ) -> float:
        """
        Compute Voc of the single module and scale to array.
        Voc satisfies I(Voc) = 0.
        """
        p = self.calculate_diode_parameters(irradiance, temperature_c)
        # Analytical approximation for single module Voc:
        # Voc ~ a * ln((I_ph + I_0)/I_0) - simplified, refined via Brent root-finding
        init_guess = p["a"] * np.log(max(1.0, (p["i_ph"] + p["i_0"]) / p["i_0"]))
        init_guess = min(max(10.0, init_guess), 100.0)

        def objective(v_mod: float) -> float:
            return abs(self.module_current(v_mod, irradiance, temperature_c))

        res = minimize_scalar(
            objective,
            bounds=(0.0, init_guess * 1.5 + 10.0),
            method="bounded",
            options={"xatol": 1e-4},
        )
        voc_module = float(res.x)
        return voc_module * self.n_series

    def calculate_short_circuit_current(
        self, irradiance: float, temperature_c: float
    ) -> float:
        """Compute Isc of the array at V = 0."""
        return float(self.array_current(0.0, irradiance, temperature_c))

    def compute_reference_mpp(
        self, irradiance: float, temperature_c: float
    ) -> MPPResult:
        """
        Numerically find the true theoretical Maximum Power Point (MPP)
        for the given environmental conditions, independent of any controller.
        Uses 1D bounded optimization on -P(V).
        """
        v_oc = self.calculate_open_circuit_voltage(irradiance, temperature_c)
        i_sc = self.calculate_short_circuit_current(irradiance, temperature_c)

        if v_oc <= 1e-3 or i_sc <= 1e-3:
            return MPPResult(v_mpp=0.0, i_mpp=0.0, p_mpp=0.0, v_oc=v_oc, i_sc=i_sc)

        def neg_power(v: float) -> float:
            # Objective: minimize -P(V)
            return -float(self.array_power(v, irradiance, temperature_c))

        # Search within [0.3 * Voc, 0.95 * Voc] where physical MPP always lies
        res = minimize_scalar(
            neg_power,
            bounds=(0.1 * v_oc, 0.98 * v_oc),
            method="bounded",
            options={"xatol": 1e-4, "maxiter": 100},
        )

        v_mpp = float(res.x)
        i_mpp = float(self.array_current(v_mpp, irradiance, temperature_c))
        p_mpp = float(v_mpp * i_mpp)

        return MPPResult(
            v_mpp=v_mpp,
            i_mpp=i_mpp,
            p_mpp=p_mpp,
            v_oc=v_oc,
            i_sc=i_sc,
        )

    def generate_characteristic_curves(
        self, irradiance: float, temperature_c: float, num_points: int = 150
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, MPPResult]:
        """
        Generate voltage, current, and power vectors for I-V and P-V curve plotting,
        along with the true reference MPP.
        """
        mpp = self.compute_reference_mpp(irradiance, temperature_c)
        v_max = mpp.v_oc * 1.02 if mpp.v_oc > 0 else 50.0

        v_vec = np.linspace(0.0, v_max, num_points)
        i_vec = np.array([self.array_current(v, irradiance, temperature_c) for v in v_vec])
        p_vec = v_vec * i_vec

        return v_vec, i_vec, p_vec, mpp
