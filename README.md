# SAILOptimus

Al-Enabled Logistics Optimizer for Cost-Optimal Vessel Scheduling and Port-Plant Linkage in Steel Supply Chain

## Tasks Accomplished
- Task 1: Integrated supervised ML models for vessel ETA, port congestion, and demurrage prediction, along with MILP + heuristic-based dispatch optimization in the backend.
- Task 2: Built REST APIs for vessels, ports, plants, stock, schedules, and simulation modules.
- Task 3: Developed a Vite + React + TypeScript frontend with Tailwind, linked to the backend for real-time visualization and scenario simulation.

## Technology Stack
- Frontend: React + TypeScript, Vite + Bun, Tailwind CSS, shadcn/Radix UI, React Router, Toaster for pop-up, Leaflet for interactive map. 
- Backend: Node.js + Express , Flask, Socket.IO for real-time updates, Python microservice for ML-based delay prediction and RL-guided speed optimization, CORS to allow a web page to request API's from different domain, Zustand for security authentication, Hash function for security.
- Data Flow: Frontend fetches data from REST endpoints or local JSON/GeoJSON → passes props to components → updates via state/hooks → real-time updates via WebSocket.
- Optimizer: Flask + Dash app, Schedules trains conflict-free, integrates ML predictions for ETAs and dynamic speed guidance.
- ML Model: An ML-powered SAIL Logistics Dashboard that predicts vessel, berthing, and freight delays in real time using Random Forest models to optimize steel transport operations.

## Key Features
- AI-Powered Scheduling: Real-time assistance for train controllers in scheduling and precedence decisions.
- Optimization Engine: Operations research algorithms ensure conflict-free schedules under constraints (track availability, priorities, platforms, safety).
- Predictive AI: Reinforcement learning forecasts delays, ETAs, and provides dynamic speed guidance.
- Scenario Simulation: Interactive “what-if” testing for different traffic situations.
- Dashboard-Centric UI: Live train states, KPIs, and route analytics via maps, charts, and intuitive visualization.
- Offline-First Design: Reliable operation and demos in low-connectivity environments using bundled JSON/GeoJSON.
- Seamless Integration: Modular architecture connects with existing railway control systems and REST APIs.
- User Experience: Responsive, accessible UI with polished navigation, charts, and toasts.
- Conflict Resolution: Automates decisions across multiple trains, priorities, and infrastructure limits.
- Performance Gains: Data-driven scheduling reduces travel time, boosts throughput, and improves punctuality.

## Repository Layout
- backend: Node/Express Backend .
- RailOptimus-dev: Frontend app (Vite + React + TS + Tailwind).
- SAILoptimisation: Standalone Python Optimizer app.
- SAIL LogisticsML : ML Model used to predict ETAs (Expected Time of Arrival of vessel) and delay.

---

## Local Setup Instructions

### 1) Clone the Repository
```
git clone <github url>
cd SAILOptimus
```
---

### 2) Backend (Node) —backend
```
cd backend
npm install
node app.js

```
---

### 3) Frontend — RailOptimus-dev
```
cd RailOptimus-dev
npm install
npm run dev
```

### 4) Optimizer — SAILoptimisation
```
cd SAILoptimisation
python -m venv venv
source venv/bin/activate
pip install -r requirements_dash.txt
python app.py
```
### 5) ETA & Delay Predictor (ML Model) - SAIL LogisticsML
```
cd 'SAIL LogisticsML'
cd VesselFinal
python -m venv venv
source venv/bin/activate
pip install -r requirements_dash.txt
python app.py
```
---


## Project Links
- **Video Demonstration:** [Video Link](https://youtu.be/Z64fNkR3K2w)
