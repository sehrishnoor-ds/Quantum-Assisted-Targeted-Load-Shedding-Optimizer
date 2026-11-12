import streamlit as st
import warnings
import pandas as pd

# Suppress Scipy SparseEfficiencyWarnings and Qiskit DeprecationWarnings
warnings.filterwarnings('ignore')

from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit.primitives import StatevectorSampler as Sampler
from qiskit_algorithms import NumPyMinimumEigensolver

# --- UI Configuration ---
st.set_page_config(page_title="Quantum Grid Optimizer", page_icon="⚡", layout="wide")
st.title("⚡ Quantum-Assisted Targeted Load-Shedding Optimizer")
st.markdown("Optimize power distribution during a generation shortfall to ensure critical infrastructure remains online, without exceeding the grid's maximum available capacity.")

# --- Sidebar Inputs ---
st.sidebar.header("⚙️ Grid Parameters")
max_capacity = st.sidebar.slider("Available Grid Capacity (MW)", min_value=10, max_value=50, value=30, step=1)
qaoa_reps = st.sidebar.slider("QAOA Repetitions (Depth)", min_value=1, max_value=5, value=2, step=1)

st.sidebar.markdown("---")
st.sidebar.info("This interface runs a hybrid quantum-classical algorithm using Qiskit. It converts the Knapsack constraints into a QUBO and solves it via QAOA.")

# --- Main Data Setup ---
sectors = {
    'Hospital': {'Demand (MW)': 10, 'Criticality Score': 50},
    'Industrial': {'Demand (MW)': 15, 'Criticality Score': 40},
    'Commercial': {'Demand (MW)': 12, 'Criticality Score': 30},
    'Res_A': {'Demand (MW)': 8, 'Criticality Score': 20},
    'Res_B': {'Demand (MW)': 5, 'Criticality Score': 10},
}

st.write("### 🏙️ City Sector Configuration")
df = pd.DataFrame(sectors).T
st.table(df)

# --- Optimizer Execution ---
if st.button("🚀 Run Quantum Optimizer", type="primary"):
    with st.spinner("Initializing Quantum Circuit and Solving..."):
        
        # 1. Initialize the Quadratic Program
        qp = QuadraticProgram()
        for sector in sectors.keys():
            qp.binary_var(sector)
            
        # Objective & Constraints
        linear_obj = {sector: data['Criticality Score'] for sector, data in sectors.items()}
        qp.maximize(linear=linear_obj)
        
        linear_constraint = {sector: data['Demand (MW)'] for sector, data in sectors.items()}
        qp.linear_constraint(linear=linear_constraint, sense='<=', rhs=max_capacity, name='capacity')
        
        # 2. Classical Exact Solver (Baseline)
        exact_mes = NumPyMinimumEigensolver()
        exact_opt = MinimumEigenOptimizer(exact_mes)
        exact_result = exact_opt.solve(qp)
        
        # 3. Quantum QAOA Solver
        sampler = Sampler()
        qaoa = QAOA(sampler=sampler, optimizer=COBYLA(), reps=qaoa_reps)
        qaoa_opt = MinimumEigenOptimizer(qaoa)
        qaoa_result = qaoa_opt.solve(qp)
        
    st.markdown("---")
    st.write("### 🧮 Problem Formulation")
    # Fix for DeprecationWarning: Using prettyprint() instead of export_as_lp_string()
    st.code(qp.prettyprint())
    
    # --- Results Display ---
    st.write("### 📊 Optimization Results")
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("#### 💻 Classical Exact Solver (Baseline)")
        st.write(f"**Maximum Criticality Score Retained:** `{exact_result.fval}`")
        res_dict_class = {sector: ("🟢 Online" if val==1 else "🔴 Cut") for sector, val in zip(sectors.keys(), exact_result.x)}
        st.table(pd.DataFrame([res_dict_class]).T.rename(columns={0: "Grid Status"}))
        
    with col2:
        st.info("#### ⚛️ Quantum QAOA Solver")
        st.write(f"**Maximum Criticality Score Retained:** `{qaoa_result.fval}`")
        res_dict_quant = {sector: ("🟢 Online" if val==1 else "🔴 Cut") for sector, val in zip(sectors.keys(), qaoa_result.x)}
        st.table(pd.DataFrame([res_dict_quant]).T.rename(columns={0: "Grid Status"}))
        
    if list(exact_result.x) == list(qaoa_result.x):
        st.balloons()
        st.success("🎯 **Success!** The Quantum QAOA algorithm perfectly matched the exact classical optimal solution.")
    else:
        st.warning("⚠️ QAOA provided a different configuration. Try increasing the QAOA Repetitions in the sidebar.")
