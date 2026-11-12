"""
Fuzzy Logic MPPT Controller for Solar Photovoltaic Systems.
Implements a 2-input, 1-output Mamdani Fuzzy Inference System (FIS)
with triangular/trapezoidal membership functions and centroid defuzzification.
"""

from dataclasses import dataclass
from typing import Tuple, Dict, Any, Optional
import numpy as np
import skfuzzy as fuzz

try:
    from skfuzzy import control as ctrl
    HAS_SKFUZZY_CONTROL = True
except (ImportError, ModuleNotFoundError):
    ctrl = None
    HAS_SKFUZZY_CONTROL = False

from src.config import FuzzyControllerParams


@dataclass
class FuzzyStepRecord:
    """Audit log of a single Fuzzy controller step."""
    e_raw: float
    ce_raw: float
    e_norm: float
    ce_norm: float
    delta_d_norm: float
    delta_d: float
    duty_cycle: float


class FuzzyMPPTController:
    """
    Intelligent Mamdani Fuzzy Logic Controller (FLC) for MPPT.

    Inputs:
      - Error E: dP/dV = (P(k) - P(k-1)) / (V(k) - V(k-1))
      - Change of Error CE: E(k) - E(k-1)

    Output:
      - Delta D: Duty cycle perturbation step

    Physical Converter Relationship:
      - Increasing duty cycle D increases inductor current and decreases PV voltage.
      - Therefore, when E > 0 (V < Vmpp), duty cycle must DECREASE (Delta D < 0).
      - When E < 0 (V > Vmpp), duty cycle must INCREASE (Delta D > 0).
    """

    # Linguistic terms
    TERMS = ["NB", "NS", "ZE", "PS", "PB"]

    def __init__(self, params: FuzzyControllerParams = FuzzyControllerParams()):
        self.params = params
        self.duty_cycle = float(0.30)
        self.prev_v: Optional[float] = None
        self.prev_p: Optional[float] = None
        self.prev_e: float = 0.0

        # Universe of discourse for normalized variables [-1, 1]
        self.universe = np.linspace(-1.0, 1.0, 201)

        # Build skfuzzy ControlSystem and fast analytical evaluator
        self._build_skfuzzy_system()

    def reset(self, initial_d: float = 0.30) -> None:
        """Reset controller internal state for a new simulation run."""
        self.duty_cycle = float(np.clip(initial_d, self.params.d_min, self.params.d_max))
        self.prev_v = None
        self.prev_p = None
        self.prev_e = 0.0

    def _build_skfuzzy_system(self) -> None:
        """Construct Mamdani FIS using scikit-fuzzy and local analytical arrays."""
        # Standalone output membership functions evaluated on universe
        self.output_mfs = {
            "NB": fuzz.trapmf(self.universe, [-1.0, -1.0, -0.5, -0.2]),
            "NS": fuzz.trimf(self.universe, [-0.5, -0.2, 0.0]),
            "ZE": fuzz.trimf(self.universe, [-0.2, 0.0, 0.2]),
            "PS": fuzz.trimf(self.universe, [0.0, 0.2, 0.5]),
            "PB": fuzz.trapmf(self.universe, [0.2, 0.5, 1.0, 1.0]),
        }

        # 5x5 Fuzzy Rule Base Matrix: [Row = E, Col = CE] -> Output Delta D
        self.rule_matrix = {
            # E == NB (V >> Vmpp)
            ("NB", "NB"): "PB",
            ("NB", "NS"): "PB",
            ("NB", "ZE"): "PB",
            ("NB", "PS"): "PS",
            ("NB", "PB"): "ZE",
            # E == NS (V > Vmpp)
            ("NS", "NB"): "PB",
            ("NS", "NS"): "PS",
            ("NS", "ZE"): "PS",
            ("NS", "PS"): "ZE",
            ("NS", "PB"): "NS",
            # E == ZE (V ~ Vmpp)
            ("ZE", "NB"): "PS",
            ("ZE", "NS"): "PS",
            ("ZE", "ZE"): "ZE",
            ("ZE", "PS"): "NS",
            ("ZE", "PB"): "NS",
            # E == PS (V < Vmpp)
            ("PS", "NB"): "PS",
            ("PS", "NS"): "ZE",
            ("PS", "ZE"): "NS",
            ("PS", "PS"): "NS",
            ("PS", "PB"): "NB",
            # E == PB (V << Vmpp)
            ("PB", "NB"): "ZE",
            ("PB", "NS"): "NS",
            ("PB", "ZE"): "NB",
            ("PB", "PS"): "NB",
            ("PB", "PB"): "NB",
        }

        # Optional scikit-fuzzy control system construction (if networkx available)
        self.control_system = None
        self.sim = None
        if HAS_SKFUZZY_CONTROL and ctrl is not None:
            try:
                self.var_e = ctrl.Antecedent(self.universe, "Error")
                self.var_ce = ctrl.Antecedent(self.universe, "ChangeInError")
                self.var_out = ctrl.Consequent(self.universe, "DeltaD")

                for term, mf_arr in self.output_mfs.items():
                    if term in ["NB", "PB"]:
                        bounds = [-1.0, -1.0, -0.5, -0.2] if term == "NB" else [0.2, 0.5, 1.0, 1.0]
                        self.var_e[term] = fuzz.trapmf(self.universe, bounds)
                        self.var_ce[term] = fuzz.trapmf(self.universe, bounds)
                        self.var_out[term] = fuzz.trapmf(self.universe, bounds)
                    else:
                        bounds = [-0.5, -0.2, 0.0] if term == "NS" else ([-0.2, 0.0, 0.2] if term == "ZE" else [0.0, 0.2, 0.5])
                        self.var_e[term] = fuzz.trimf(self.universe, bounds)
                        self.var_ce[term] = fuzz.trimf(self.universe, bounds)
                        self.var_out[term] = fuzz.trimf(self.universe, bounds)

                self.var_out.defuzzify_method = "centroid"
                rules = []
                for (e_term, ce_term), out_term in self.rule_matrix.items():
                    rules.append(ctrl.Rule(self.var_e[e_term] & self.var_ce[ce_term], self.var_out[out_term]))
                self.control_system = ctrl.ControlSystem(rules)
                self.sim = ctrl.ControlSystemSimulation(self.control_system)
            except Exception:
                self.sim = None

    def compute_membership(self, val: float) -> Dict[str, float]:
        """Compute degree of membership for a scalar in [-1, 1] across all 5 terms."""
        v = float(np.clip(val, -1.0, 1.0))
        m = {}
        # NB: trapezoid [-1.0, -1.0, -0.5, -0.2]
        if v <= -0.5:
            m["NB"] = 1.0
        elif v < -0.2:
            m["NB"] = (-0.2 - v) / 0.3
        else:
            m["NB"] = 0.0

        # NS: triangle [-0.5, -0.2, 0.0]
        if -0.5 <= v <= -0.2:
            m["NS"] = (v + 0.5) / 0.3
        elif -0.2 < v <= 0.0:
            m["NS"] = (-v) / 0.2
        else:
            m["NS"] = 0.0

        # ZE: triangle [-0.2, 0.0, 0.2]
        if -0.2 <= v <= 0.0:
            m["ZE"] = (v + 0.2) / 0.2
        elif 0.0 < v <= 0.2:
            m["ZE"] = (0.2 - v) / 0.2
        else:
            m["ZE"] = 0.0

        # PS: triangle [0.0, 0.2, 0.5]
        if 0.0 <= v <= 0.2:
            m["PS"] = v / 0.2
        elif 0.2 < v <= 0.5:
            m["PS"] = (0.5 - v) / 0.3
        else:
            m["PS"] = 0.0

        # PB: trapezoid [0.2, 0.5, 1.0, 1.0]
        if v >= 0.5:
            m["PB"] = 1.0
        elif v > 0.2:
            m["PB"] = (v - 0.2) / 0.3
        else:
            m["PB"] = 0.0

        return m

    def evaluate_fuzzy_analytical(self, e_norm: float, ce_norm: float) -> float:
        """
        High-performance vectorized analytical Mamdani Centroid defuzzifier.
        Evaluates the identical 5x5 min-max Mamdani inference with high precision.
        """
        mu_e = self.compute_membership(e_norm)
        mu_ce = self.compute_membership(ce_norm)

        # Aggregate rule firing strengths for each output term
        out_strengths = {"NB": 0.0, "NS": 0.0, "ZE": 0.0, "PS": 0.0, "PB": 0.0}

        for (e_term, ce_term), out_term in self.rule_matrix.items():
            firing = min(mu_e[e_term], mu_ce[ce_term])
            if firing > out_strengths[out_term]:
                out_strengths[out_term] = firing

        # If zero firing everywhere (dead zone), output is 0.0
        if sum(out_strengths.values()) < 1e-6:
            return 0.0

        # Discretize output universe and aggregate output fuzzy set
        # mu_agg(y) = max_i ( min(out_strengths[i], mu_out_i(y)) )
        y = self.universe
        mu_agg = np.zeros_like(y)

        # Output term membership vectors on self.universe
        for term, strength in out_strengths.items():
            if strength > 0.0:
                # Clip membership function at firing strength
                term_mf = self.output_mfs[term]
                clipped = np.minimum(strength, term_mf)
                mu_agg = np.maximum(mu_agg, clipped)

        # Centroid defuzzification: int(y * mu) / int(mu)
        denom = np.sum(mu_agg)
        if denom < 1e-9:
            return 0.0
        return float(np.sum(y * mu_agg) / denom)

    def evaluate(self, e_norm: float, ce_norm: float, use_skfuzzy: bool = False) -> float:
        """
        Evaluate fuzzy inference for normalized inputs [-1, 1].
        Returns normalized duty cycle adjustment in [-1, 1].
        """
        e_n = float(np.clip(e_norm, -1.0, 1.0))
        ce_n = float(np.clip(ce_norm, -1.0, 1.0))

        if use_skfuzzy:
            try:
                self.sim.input["Error"] = e_n
                self.sim.input["ChangeInError"] = ce_n
                self.sim.compute()
                return float(self.sim.output["DeltaD"])
            except Exception:
                pass

        return self.evaluate_fuzzy_analytical(e_n, ce_n)

    def step(self, v_pv: float, p_pv: float) -> Tuple[float, FuzzyStepRecord]:
        """
        Execute one controller sampling step.

        Parameters:
          v_pv: Current PV voltage (V)
          p_pv: Current PV power (W)

        Returns:
          Updated duty cycle D, and detailed step audit record.
        """
        v = float(v_pv)
        p = float(p_pv)

        # Initial sample setup
        if self.prev_v is None or self.prev_p is None:
            self.prev_v = v
            self.prev_p = p
            self.prev_e = 0.0
            record = FuzzyStepRecord(
                e_raw=0.0,
                ce_raw=0.0,
                e_norm=0.0,
                ce_norm=0.0,
                delta_d_norm=0.0,
                delta_d=0.0,
                duty_cycle=self.duty_cycle,
            )
            return self.duty_cycle, record

        # Error computation: E = dP/dV
        delta_v = v - self.prev_v
        delta_p = p - self.prev_p

        if abs(delta_v) < self.params.deadband_v:
            e_raw = 0.0
        else:
            e_raw = delta_p / delta_v

        # Prevent runaway derivative if delta_v is very small
        e_raw = float(np.clip(e_raw, -100.0, 100.0))

        # Change in error: CE = E(k) - E(k-1)
        ce_raw = e_raw - self.prev_e

        # Normalization
        e_norm = float(np.clip(e_raw / self.params.ke, -1.0, 1.0))
        ce_norm = float(np.clip(ce_raw / self.params.kce, -1.0, 1.0))

        # Fuzzy evaluation
        delta_d_norm = self.evaluate(e_norm, ce_norm)

        # Scale duty cycle adjustment
        delta_d = self.params.k_delta_d * delta_d_norm

        # Update and saturate duty cycle
        new_d = float(np.clip(
            self.duty_cycle + delta_d,
            self.params.d_min,
            self.params.d_max
        ))

        self.duty_cycle = new_d
        self.prev_v = v
        self.prev_p = p
        self.prev_e = e_raw

        record = FuzzyStepRecord(
            e_raw=e_raw,
            ce_raw=ce_raw,
            e_norm=e_norm,
            ce_norm=ce_norm,
            delta_d_norm=delta_d_norm,
            delta_d=delta_d,
            duty_cycle=self.duty_cycle,
        )
        return self.duty_cycle, record
