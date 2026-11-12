# Quantum-Assisted-Targeted-Load-Shedding-Optimizer

**Domain:** Energy & Smart Infrastructure  
**Challenge Track:** Quantum Optimization Challenge (IBM Qiskit)  
**Problem Class:** Combinatorial Resource Allocation (0-1 Knapsack / QUBO)  

---

## 1. Executive Summary

Electrical power deficits in developing grid networks frequently force utility operators to enforce scheduled load-shedding (rolling blackouts). In practice, these outages are often applied broadly across distribution feeders on fixed rotation schedules rather than dynamically optimized around real-time criticality. Consequently, essential public infrastructure—such as hospitals, emergency response centers, and high-value industrial zones—can lose power while lower-priority residential feeders remain energized.

The **Quantum-Assisted Targeted Load-Shedding Optimizer** addresses this resource-allocation problem using a hybrid quantum-classical workflow built in IBM Qiskit. By formulating feeder selection during a generation shortfall as a **0-1 Knapsack Problem**, translating the capacity constraint into a **Quadratic Unconstrained Binary Optimization (QUBO)** model, and solving it via the **Quantum Approximate Optimization Algorithm (QAOA)**, the system identifies the subset of city sectors that maximizes retained societal and economic criticality without exceeding available grid generation capacity.

---

## 2. Problem Statement & Real-World Motivation

### 2.1 Operational Context
In regional distribution networks across Pakistan (such as local grid subdivisions in Rawalpindi), peak summer demand and supply bottlenecks routinely create sudden megawatt (MW) shortfalls. Grid control operators must rapidly shed load to prevent transformer overload and cascading grid instability.

### 2.2 Competing Objectives and Constraints
During an energy deficit, grid operators face a strict trade-off between competing priorities:
* **Maximize Critical Service Continuity:** Keep high-priority facilities (hospitals, water treatment, industrial production) energized to minimize human and economic harm.
* **Respect Hard Physical Capacity Limits:** Ensure the aggregate power draw of all energized sectors remains strictly at or below the available generation capacity ($C_{\max}$) to avoid voltage collapse or equipment damage.

Because the number of possible feeder on/off combinations grows exponentially ($2^n$ states for $n$ sectors), dynamic feeder prioritization becomes a classic combinatorial optimization bottleneck as network granularity increases.

---

## 3. Mathematical Formulation

### 3.1 Decision Variables
For a local distribution network divided into $n$ distinct city sectors, we define a binary decision variable $x_i$ for each sector $i \in \{1, 2, \dots, n\}$:

$$x_i = \begin{cases} 1, & \text{if sector } i \text{ remains energized (Online)} \\ 0, & \text{if sector } i \text{ undergoes load-shedding (Cut)} \end{cases}$$

### 3.2 Objective Function
Each sector $i$ is assigned a criticality weight $w_i > 0$ reflecting its societal and economic importance (for example, hospitals receive the highest priority weight, followed by industrial and commercial zones, and then residential blocks). The objective is to maximize the total criticality score of all energized sectors:

$$\max_{x \in \{0,1\}^n} Z(x) = \sum_{i=1}^{n} w_i x_i$$

### 3.3 Grid Capacity Constraint
Each sector $i$ requires a known power demand $d_i > 0$ (measured in MW). The total demand of all energized sectors cannot exceed the available grid capacity $C_{\max}$ during the shortfall:

$$\sum_{i=1}^{n} d_i x_i \le C_{\max}$$

### 3.4 Benchmark Test Instance
To evaluate the formulation on a simulator-friendly scale, we model a 5-sector localized grid instance with a reduced generation cap of $C_{\max} = 30\text{ MW}$ (down from a total connected demand of $50\text{ MW}$):

| Sector ID | Sector Name | Power Demand $d_i$ (MW) | Criticality Weight $w_i$ | Infrastructure Role |
| :--- | :--- | :---: | :---: | :--- |
| $x_1$ | **Hospital** | $10$ | $50$ | Emergency healthcare and life-support systems |
| $x_2$ | **Industrial** | $15$ | $40$ | Continuous manufacturing and export operations |
| $x_3$ | **Commercial** | $12$ | $30$ | Retail, banking, and municipal offices |
| $x_4$ | **Res\_A** | $8$ | $20$ | High-density residential block A |
| $x_5$ | **Res\_B** | $5$ | $10$ | Residential block B |
| **Total** | **All Sectors** | **$50\text{ MW}$** | **$150$** | **Full-load baseline (requires $20\text{ MW}$ shed)** |

---

## 4. Quantum Mapping & Algorithm Justification

### 4.1 Mapping to QUBO and Ising Hamiltonian
Gate-based quantum optimization algorithms operate on unconstrained binary objectives. Using `qiskit_optimization`, the constrained `QuadraticProgram` is converted into an unconstrained **QUBO** problem:
1. **Slack Variable Encoding:** The linear inequality $\sum_{i=1}^n d_i x_i \le C_{\max}$ is transformed into an equality constraint by introducing binary slack variables $s_k \in \{0, 1\}$ that represent unused grid capacity up to $C_{\max}$.
2. **Quadratic Penalty Augmentation:** The equality constraint is squared and multiplied by a penalty scalar $P > 0$, adding a penalty term $P \left(\sum_{i=1}^n d_i x_i + \sum_k 2^k s_k - C_{\max}\right)^2$ to the objective function. Any bitstring violating $C_{\max}$ incurs a high energy penalty.
3. **Ising Hamiltonian Mapping:** Each binary variable $z \in \{0, 1\}$ is mapped to a Pauli-$Z$ spin operator via $z = \frac{1 - Z}{2}$, translating the QUBO matrix into a cost Hamiltonian $H_C$ whose ground state encodes the optimal load-shedding schedule.

