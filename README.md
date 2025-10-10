# RailOptimus

AI-assisted railway operations: delay prediction, schedule optimization, increased throughput, and network simulation with a modern web UI.

## Tasks Accomplished
- Task 1: Integrated supervised delay prediction and RL-based scheduling into the backend.
- Task 2: Built REST APIs for trains, routes, schedules, sections, maps, and simulations.
- Task 3: Implemented a Vite + React + TypeScript frontend with Tailwind and connected it to the backend.

## Technology Stack
- Frontend: React + TypeScript, Vite + Bun, Tailwind CSS, shadcn/Radix UI, React Router, Toaster for pop-up, Leaflet for interactive map. 
- Backend: Node.js + Express, MongoDB + Mongoose (Atlas), Flask, Socket.IO for real-time updates, Python microservice for ML-based delay prediction and RL-guided speed optimization, CORS to allow a web page to request API's from different domain, Zustand for security authentication, Hash function for security.
- Data Flow: Frontend fetches data from REST endpoints or local JSON/GeoJSON → passes props to components → updates via state/hooks → real-time updates via WebSocket.
- Simulation Engine: Flask + Dash app, Schedules trains conflict-free, integrates ML predictions for ETAs and dynamic speed guidance.

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
- rail-optimus-backend: Node/Express Backend + Python ML microservice assets and models.
- RailOptimus-dev: Frontend app (Vite + React + TS + Tailwind).
- RailOptiSim: Standalone Python Simulation app.

---

## Local Setup Instructions

### 1) Clone the Repository
```
git clone <github url>
cd RailOptimus
```
---

### 2) Backend (Node + Python ML) — rail-optimus-backend
```
cd rail-optimus-backend
npm install
node app.js

# for the ML model: create a venv and install requirements.
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 api.py
```
---

### 3) Frontend — RailOptimus-dev
```
cd RailOptimus-dev
npm install
npm run dev
```

### 4) Simulator — RailOptiSim
```
cd RailOptiSim
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```
---
