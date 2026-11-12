"""
Conventional Perturb and Observe (P&O) MPPT Controller.
Baseline classical MPPT benchmark for comparison against Fuzzy Logic MPPT.
"""

from dataclasses import dataclass
from typing import Tuple, Optional
import numpy as np

from src.config import POControllerParams


@dataclass
class POStepRecord:
    """Audit log of a single P&O controller step."""
    delta_v: float
    delta_p: float
    perturbation_direction: int  # +1 (increase D), -1 (decrease D), 0 (none)
    delta_d: float
    duty_cycle: float


class POController:
    """
    Conventional Perturb & Observe (P&O) MPPT Controller.

    Coupling to Boost Converter:
      - Increasing duty cycle D decreases PV terminal voltage V_pv.
      - Decreasing duty cycle D increases PV terminal voltage V_pv.

    Logic:
      If Delta P > 0:
        If Delta V > 0 -> Voltage is moving toward MPP from left. Decrease D to keep increasing V.
        If Delta V < 0 -> Voltage is moving toward MPP from right. Increase D to keep decreasing V.
      If Delta P < 0:
        If Delta V > 0 -> Voltage moved past MPP to the right. Reverse direction: Increase D.
        If Delta V < 0 -> Voltage moved past MPP to the left. Reverse direction: Decrease D.
    """

    def __init__(self, params: POControllerParams = POControllerParams()):
        self.params = params
        self.duty_cycle = float(0.30)
        self.prev_v: Optional[float] = None
        self.prev_p: Optional[float] = None
        self.last_direction: int = -1  # Default initial search direction

    def reset(self, initial_d: float = 0.30) -> None:
        """Reset internal state."""
        self.duty_cycle = float(np.clip(initial_d, self.params.d_min, self.params.d_max))
        self.prev_v = None
        self.prev_p = None
        self.last_direction = -1

    def step(self, v_pv: float, p_pv: float) -> Tuple[float, POStepRecord]:
        """
        Execute one P&O control step based on measured PV voltage and power.
        """
        v = float(v_pv)
        p = float(p_pv)

        if self.prev_v is None or self.prev_p is None:
            self.prev_v = v
            self.prev_p = p
            record = POStepRecord(
                delta_v=0.0,
                delta_p=0.0,
                perturbation_direction=0,
                delta_d=0.0,
                duty_cycle=self.duty_cycle,
            )
            return self.duty_cycle, record

        delta_v = v - self.prev_v
        delta_p = p - self.prev_p

        # Check if power change is significant beyond tolerance
        if abs(delta_p) < self.params.power_tolerance:
            direction = 0
            delta_d = 0.0
        else:
            if delta_p > 0.0:
                # Power increased
                if delta_v > 0.0:
                    # Increasing V increased P -> need to keep increasing V -> decrease D
                    direction = -1
                else:
                    # Decreasing V increased P -> need to keep decreasing V -> increase D
                    direction = +1
            else:
                # Power decreased
                if delta_v > 0.0:
                    # Increasing V decreased P -> reversed past MPP -> decrease V -> increase D
                    direction = +1
                else:
                    # Decreasing V decreased P -> reversed past MPP -> increase V -> decrease D
                    direction = -1

            delta_d = float(direction) * self.params.delta_d_step
            self.last_direction = direction

        # Update and clip duty cycle
        new_d = float(np.clip(
            self.duty_cycle + delta_d,
            self.params.d_min,
            self.params.d_max
        ))

        self.duty_cycle = new_d
        self.prev_v = v
        self.prev_p = p

        record = POStepRecord(
            delta_v=delta_v,
            delta_p=delta_p,
            perturbation_direction=direction,
            delta_d=delta_d,
            duty_cycle=self.duty_cycle,
        )
        return self.duty_cycle, record
