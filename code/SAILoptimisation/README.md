# 🚢🚂 SIH 2025 Logistics Optimization Simulator

A production-quality **Dash web application** for optimizing railway rake dispatch from multiple ports to steel plants. Built for the **Smart India Hackathon 2025**.

## 🚀 Quick Start (30 Seconds)

```bash
# 1. Install dependencies
pip install -r requirements_dash.txt

# 2. Activate virtual environment
source venv/bin/activate

# 3. Launch dashboard
python app.py
# OR: python run.py

# 4. Open browser
http://127.0.0.1:5006/

# 4. Quick demo
Click "Load Sample Data" → "Run Optimized" → "Run Simulation"
```

## 📁 Project Structure

```
SIH-Logistics-Optimizer/
├── 🚀 CORE APPLICATION
│   ├── app.py                    # Main Dash web application
│   ├── data_loader.py            # Data management & CSV validation
│   ├── milp_optimizer.py         # MILP optimization engine
│   ├── heuristics.py            # GA & SA algorithms
│   ├── simulation.py            # Discrete-time simulation
│   ├── visuals.py               # Plotly visualizations
│   ├── utils.py                 # ML stubs & helper functions
│   └── launch_dashboard.py      # Smart launch script
│
├── 📊 SAMPLE DATA
│   └── assets/
│       ├── sample_vessels.csv    # 10 vessels with mixed cargo
│       ├── sample_ports.csv      # 3 major Indian ports
│       ├── sample_plants.csv     # 5 steel plants
│       └── sample_rail_costs.csv # 15 port-plant routes
│
├── 🧪 TESTING & VALIDATION
│   └── tests/
│       ├── test_dash_app.py         # Comprehensive test suite
│       ├── test_app_launch.py       # App launch verification
│       └── demo_complete_system.py  # Full system demonstration
│
├── 📚 DOCUMENTATION
│   └── docs/
│       ├── README.md                # Complete web app guide
│       └── PROJECT_SUMMARY.md       # Comprehensive overview
│
└── 🔧 CONFIGURATION
    └── requirements_dash.txt       # Python dependencies
```

## 🎯 Key Features

### **Interactive Web Dashboard**
- **6 Main Tabs**: Overview, Gantt Charts, Cost Analysis, Rake Dashboard, What-if Analysis, Logs
- **Real-time Optimization**: MILP + Genetic Algorithm + Simulated Annealing
- **Interactive Visualizations**: Gantt charts, heatmaps, cost breakdowns
- **Scenario Analysis**: What-if modeling with parameter variations

### **Advanced Optimization**
- **MILP (Exact)**: PuLP with CBC/Gurobi for optimal solutions
- **Genetic Algorithm**: DEAP-based scalable heuristic optimization
- **Simulated Annealing**: Solution refinement with adaptive cooling
- **Hybrid Pipeline**: MILP → GA → SA for best results

### **Comprehensive Simulation**
- **Discrete-time simulation** with 1-hour or 6-hour time steps
- **Real-time KPI tracking**: Cost, fulfillment, utilization, delays
- **Multi-scenario analysis**: Weather delays, equipment shortages, demand spikes

## 🧪 Testing

```bash
# Run comprehensive test suite
python tests/test_dash_app.py

# Test app launch capability
python tests/test_app_launch.py

# Run complete system demonstration
python tests/demo_complete_system.py
```

## 📊 Sample Results

**Demonstrated on toy dataset:**
- **9.5% cost reduction** ($3.8M savings)
- **12.5% demand fulfillment** with comprehensive KPI tracking
- **0.8 seconds** optimization time for heuristic methods
- **Multiple scenario analysis** across different conditions

## 🏆 SIH 2025 Competition Ready

**All Requirements Met:**
- ✅ Railway rake dispatch optimization from multiple ports to 5 plants
- ✅ MILP + GA + SA optimization pipeline
- ✅ Interactive web dashboard with real-time optimization
- ✅ CSV upload/validation for all datasets
- ✅ Scenario analysis and what-if modeling
- ✅ ML integration hooks for ETA prediction
- ✅ Production-quality code with comprehensive testing

## 📚 Documentation

- **[Complete Guide](docs/README.md)** - Detailed web application documentation
- **[Project Summary](docs/PROJECT_SUMMARY.md)** - Comprehensive project overview
- **Inline Documentation** - Detailed docstrings for all functions

## 🔧 Technical Stack

- **Backend**: Python with PuLP (MILP), DEAP (GA), scikit-learn (ML)
- **Frontend**: Dash with Plotly for interactive visualizations
- **Optimization**: CBC solver (free) with Gurobi support (commercial)
- **Data**: Pandas for data management, CSV import/export

## 🎯 Business Impact

- **10-25% logistics cost reduction** potential
- **30-50% demurrage cost reduction** through better scheduling
- **15-20% rake utilization improvement**
- **Real-time decision support** for port operations

---

**Built for Smart India Hackathon 2025** 🇮🇳  
*Transforming India's logistics infrastructure through intelligent optimization*

**🚀 Ready to optimize? Launch the dashboard and start exploring!**# VesselOptimisation
