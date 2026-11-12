"""
DC-DC Boost Converter Averaged Dynamic Model.
Simulates the continuous-conduction averaged state-space dynamics of an
interleaved/conventional boost converter coupled to a photovoltaic source and resistive load.
"""

from dataclasses import dataclass
from typing import Tuple, Optional
import numpy as np

from src.config import BoostConverterParams
from src.pv_model import SingleDiodePVModel


@dataclass
class BoostConverterState:
    """State vector of the boost converter at an instant in time."""
    v_pv: float        # PV terminal capacitor voltage (V)
    i_inductor: float  # Inductor current (A)
    v_out: float       # Output capacitor voltage (V)
    duty_cycle: float  # Current duty cycle D in [0, 1]


class BoostConverterModel:
    """
    Averaged Continuous-Conduction Mode (CCM) DC-DC Boost Converter.

    State variables:
      x1 = V_pv    (PV input capacitor voltage)
      x2 = i_L     (Inductor current)
      x3 = V_out   (Output capacitor voltage)

    Dynamic equations:
      dV_pv/dt  = (I_pv(V_pv, G, T) - i_L) / C_pv
      di_L/dt   = (V_pv - (1 - D)*V_out - r_L*i_L) / L
      dV_out/dt = ((1 - D)*i_L - V_out/R_load) / C_out
    """

    def __init__(
        self,
        pv_model: SingleDiodePVModel,
        params: BoostConverterParams = BoostConverterParams(),
    ):
        self.pv_model = pv_model
        self.params = params

        # Initial conditions
        self.v_pv: float = float(params.initial_v_pv)
        self.i_l: float = float(params.initial_i_l)
        self.v_out: float = float(params.initial_v_out)
        self.duty_cycle: float = float(params.initial_d)

    def reset(
        self,
        v_pv: Optional[float] = None,
        i_l: Optional[float] = None,
        v_out: Optional[float] = None,
        duty_cycle: Optional[float] = None,
    ) -> None:
        """Reset state variables to initial or specified values."""
        self.v_pv = float(self.params.initial_v_pv if v_pv is None else v_pv)
        self.i_l = float(self.params.initial_i_l if i_l is None else i_l)
        self.v_out = float(self.params.initial_v_out if v_out is None else v_out)
        self.duty_cycle = float(self.params.initial_d if duty_cycle is None else duty_cycle)

    def set_duty_cycle(self, d: float, d_min: float = 0.05, d_max: float = 0.90) -> None:
        """Update converter duty cycle with safety saturation."""
        self.duty_cycle = float(np.clip(d, d_min, d_max))

    def derivatives(
        self,
        v_pv: float,
        i_l: float,
        v_out: float,
        duty_cycle: float,
        irradiance: float,
        temperature_c: float,
    ) -> Tuple[float, float, float]:
        """
        Compute time derivatives dx/dt = f(x, u).
        Enforces physical non-negativity on inductor current (diode conduction).
        """
        # Photovoltaic current at current terminal voltage
        i_pv = float(self.pv_model.array_current(v_pv, irradiance, temperature_c))

        # Parameters
        c_pv = self.params.c_pv
        l = self.params.inductance_l
        r_l = self.params.inductor_r
        c_out = self.params.c_out
        r_load = self.params.load_r

        # Continuous-conduction state derivatives
        dv_pv_dt = (i_pv - i_l) / c_pv

        d = duty_cycle
        di_l_dt = (v_pv - (1.0 - d) * v_out - r_l * i_l) / l

        # Physical diode constraint: inductor current cannot reverse in a boost converter
        if i_l <= 0.0 and di_l_dt < 0.0:
            di_l_dt = 0.0

        dv_out_dt = ((1.0 - d) * i_l - (v_out / r_load)) / c_out

        return dv_pv_dt, di_l_dt, dv_out_dt

    def step_rk4(
        self,
        dt: float,
        irradiance: float,
        temperature_c: float,
    ) -> BoostConverterState:
        """
        Advance state forward by dt using classical 4th-order Runge-Kutta (RK4)
        numerical integration.
        """
        d = self.duty_cycle
        v_pv0 = self.v_pv
        i_l0 = self.i_l
        v_out0 = self.v_out

        # Stage 1
        k1_vpv, k1_il, k1_vout = self.derivatives(
            v_pv0, i_l0, v_out0, d, irradiance, temperature_c
        )

        # Stage 2
        k2_vpv, k2_il, k2_vout = self.derivatives(
            v_pv0 + 0.5 * dt * k1_vpv,
            max(0.0, i_l0 + 0.5 * dt * k1_il),
            max(0.0, v_out0 + 0.5 * dt * k1_vout),
            d,
            irradiance,
            temperature_c,
        )

        # Stage 3
        k3_vpv, k3_il, k3_vout = self.derivatives(
            v_pv0 + 0.5 * dt * k2_vpv,
            max(0.0, i_l0 + 0.5 * dt * k2_il),
            max(0.0, v_out0 + 0.5 * dt * k2_vout),
            d,
            irradiance,
            temperature_c,
        )

        # Stage 4
        k4_vpv, k4_il, k4_vout = self.derivatives(
            v_pv0 + dt * k3_vpv,
            max(0.0, i_l0 + dt * k3_il),
            max(0.0, v_out0 + dt * k3_vout),
            d,
            irradiance,
            temperature_c,
        )

        # RK4 update
        self.v_pv = max(0.0, v_pv0 + (dt / 6.0) * (k1_vpv + 2.0 * k2_vpv + 2.0 * k3_vpv + k4_vpv))
        self.i_l = max(0.0, i_l0 + (dt / 6.0) * (k1_il + 2.0 * k2_il + 2.0 * k3_il + k4_il))
        self.v_out = max(0.0, v_out0 + (dt / 6.0) * (k1_vout + 2.0 * k2_vout + 2.0 * k3_vout + k4_vout))

        return BoostConverterState(
            v_pv=self.v_pv,
            i_inductor=self.i_l,
            v_out=self.v_out,
            duty_cycle=self.duty_cycle,
        )

    def get_output_power(self) -> float:
        """Converter electrical output power P_out = V_out^2 / R_load."""
        return (self.v_out ** 2.0) / self.params.load_r

    def get_input_power(self, irradiance: float, temperature_c: float) -> float:
        """PV panel electrical input power P_pv = V_pv * I_pv."""
        i_pv = float(self.pv_model.array_current(self.v_pv, irradiance, temperature_c))
        return self.v_pv * i_pv
