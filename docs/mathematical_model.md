# Mathematical Modeling of Solar Photovoltaic (PV) Generators

## 1. Semiconductor Physics of Photovoltaic Conversion
A solar cell is an illuminated large-area p-n junction semiconductor device. Incident photons with energy exceeding the semiconductor bandgap ($h\nu \ge E_g$) generate electron-hole pairs. The built-in electric field across the depletion region sweeps the minority carriers across the junction, producing a light-generated photocurrent $I_{ph}$.

---

## 2. Five-Parameter Single-Diode Model
The equivalent electrical circuit of a single-diode photovoltaic generator consists of:
1. A photocurrent source $I_{ph}$ proportional to solar irradiance.
2. A p-n junction diode accounting for non-linear recombination.
3. An internal series resistance $R_s$ representing semiconductor bulk resistivity, metal contact resistance, and interconnects.
4. A parallel shunt resistance $R_{sh}$ modeling structural crystal defects and junction perimeter leakage.

The implicit transcendental relationship governing output terminal current $I$ and voltage $V$ is:

$$I = I_{ph} - I_0 \left[ \exp\left( \frac{V + I R_s}{n N_s V_t} \right) - 1 \right] - \frac{V + I R_s}{R_{sh}}$$

Where:
- $I$: PV terminal output current (A)
- $V$: PV terminal output voltage (V)
- $I_{ph}$: Light-generated photocurrent (A)
- $I_0$: Diode reverse dark saturation current (A)
- $R_s$: Internal series resistance ($\Omega$)
- $R_{sh}$: Shunt leakage resistance ($\Omega$)
- $n$: Diode ideality factor (dimensionless, typically $1.0 \le n \le 1.3$)
- $N_s$: Number of individual solar cells connected in series
- $V_t$: Thermal voltage per cell ($V_t = \frac{k_B T_K}{q}$)

### Physical Constants:
- Boltzmann constant $k_B = 1.380649 \times 10^{-23}\ \text{J/K}$
- Elementary charge $q = 1.602176634 \times 10^{-19}\ \text{C}$
- Standard Test Conditions (STC): $G_{stc} = 1000\ \text{W/m}^2$, $T_{stc} = 25^\circ\text{C} = 298.15\ \text{K}$

---

## 3. Environmental Temperature & Irradiance Dependencies

### 3.1 Photocurrent Dependency:
$$I_{ph}(G, T_K) = \frac{G}{G_{stc}} \left[ I_{sc, stc} + \alpha_{sc} (T_K - T_{stc}) \right]$$
Where $\alpha_{sc}$ is the short-circuit current temperature coefficient ($+0.065\%/^\circ\text{C}$).

### 3.2 Diode Saturation Current Dependency:
$$I_0(T_K) = I_{0, ref} \left( \frac{T_K}{T_{stc}} \right)^3 \exp\left[ \frac{q E_g}{n k_B} \left( \frac{1}{T_{stc}} - \frac{1}{T_K} \right) \right]$$
Where $E_g \approx 1.121\ \text{eV}$ for crystalline Silicon.

### 3.3 Shunt Resistance Scaling:
$$R_{sh}(G) = R_{sh, stc} \left( \frac{G_{stc}}{G} \right)$$

---

## 4. Analytical Solution via Lambert W Function
Because $I$ appears both linearly and within the exponent, classical numerical root-finding (such as Newton-Raphson) can fail or diverge near $V_{oc}$. An exact closed-form analytical solution is achieved through the principal branch of the Lambert W function $W_0(z)$, where $z = W(z) e^{W(z)}$:

Let:
$$\theta = \frac{R_s R_{sh}}{R_s + R_{sh}}$$
$$a = n N_s \frac{k_B T_K}{q}$$
$$z = \frac{\theta I_0}{a} \exp\left( \frac{R_{sh}(V + R_s(I_{ph} + I_0))}{a(R_s + R_{sh})} \right)$$

The exact output current is given by:
$$I(V) = \frac{R_{sh}(I_{ph} + I_0) - V}{R_s + R_{sh}} - \frac{a}{R_s} W_0(z)$$

---

## 5. Maximum Power Point (MPP) Formulation
The power extracted from the PV generator is:
$$P(V) = V \cdot I(V)$$

The necessary condition for maximum electrical power extraction is:
$$\frac{dP}{dV} = I(V) + V \frac{dI(V)}{dV} = 0 \iff \frac{dI}{dV} = -\frac{I}{V}$$

Because $\frac{d^2P}{dV^2} < 0$ over the physical operating range $[0, V_{oc}]$, $P(V)$ possesses a single global maximum. The reference Maximum Power Point $(V_{mpp}^*, I_{mpp}^*, P_{mpp}^*)$ is evaluated numerically using bounded 1D optimization over $[0.1 V_{oc}, 0.98 V_{oc}]$ independent of the controller.
