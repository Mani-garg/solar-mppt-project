"""
Input Validation and Physical Consistency Checks for MPPT System.
Verifies electrical limits, bounds, and physical consistency to prevent numerical instability.
"""

from dataclasses import dataclass, field
from typing import List, Tuple
from src.config import (
    PVArrayConfig,
    BoostConverterParams,
    FuzzyControllerParams,
    POControllerParams,
    SimulationConfig,
)


@dataclass
class ValidationReport:
    """Audit report for configuration parameters."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def validate_pv_config(config: PVArrayConfig) -> ValidationReport:
    """Validate PV array configuration."""
    errors = []
    warnings = []

    if config.n_modules_series < 1:
        errors.append(f"Number of series modules must be >= 1 (got {config.n_modules_series})")
    elif config.n_modules_series > 50:
        warnings.append(f"High number of series modules ({config.n_modules_series}) may exceed typical DC string limits.")

    if config.n_strings_parallel < 1:
        errors.append(f"Number of parallel strings must be >= 1 (got {config.n_strings_parallel})")
    elif config.n_strings_parallel > 50:
        warnings.append(f"High number of parallel strings ({config.n_strings_parallel}) produces high array current.")

    mod = config.module_params
    if mod.p_mp <= 0:
        errors.append("Module maximum power Pmp must be positive.")
    if mod.v_oc <= 0:
        errors.append("Module open-circuit voltage Voc must be positive.")
    if mod.i_sc <= 0:
        errors.append("Module short-circuit current Isc must be positive.")
    if mod.v_mp >= mod.v_oc:
        errors.append("Maximum power voltage Vmp cannot exceed open-circuit voltage Voc.")
    if mod.i_mp >= mod.i_sc:
        errors.append("Maximum power current Imp cannot exceed short-circuit current Isc.")

    return ValidationReport(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_converter_params(params: BoostConverterParams) -> ValidationReport:
    """Validate DC-DC Boost Converter components."""
    errors = []
    warnings = []

    if params.inductance_l <= 0.0:
        errors.append("Inductance L must be strictly positive.")
    elif params.inductance_l < 1e-4:
        warnings.append("Very small inductance (< 100 µH) may cause high current ripple.")

    if params.c_pv <= 0.0:
        errors.append("PV input capacitance C_pv must be strictly positive.")

    if params.c_out <= 0.0:
        errors.append("Output capacitance C_out must be strictly positive.")

    if params.load_r <= 0.0:
        errors.append("Load resistance R_load must be strictly positive.")

    if not (0.0 < params.initial_d < 1.0):
        errors.append(f"Initial duty cycle must be in (0, 1), got {params.initial_d}")

    return ValidationReport(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_controller_params(
    fuzzy_params: FuzzyControllerParams,
    po_params: POControllerParams,
) -> ValidationReport:
    """Validate MPPT Controller bounds and settings."""
    errors = []
    warnings = []

    # Fuzzy limits
    if not (0.0 < fuzzy_params.d_min < fuzzy_params.d_max < 1.0):
        errors.append("Fuzzy controller duty limits must satisfy 0 < d_min < d_max < 1.")

    if fuzzy_params.ke <= 0.0 or fuzzy_params.kce <= 0.0:
        errors.append("Fuzzy normalization factors (ke, kce) must be strictly positive.")

    if fuzzy_params.k_delta_d <= 0.0:
        errors.append("Fuzzy output scaling factor k_delta_d must be strictly positive.")

    # P&O limits
    if not (0.0 < po_params.d_min < po_params.d_max < 1.0):
        errors.append("P&O duty limits must satisfy 0 < d_min < d_max < 1.")

    if po_params.delta_d_step <= 0.0:
        errors.append("P&O perturbation step delta_d_step must be positive.")
    elif po_params.delta_d_step > 0.10:
        warnings.append("Large P&O step size (> 0.10) may induce violent limit-cycle oscillations.")

    return ValidationReport(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


def validate_simulation_config(
    sim_config: SimulationConfig,
    controller_sampling_time: float,
) -> ValidationReport:
    """Validate simulation duration and time-step stability."""
    errors = []
    warnings = []

    if sim_config.duration <= 0.0:
        errors.append("Simulation duration must be positive.")

    if sim_config.time_step <= 0.0:
        errors.append("Simulation numerical time step dt must be positive.")
    elif sim_config.time_step > 5e-4:
        warnings.append("Time step dt > 500 µs may compromise numerical ODE stability for switching converters.")

    if controller_sampling_time < sim_config.time_step:
        errors.append("Controller sampling time cannot be smaller than numerical integration step dt.")

    return ValidationReport(is_valid=len(errors) == 0, errors=errors, warnings=warnings)
