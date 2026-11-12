# Simulation Methodology and Numerical Integration

## 1. Multi-Rate Discrete-Continuous System
The simulation model couples two distinct dynamic timescales:
1. **High-Frequency Continuous Circuit Dynamics:**
   The DC-DC boost converter states ($V_{pv}, i_L, V_{out}$) evolve according to non-linear differential equations with natural LC resonant frequencies around $200\ \text{Hz}$ to $1\ \text{kHz}$.
2. **Discrete Controller Execution:**
   The digital microcontroller executes the MPPT algorithm at a discrete sampling interval $T_s = 5\ \text{ms}$ ($200\ \text{Hz}$).

---

## 2. Averaged State-Space Converter Equations
For continuous conduction mode (CCM):

$$\frac{d V_{pv}}{dt} = \frac{I_{pv}(V_{pv}, G, T) - i_L}{C_{pv}}$$
$$\frac{d i_L}{dt} = \frac{V_{pv} - (1 - D) V_{out} - r_L i_L}{L}$$
$$\frac{d V_{out}}{dt} = \frac{(1 - D) i_L - \frac{V_{out}}{R_{load}}}{C_{out}}$$

### Boundary Condition:
The diode blocks reverse current. If $i_L = 0$ and $\frac{d i_L}{dt} < 0$, then $\frac{d i_L}{dt} = 0$.

---

## 3. Fourth-Order Runge-Kutta (RK4) Numerical Integration
To ensure numerical stability and precision without artificial numerical damping, the classical 4th-order Runge-Kutta scheme is employed:

For a vector state $\mathbf{x} = [V_{pv}, i_L, V_{out}]^T$:
$$\mathbf{k}_1 = \mathbf{f}(t_n, \mathbf{x}_n)$$
$$\mathbf{k}_2 = \mathbf{f}\left(t_n + \frac{\Delta t}{2}, \mathbf{x}_n + \frac{\Delta t}{2} \mathbf{k}_1\right)$$
$$\mathbf{k}_3 = \mathbf{f}\left(t_n + \frac{\Delta t}{2}, \mathbf{x}_n + \frac{\Delta t}{2} \mathbf{k}_2\right)$$
$$\mathbf{k}_4 = \mathbf{f}\left(t_n + \Delta t, \mathbf{x}_n + \Delta t \mathbf{k}_3\right)$$
$$\mathbf{x}_{n+1} = \mathbf{x}_n + \frac{\Delta t}{6} \left( \mathbf{k}_1 + 2 \mathbf{k}_2 + 2 \mathbf{k}_3 + \mathbf{k}_4 \right)$$

With $\Delta t = 50\ \mu\text{s}$, the numerical time step satisfies the Courant-Friedrichs-Lewy (CFL) stability criterion:
$$\Delta t \ll \pi \sqrt{L C_{pv}} \approx 2.3\ \text{ms}$$

---

## 4. Multi-Rate Integration Loop
1. At time $t = k \cdot T_s$:
   - Sensed PV voltage $V_{pv}(k)$ and current $I_{pv}(k)$ are measured.
   - Power $P_{pv}(k) = V_{pv}(k) \cdot I_{pv}(k)$ is calculated.
   - The active MPPT controller updates duty cycle $D(k+1)$.
2. For $m = 1 \dots \frac{T_s}{\Delta t}$:
   - Current environmental conditions $G(t), T(t)$ are evaluated.
   - Continuous states are advanced by $\Delta t$ using RK4.
   - Independent theoretical MPP $(V_{mpp}^*, I_{mpp}^*, P_{mpp}^*)$ is evaluated directly from the PV single-diode model at $(G(t), T(t))$.
   - System telemetry is logged.