### 4.2 Why QAOA?
The **Quantum Approximate Optimization Algorithm (QAOA)** is well-suited for this combinatorial problem because:
* It is specifically designed for near-term variational quantum circuits where problem structure is encoded directly into alternating cost ($e^{-i \gamma H_C}$) and mixer ($e^{-i \beta H_M}$) unitary layers.
* A classical optimizer (**COBYLA**) iteratively updates the variational angles $(\vec{\gamma}, \vec{\beta})$ using measurement samples from Qiskit's `StatevectorSampler` primitive to minimize the expected energy $\langle \psi(\vec{\gamma}, \vec{\beta}) | H_C | \psi(\vec{\gamma}, \vec{\beta}) \rangle$.

---

## 5. System Architecture & Prototype Implementation

The prototype is structured into a modular hybrid pipeline:
1. **Grid Input & Parameter Layer:** Accepts sector power demands, criticality scores, and real-time available capacity ($C_{\max}$).
2. **Optimization Modeling Layer:** Builds the `QuadraticProgram` in Qiskit and handles automated QUBO conversion via `QuadraticProgramToQubo`.
3. **Dual-Solver Execution Layer:**
   * **Classical Exact Baseline:** Uses `NumPyMinimumEigensolver` wrapped in `MinimumEigenOptimizer` to compute the mathematically exact ground-truth schedule.
   * **Quantum Variational Solver:** Executes parameterized QAOA circuits (configurable circuit depth $p$) via `StatevectorSampler` and `COBYLA`.
4. **Interactive Decision Dashboard (`app.py`):** Built with Streamlit and Pandas, enabling grid operators and judges to dynamically adjust $C_{\max}$ ($10\text{ MW}$ to $50\text{ MW}$) and QAOA circuit depth ($p = 1$ to $5$), inspect the generated linear program, and compare Classical vs. Quantum feeder statuses side by side.

---

## 6. Validation & Results

On the 5-sector benchmark instance with $C_{\max} = 30\text{ MW}$ and QAOA depth $p = 2$:

| Metric / Sector | Classical Exact Solver | Quantum QAOA Solver ($p=2$) | Status / Interpretation |
| :--- | :---: | :---: | :--- |
| **Hospital ($10\text{ MW}$, $w=50$)** | `1` (Online) | `1` (Online) | Energized (Highest priority preserved) |
| **Industrial ($15\text{ MW}$, $w=40$)** | `1` (Online) | `1` (Online) | Energized (High economic priority preserved) |
| **Commercial ($12\text{ MW}$, $w=30$)** | `0` (Cut) | `0` (Cut) | Shed to satisfy $30\text{ MW}$ cap |
| **Res\_A ($8\text{ MW}$, $w=20$)** | `0` (Cut) | `0` (Cut) | Shed to satisfy $30\text{ MW}$ cap |
| **Res\_B ($5\text{ MW}$, $w=10$)** | `1` (Online) | `1` (Online) | Energized (Fills remaining $5\text{ MW}$ headroom) |
| **Total Power Used** | **$30\text{ MW} / 30\text{ MW}$** | **$30\text{ MW} / 30\text{ MW}$** | **$100\%$ capacity utilization, zero violation** |
| **Total Criticality Score** | **$100$** | **$100$** | **Exact global optimum achieved** |

The QAOA solver matches the classical exact baseline, proving that the quantum variational circuit reliably recovers the optimal feasible subset under tight resource constraints.

---

## 7. Honest Limitations & Future Work

1. **Slack-Variable Qubit Overhead:** Encoding inequality constraints ($\sum d_i x_i \le C_{\max}$) into a QUBO introduces ancillary slack qubits proportional to $\lceil \log_2(C_{\max}) \rceil$. For a 5-sector problem with $C_{\max} = 30$, this requires 5 decision qubits plus 5 slack qubits ($10$ qubits total), which doubles the qubit footprint on simulator and hardware backends.
2. **Penalty Weight Sensitivity:** If the QUBO penalty multiplier $P$ is tuned too low, QAOA may favor infeasible bitstrings that exceed $C_{\max}$; if $P$ is too high, the energy landscape becomes steep and ill-conditioned for gradient-free optimizers like COBYLA.
3. **NISQ Hardware Noise:** While the noiseless `StatevectorSampler` achieves $100\%$ agreement with the classical solver at depth $p=2$, executing multi-qubit $R_{ZZ}$ entangling gates from dense QUBO slack terms on real noisy quantum processors would suffer from decoherence and readout errors without error mitigation.
4. **Simplified Power Flow Physics:** The current 0-1 Knapsack model balances active megawatt capacity ($P_{\text{MW}}$) but abstracts away reactive power ($Q_{\text{MVAR}}$), line losses, and multi-period temporal fairness (ensuring the same residential block is not shed across consecutive intervals). Future iterations can incorporate multi-time-step fairness penalties and DC/AC power flow constraints.
