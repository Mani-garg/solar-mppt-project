"""
Environmental Scenarios and Dynamic Profiles for Solar PV MPPT Simulation.
Provides standard IEEE / academic benchmark irradiance and temperature test profiles
as well as customizable user schedules.
"""

from dataclasses import dataclass, field
from typing import Callable, List, Tuple
import numpy as np


@dataclass
class EnvironmentalCondition:
    """Instantaneous environmental condition."""
    irradiance: float    # W/m^2
    temperature_c: float # deg C


@dataclass
class ProfileTransition:
    """Step transition timestamp and target conditions."""
    time: float
    irradiance: float
    temperature_c: float


class EnvironmentalProfile:
    """
    Environmental profile generator producing G(t) and T(t) throughout
    the simulation duration.
    """

    def __init__(
        self,
        name: str,
        description: str,
        generator_fn: Callable[[float], EnvironmentalCondition],
        transition_times: List[float] = field(default_factory=list),
    ):
        self.name = name
        self.description = description
        self.generator_fn = generator_fn
        self.transition_times = transition_times

    def get_condition(self, t: float) -> EnvironmentalCondition:
        """Evaluate G and T at time t."""
        return self.generator_fn(t)

    @classmethod
    def scenario_a_constant(
        cls, g: float = 1000.0, t_c: float = 25.0
    ) -> "EnvironmentalProfile":
        """Scenario A: Constant Standard Irradiance and Temperature."""
        return cls(
            name="Scenario A: Constant STC",
            description=f"Constant STC: Irradiance = {g} W/m², Temp = {t_c}°C",
            generator_fn=lambda t: EnvironmentalCondition(irradiance=g, temperature_c=t_c),
            transition_times=[],
        )

    @classmethod
    def scenario_b_irradiance_drop(
        cls, t_step: float = 0.25, g1: float = 1000.0, g2: float = 600.0, t_c: float = 25.0
    ) -> "EnvironmentalProfile":
        """Scenario B: Sudden Irradiance Decrease (Cloud shadow)."""
        def fn(t: float) -> EnvironmentalCondition:
            g = g1 if t < t_step else g2
            return EnvironmentalCondition(irradiance=g, temperature_c=t_c)

        return cls(
            name="Scenario B: Sudden Irradiance Drop",
            description=f"Sudden drop from {g1} to {g2} W/m² at t = {t_step:.2f}s",
            generator_fn=fn,
            transition_times=[t_step],
        )

    @classmethod
    def scenario_c_irradiance_rise(
        cls, t_step: float = 0.25, g1: float = 600.0, g2: float = 1000.0, t_c: float = 25.0
    ) -> "EnvironmentalProfile":
        """Scenario C: Sudden Irradiance Increase (Cloud clearing)."""
        def fn(t: float) -> EnvironmentalCondition:
            g = g1 if t < t_step else g2
            return EnvironmentalCondition(irradiance=g, temperature_c=t_c)

        return cls(
            name="Scenario C: Sudden Irradiance Rise",
            description=f"Sudden rise from {g1} to {g2} W/m² at t = {t_step:.2f}s",
            generator_fn=fn,
            transition_times=[t_step],
        )

    @classmethod
    def scenario_d_temperature_rise(
        cls, t_step: float = 0.25, g: float = 1000.0, t1: float = 25.0, t2: float = 45.0
    ) -> "EnvironmentalProfile":
        """Scenario D: Cell Temperature Heating Rise."""
        def fn(t: float) -> EnvironmentalCondition:
            temp = t1 if t < t_step else t2
            return EnvironmentalCondition(irradiance=g, temperature_c=temp)

        return cls(
            name="Scenario D: Temperature Rise",
            description=f"Temperature rise from {t1}°C to {t2}°C at t = {t_step:.2f}s",
            generator_fn=fn,
            transition_times=[t_step],
        )

    @classmethod
    def scenario_e_multiple_changes(
        cls, total_duration: float = 0.6
    ) -> "EnvironmentalProfile":
        """Scenario E: Complex dynamic conditions with multiple transitions."""
        t1 = 0.20 * total_duration
        t2 = 0.50 * total_duration
        t3 = 0.75 * total_duration

        def fn(t: float) -> EnvironmentalCondition:
            if t < t1:
                return EnvironmentalCondition(1000.0, 25.0)
            elif t < t2:
                return EnvironmentalCondition(650.0, 32.0)
            elif t < t3:
                return EnvironmentalCondition(850.0, 42.0)
            else:
                return EnvironmentalCondition(1000.0, 30.0)

        return cls(
            name="Scenario E: Multiple Dynamic Changes",
            description="Multi-step dynamic variations in both irradiance and cell temperature",
            generator_fn=fn,
            transition_times=[t1, t2, t3],
        )

    @classmethod
    def custom_profile(
        cls, transitions: List[ProfileTransition], default_g: float = 1000.0, default_t: float = 25.0
    ) -> "EnvironmentalProfile":
        """Custom user-defined profile based on sorted transition schedule."""
        sorted_trans = sorted(transitions, key=lambda x: x.time)
        transition_times = [tr.time for tr in sorted_trans]

        def fn(t: float) -> EnvironmentalCondition:
            current_g = default_g
            current_t = default_t
            for tr in sorted_trans:
                if t >= tr.time:
                    current_g = tr.irradiance
                    current_t = tr.temperature_c
                else:
                    break
            return EnvironmentalCondition(current_g, current_t)

        return cls(
            name="Custom Profile",
            description="User-defined custom environmental step schedule",
            generator_fn=fn,
            transition_times=transition_times,
        )


def get_available_profiles(duration: float = 0.5) -> dict:
    """Helper to return dict of standard profile instances keyed by scenario id."""
    t_mid = 0.5 * duration
    return {
        "A": EnvironmentalProfile.scenario_a_constant(),
        "B": EnvironmentalProfile.scenario_b_irradiance_drop(t_step=t_mid),
        "C": EnvironmentalProfile.scenario_c_irradiance_rise(t_step=t_mid),
        "D": EnvironmentalProfile.scenario_d_temperature_rise(t_step=t_mid),
        "E": EnvironmentalProfile.scenario_e_multiple_changes(total_duration=duration),
    }
