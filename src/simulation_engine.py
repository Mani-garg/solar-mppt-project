"""
Simulation Engine for Solar PV System with Boost Converter and MPPT Controllers.
Coordinates multi-rate discrete-continuous numerical simulation, independent theoretical
MPP reference tracking, and performance data collection.
"""

from typing import Union, Optional, Dict, Tuple
import numpy as np
import pandas as pd

from src.config import (
    SimulationConfig,
    PVArrayConfig,
    BoostConverterParams,
    FuzzyControllerParams,
    POControllerParams,
)
from src.pv_model import SingleDiodePVModel, MPPResult
from src.boost_converter import BoostConverterModel
from src.fuzzy_controller import FuzzyMPPTController
from src.po_controller import POController
from src.environmental_profiles import EnvironmentalProfile


class SimulationEngine:
    """
    Coordinates numerical integration between the continuous-conduction
    boost converter dynamics and discrete-time MPPT controllers.
    """

    def __init__(
        self,
        pv_model: SingleDiodePVModel,
        converter: BoostConverterModel,
        profile: EnvironmentalProfile,
        sim_config: SimulationConfig = SimulationConfig(),
    ):
        self.pv_model = pv_model
        self.converter = converter
        self.profile = profile
        self.config = sim_config

    def run(
        self,
        controller: Union[FuzzyMPPTController, POController, str],
        controller_sampling_time: float = 0.005,
        downsample_factor: int = 1,
    ) -> pd.DataFrame:
        """
        Execute full time-domain simulation.

        Parameters:
          controller: Initialized FuzzyMPPTController, POController, or string 'fuzzy' / 'po'
          controller_sampling_time: Sampling period Ts for the controller (seconds)
          downsample_factor: Integer decimation factor for logged output points (1 = full log)

        Returns:
          pandas.DataFrame containing time-series simulation telemetry.
        """
        # Determine controller instance
        ctrl_type = ""
        if isinstance(controller, str):
            if controller.lower().startswith("fuzz"):
                ctrl_obj: Union[FuzzyMPPTController, POController] = FuzzyMPPTController()
                ctrl_type = "Fuzzy Logic MPPT"
            else:
                ctrl_obj = POController()
                ctrl_type = "P&O MPPT"
        else:
            ctrl_obj = controller
            ctrl_type = "Fuzzy Logic MPPT" if isinstance(controller, FuzzyMPPTController) else "P&O MPPT"

        # Reset converter and controller
        self.converter.reset()
        ctrl_obj.reset(initial_d=self.converter.duty_cycle)

        # Time parameters
        duration = self.config.duration
        dt = self.config.time_step
        total_steps = int(np.ceil(duration / dt))
        steps_per_ctrl = max(1, int(round(controller_sampling_time / dt)))

        # Cache reference MPP results for unique (G, T) to accelerate simulation
        mpp_cache: Dict[Tuple[float, float], MPPResult] = {}

        def get_cached_mpp(g_val: float, t_val: float) -> MPPResult:
            key = (round(g_val, 2), round(t_val, 2))
            if key not in mpp_cache:
                mpp_cache[key] = self.pv_model.compute_reference_mpp(key[0], key[1])
            return mpp_cache[key]

        # Pre-allocate output arrays
        logged_steps = int(np.ceil(total_steps / downsample_factor))
        times = np.zeros(logged_steps)
        irradiances = np.zeros(logged_steps)
        temperatures = np.zeros(logged_steps)
        v_pv_arr = np.zeros(logged_steps)
        i_pv_arr = np.zeros(logged_steps)
        p_pv_arr = np.zeros(logged_steps)
        v_mpp_arr = np.zeros(logged_steps)
        i_mpp_arr = np.zeros(logged_steps)
        p_mpp_arr = np.zeros(logged_steps)
        duty_arr = np.zeros(logged_steps)
        v_out_arr = np.zeros(logged_steps)
        i_l_arr = np.zeros(logged_steps)
        p_out_arr = np.zeros(logged_steps)
        delta_d_arr = np.zeros(logged_steps)
        eff_arr = np.zeros(logged_steps)

        log_idx = 0
        curr_delta_d = 0.0

        for step_i in range(total_steps):
            t = step_i * dt
            env = self.profile.get_condition(t)
            g_curr = env.irradiance
            t_curr = env.temperature_c

            # Sensed PV operating point
            v_curr = self.converter.v_pv
            i_curr = float(self.pv_model.array_current(v_curr, g_curr, t_curr))
            p_curr = v_curr * i_curr

            # Controller sampling execution
            if step_i % steps_per_ctrl == 0:
                new_d, rec = ctrl_obj.step(v_curr, p_curr)
                self.converter.set_duty_cycle(new_d)
                curr_delta_d = getattr(rec, "delta_d", 0.0)

            # Theoretical reference MPP under current conditions
            mpp_ref = get_cached_mpp(g_curr, t_curr)

            # Log data
            if step_i % downsample_factor == 0 and log_idx < logged_steps:
                times[log_idx] = t
                irradiances[log_idx] = g_curr
                temperatures[log_idx] = t_curr
                v_pv_arr[log_idx] = v_curr
                i_pv_arr[log_idx] = i_curr
                p_pv_arr[log_idx] = p_curr
                v_mpp_arr[log_idx] = mpp_ref.v_mpp
                i_mpp_arr[log_idx] = mpp_ref.i_mpp
                p_mpp_arr[log_idx] = mpp_ref.p_mpp
                duty_arr[log_idx] = self.converter.duty_cycle
                v_out_arr[log_idx] = self.converter.v_out
                i_l_arr[log_idx] = self.converter.i_l
                p_out_arr[log_idx] = self.converter.get_output_power()
                delta_d_arr[log_idx] = curr_delta_d

                # Instantaneous tracking efficiency (%)
                inst_eff = (p_curr / mpp_ref.p_mpp * 100.0) if mpp_ref.p_mpp > 1e-3 else 0.0
                eff_arr[log_idx] = min(105.0, max(0.0, inst_eff))

                log_idx += 1

            # Advance continuous converter dynamics with RK4
            self.converter.step_rk4(dt, g_curr, t_curr)

        # Trim in case logged_steps exceeded
        valid = log_idx
        df = pd.DataFrame({
            "time": times[:valid],
            "irradiance": irradiances[:valid],
            "temperature": temperatures[:valid],
            "v_pv": v_pv_arr[:valid],
            "i_pv": i_pv_arr[:valid],
            "p_pv": p_pv_arr[:valid],
            "v_mpp_ref": v_mpp_arr[:valid],
            "i_mpp_ref": i_mpp_arr[:valid],
            "p_mpp_ref": p_mpp_arr[:valid],
            "duty_cycle": duty_arr[:valid],
            "v_out": v_out_arr[:valid],
            "i_inductor": i_l_arr[:valid],
            "p_out": p_out_arr[:valid],
            "delta_d": delta_d_arr[:valid],
            "instantaneous_efficiency": eff_arr[:valid],
            "controller_type": ctrl_type,
        })

        return df
