"""
Configuration and Physical Constants for Solar PV MPPT Simulation.
Defines module parameters, converter defaults, controller settings,
and physical constants.
"""

from dataclasses import dataclass, field
from typing import Dict, Any


# Physical constants
BOLTZMANN_K: float = 1.380649e-23  # Joules per Kelvin
ELEMENTARY_Q: float = 1.602176634e-19  # Coulombs
T_STC_KELVIN: float = 298.15  # 25 deg C in Kelvin
G_STC: float = 1000.0  # W/m^2 (STC irradiance)
EG_SILICON: float = 1.121  # Bandgap energy of Silicon in eV


@dataclass
class PVModuleParams:
    """Parameters of a single photovoltaic module under Standard Test Conditions (STC)."""
    name: str = "Canadian Solar CS5P-220M"
    n_series_cells: int = 96
    p_mp: float = 220.0       # Maximum power (W)
    v_mp: float = 48.3        # Maximum power voltage (V)
    i_mp: float = 4.55        # Maximum power current (A)
    v_oc: float = 59.2        # Open-circuit voltage (V)
    i_sc: float = 5.09        # Short-circuit current (A)
    alpha_sc: float = 0.0034  # Temp coeff of Isc (A/K) [+0.065%/K]
    beta_voc: float = -0.198  # Temp coeff of Voc (V/K) [-0.334%/K]
    r_s: float = 0.75         # Series resistance (Ohms)
    r_sh: float = 450.0       # Shunt resistance at STC (Ohms)
    ideality_n: float = 1.00  # Diode ideality factor
    i_0_ref: float = 3.5e-10  # Reverse saturation current at STC (A)


@dataclass
class PVArrayConfig:
    """PV Array grouping configuration."""
    module_params: PVModuleParams = field(default_factory=PVModuleParams)
    n_modules_series: int = 1
    n_strings_parallel: int = 1

    @property
    def total_modules(self) -> int:
        return self.n_modules_series * self.n_strings_parallel


@dataclass
class BoostConverterParams:
    """Averaged continuous-conduction DC-DC Boost Converter parameters."""
    inductance_l: float = 2.5e-3          # Inductor (Henry)
    inductor_r: float = 0.05             # Parasitic series resistance (Ohms)
    c_pv: float = 220e-6                 # PV input terminal capacitor (Farad)
    c_out: float = 470e-6                # Output capacitor (Farad)
    load_r: float = 30.0                 # Load resistance (Ohms)
    initial_d: float = 0.30              # Initial duty cycle
    initial_v_pv: float = 45.0           # Initial PV voltage (V)
    initial_i_l: float = 2.0             # Initial inductor current (A)
    initial_v_out: float = 60.0          # Initial output voltage (V)


@dataclass
class FuzzyControllerParams:
    """Fuzzy Logic Controller tuning parameters."""
    ke: float = 10.0                     # Error normalization factor: E_norm = E / ke
    kce: float = 100.0                   # Change in error normalization factor: CE_norm = CE / kce
    k_delta_d: float = 0.015             # Output duty cycle adjustment scaling: Delta_D = k_delta_d * out_norm
    d_min: float = 0.05                  # Minimum duty cycle limit
    d_max: float = 0.90                  # Maximum duty cycle limit
    sampling_time: float = 0.005         # Controller sampling period (seconds, e.g. 5 ms)
    deadband_v: float = 1e-4             # Deadband threshold for delta V to prevent division by zero


@dataclass
class POControllerParams:
    """Perturb & Observe Controller parameters."""
    delta_d_step: float = 0.008          # Fixed perturbation step size
    d_min: float = 0.05                  # Minimum duty cycle
    d_max: float = 0.90                  # Maximum duty cycle
    sampling_time: float = 0.005         # Controller sampling period (seconds)
    power_tolerance: float = 0.01        # Minimum power delta to trigger perturbation (W)


@dataclass
class SimulationConfig:
    """Numerical Simulation timing and settings."""
    duration: float = 0.5                # Total duration (seconds)
    time_step: float = 5e-5              # Converter ODE numerical time step dt (seconds)
    irradiance_initial: float = 1000.0   # Default STC irradiance (W/m^2)
    temperature_initial: float = 25.0    # Default STC cell temperature (deg C)


# Available preset modules
PRESET_MODULES: Dict[str, PVModuleParams] = {
    "Canadian Solar CS5P-220M": PVModuleParams(
        name="Canadian Solar CS5P-220M",
        n_series_cells=96,
        p_mp=220.0,
        v_mp=48.3,
        i_mp=4.55,
        v_oc=59.2,
        i_sc=5.09,
        alpha_sc=0.0034,
        beta_voc=-0.198,
        r_s=0.77,
        r_sh=450.0,
        ideality_n=1.05,
        i_0_ref=2.1e-10,
    ),
    "Kyocera KC200GT": PVModuleParams(
        name="Kyocera KC200GT",
        n_series_cells=54,
        p_mp=200.0,
        v_mp=26.3,
        i_mp=7.61,
        v_oc=32.9,
        i_sc=8.21,
        alpha_sc=0.00318,
        beta_voc=-0.123,
        r_s=0.22,
        r_sh=250.0,
        ideality_n=1.10,
        i_0_ref=1.5e-9,
    ),
    "SunPower SPR-305-WHT": PVModuleParams(
        name="SunPower SPR-305-WHT",
        n_series_cells=96,
        p_mp=305.0,
        v_mp=54.7,
        i_mp=5.58,
        v_oc=64.2,
        i_sc=5.96,
        alpha_sc=0.0035,
        beta_voc=-0.177,
        r_s=0.58,
        r_sh=600.0,
        ideality_n=1.08,
        i_0_ref=1.2e-10,
    ),
}
