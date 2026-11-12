# Intelligent Fuzzy Logic MPPT Controller Design

## 1. Control Philosophy & Architecture
The Maximum Power Point Tracking (MPPT) controller regulates the pulse-width duty cycle $D \in [D_{min}, D_{max}]$ of a DC-DC boost converter. The controller continuously shifts the operating point along the $P-V$ characteristic curve toward the optimal condition where:

$$\frac{dP}{dV} = 0$$

Unlike conventional fixed-step methods, the Fuzzy Logic Controller (FLC) adapts its step size non-linearly:
- **Large step size:** Dispatched when far from the MPP, providing fast dynamic tracking during irradiance steps.
- **Micro-fine step size:** Dispatched near the peak, eliminating limit-cycle oscillations at steady state.

---

## 2. Controller Inputs & Fuzzification
The FLC processes two normalized continuous input variables:

### 2.1 Error $E(k)$
Measures the local derivative slope of the power-voltage curve:
$$E(k) = \frac{P(k) - P(k-1)}{V(k) - V(k-1)}$$
*Protection:* A voltage deadband $\epsilon = 10^{-4}\ \text{V}$ is applied. If $|V(k) - V(k-1)| < \epsilon$, $E(k) = 0$.

### 2.2 Change in Error $CE(k)$
Measures the trend and rate-of-change of the slope:
$$CE(k) = E(k) - E(k-1)$$

### 2.3 Input Normalization
Inputs are scaled into the universal discourse universe $[-1, 1]$:
$$E_N(k) = \text{clip}\left(\frac{E(k)}{K_E}, -1.0, 1.0\right)$$
$$CE_N(k) = \text{clip}\left(\frac{CE(k)}{K_{CE}}, -1.0, 1.0\right)$$

Where $K_E = 10.0$ and $K_{CE} = 100.0$ are tuning gains.

---

## 3. Linguistic Membership Functions
Five linguistic fuzzy levels are assigned across both inputs and output:
1. **NB:** Negative Big
2. **NS:** Negative Small
3. **ZE:** Zero
4. **PS:** Positive Small
5. **PB:** Positive Big

The membership functions follow a standard Ruspini partition over $[-1, 1]$:
- **NB:** Trapezoidal $[-1.0, -1.0, -0.5, -0.2]$
- **NS:** Triangular $[-0.5, -0.2, 0.0]$
- **ZE:** Triangular $[-0.2, 0.0, 0.2]$
- **PS:** Triangular $[0.0, 0.2, 0.5]$
- **PB:** Trapezoidal $[0.2, 0.5, 1.0, 1.0]$

At every point $x \in [-1, 1]$, the sum of memberships satisfies the Ruspini partition condition: $\sum_{i} \mu_i(x) = 1.0$.

---

## 4. Converter Coupling & Rule Base Sign Verification
The sign mapping of the fuzzy output must be physically verified with the DC-DC boost converter:

For a boost converter operating in continuous conduction mode connected to a resistive load $R_{load}$:
$$R_{in, avg} \approx (1 - D)^2 R_{load}$$

- **Increasing $D$:** Decreases $(1-D) \implies$ Decreases input resistance $R_{in} \implies$ Increases inductor current $i_L \implies$ **Decreases PV terminal voltage $V_{pv}$**.
- **Decreasing $D$:** Increases $(1-D) \implies$ Increases input resistance $R_{in} \implies$ Decreases inductor current $i_L \implies$ **Increases PV terminal voltage $V_{pv}$**.

### Physical Direction Check:
1. **Left of MPP ($V < V_{mpp}$):**
   $E = dP/dV > 0$. The PV voltage is too low. To increase $V_{pv}$ toward $V_{mpp}$, duty cycle $D$ must **decrease** ($\Delta D < 0$, Negative).
2. **Right of MPP ($V > V_{mpp}$):**
   $E = dP/dV < 0$. The PV voltage is too high. To decrease $V_{pv}$ toward $V_{mpp}$, duty cycle $D$ must **increase** ($\Delta D > 0$, Positive).

### 5x5 Mamdani Rule Base Table
| Error $E$ \ $CE$ | **NB** | **NS** | **ZE** | **PS** | **PB** |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **NB** ($V \gg V_{mp}$) | **PB** | **PB** | **PB** | **PS** | **ZE** |
| **NS** ($V > V_{mp}$)    | **PB** | **PS** | **PS** | **ZE** | **NS** |
| **ZE** ($V \approx V_{mp}$) | **PS** | **PS** | **ZE** | **NS** | **NS** |
| **PS** ($V < V_{mp}$)    | **PS** | **ZE** | **NS** | **NS** | **NB** |
| **PB** ($V \ll V_{mp}$) | **ZE** | **NS** | **NB** | **NB** | **NB** |

---

## 5. Mamdani Inference & Centroid Defuzzification
The degree of fulfillment (firing strength) of each rule $r$ is:
$$\alpha_r = \min\left( \mu_E^r(E_N), \mu_{CE}^r(CE_N) \right)$$

The aggregated output fuzzy set $\mu_{agg}(y)$ across all 25 rules is:
$$\mu_{agg}(y) = \max_{r=1}^{25} \left( \min\left( \alpha_r, \mu_{\Delta D}^r(y) \right) \right)$$

The crisp normalized duty adjustment is calculated using center of gravity (centroid):
$$\Delta D_N = \frac{\int_{-1}^1 y \cdot \mu_{agg}(y) dy}{\int_{-1}^1 \mu_{agg}(y) dy}$$

The final saturated duty cycle command is:
$$\Delta D = K_{\Delta D} \cdot \Delta D_N$$
$$D(k+1) = \text{clip}\left( D(k) + \Delta D, D_{min}, D_{max} \right)$$
