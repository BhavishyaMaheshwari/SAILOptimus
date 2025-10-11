"""
MILP Optimizer using PuLP for exact optimization of rake dispatch
Minimizes total cost: port handling + rail transport + demurrage
"""
import pulp
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from utils import CostCalculator, ETAPredictor
import time
import math
import re

from config import (
    PORT_BENCHMARKS,
    SECONDARY_PORT_PENALTY_PER_MT,
    DEFAULT_RAKE_CAPACITY_MT,
)

class MILPOptimizer:
    """Mixed Integer Linear Programming optimizer for logistics dispatch"""
    
    def __init__(self, data: Dict[str, pd.DataFrame], time_horizon_days: int = 30):
        self.vessels_df = data['vessels']
        self.ports_df = data['ports'] 
        self.plants_df = data['plants']
        self.rail_costs_df = data['rail_costs']
        self.time_horizon = time_horizon_days
        self.rake_capacity_mt = DEFAULT_RAKE_CAPACITY_MT
        
        # Create lookup dictionaries for faster access
        self.port_lookup = self.ports_df.set_index('port_id').to_dict('index')
        self.plant_lookup = self.plants_df.set_index('plant_id').to_dict('index')
        self.vessel_lookup = self.vessels_df.set_index('vessel_id').to_dict('index')

        self.secondary_port_penalty_per_mt = SECONDARY_PORT_PENALTY_PER_MT
        self.secondary_port_bias_days = 0.25

        self.vessel_allowed_ports: Dict[str, List[str]] = {}
        self.primary_port_map: Dict[str, str] = {}
        self.port_daily_throughput: Dict[str, float] = {}
        self.vessel_service_day_limits: Dict[str, Dict[str, int]] = {}
        self.vessel_freight_inr: Dict[str, float] = {}
        self.port_storage_costs: Dict[str, float] = {}
        self.port_free_days: Dict[str, int] = {}

        for vessel_id, vessel_data in self.vessel_lookup.items():
            primary_port = str(vessel_data['port_id']).strip()
            allowed_ports = self._parse_allowed_ports(vessel_data, primary_port)
            self.vessel_allowed_ports[vessel_id] = allowed_ports
            self.primary_port_map[vessel_id] = primary_port
            freight_inr_per_mt = CostCalculator.get_freight_inr_per_mt(vessel_data)
            self.vessel_freight_inr[vessel_id] = freight_inr_per_mt

        for port_id, port_data in self.port_lookup.items():
            daily_capacity = float(port_data.get('daily_capacity_mt', 0.0) or 0.0)
            rakes_available = float(port_data.get('rakes_available_per_day', 0.0) or 0.0)
            rake_capacity = rakes_available * self.rake_capacity_mt
            throughput = min(daily_capacity, rake_capacity) if daily_capacity and rake_capacity else max(daily_capacity, rake_capacity)
            self.port_daily_throughput[port_id] = max(1.0, throughput)
            benchmark = PORT_BENCHMARKS.get(port_id)
            if benchmark:
                self.port_storage_costs[port_id] = benchmark.storage_cost_per_mt_per_day
                self.port_free_days[port_id] = benchmark.free_storage_days
            else:
                self.port_storage_costs[port_id] = float(port_data.get('storage_cost_per_mt_per_day', 0.0) or 0.0)
                self.port_free_days[port_id] = int(port_data.get('free_storage_days', 0) or 0)

        for vessel_id, vessel_data in self.vessel_lookup.items():
            cargo_mt = float(vessel_data.get('cargo_mt', 0.0) or 0.0)
            self.vessel_service_day_limits[vessel_id] = {}
            allowed_ports = self.vessel_allowed_ports.get(vessel_id, [self.primary_port_map.get(vessel_id)])
            for port_id in allowed_ports:
                port_throughput = self.port_daily_throughput.get(port_id, cargo_mt if cargo_mt > 0 else 1.0)
                if port_throughput <= 0:
                    service_days = self.time_horizon
                else:
                    service_days = int(math.ceil(cargo_mt / port_throughput))

                buffered_days = min(self.time_horizon, max(1, service_days + 1))
                self.vessel_service_day_limits[vessel_id][port_id] = buffered_days

        # Predict inherent pre-berthing delays for realism (in days)
        self.eta_predictor = ETAPredictor()
        self.predicted_delay_days: Dict[str, Dict[str, float]] = {}
        for vessel_id, vessel_data in self.vessel_lookup.items():
            eta_day = float(vessel_data['eta_day'])
            port_delay_map: Dict[str, float] = {}
            for port_id in self.vessel_allowed_ports[vessel_id]:
                try:
                    delay_hours = self.eta_predictor.predict_delay(
                        vessel_id=vessel_id,
                        port_id=port_id,
                        base_eta=eta_day
                    )
                    port_delay_map[port_id] = max(0.0, delay_hours / 24.0)
                except Exception:
                    port_delay_map[port_id] = 0.0
            self.predicted_delay_days[vessel_id] = port_delay_map
        
    def _parse_allowed_ports(self, vessel_row: Dict, primary_port: str) -> List[str]:
        allowed = [primary_port]
        secondary_value = vessel_row.get('secondary_port_id')
        if secondary_value is None:
            return allowed

        if isinstance(secondary_value, (float, int)) and pd.isna(secondary_value):
            return allowed

        if isinstance(secondary_value, str):
            tokens = [tok.strip().upper() for tok in re.split(r'[|;,]+', secondary_value) if tok.strip()]
        elif isinstance(secondary_value, (list, tuple, set)):
            tokens = [str(tok).strip().upper() for tok in secondary_value if str(tok).strip()]
        else:
            tokens = [str(secondary_value).strip().upper()]

        for token in tokens:
            if token and token not in allowed and token in self.port_lookup:
                allowed.append(token)
        return allowed

    def build_milp_model(self, solver_time_limit: int = 300) -> Tuple[pulp.LpProblem, Dict]:
        """Build the MILP model for rake dispatch optimization"""
        
        print("Building MILP model...")
        
        # Create the optimization problem
        prob = pulp.LpProblem("Rake_Dispatch_Optimization", pulp.LpMinimize)
        
        # Sets
        vessels = self.vessels_df['vessel_id'].tolist()
        ports = self.ports_df['port_id'].tolist()
        plants = self.plants_df['plant_id'].tolist()
        time_periods = list(range(1, self.time_horizon + 1))
        
        # Decision Variables
        # x[v,p,pl,t] = amount of cargo (MT) from vessel v at port p to plant pl in period t
        x = pulp.LpVariable.dicts("cargo_flow",
                                 [(v, p, pl, t) for v in vessels for p in ports 
                                  for pl in plants for t in time_periods],
                                 lowBound=0, cat='Continuous')
        
        # y[v,p,t] = 1 if vessel v berths at port p in period t
        y = pulp.LpVariable.dicts("vessel_berth",
                                 [(v, p, t) for v in vessels for p in ports for t in time_periods],
                                 cat='Binary')
        
        # u[v,p] = 1 if vessel v chooses port p for discharge
        vessel_port_pairs = []
        for v in vessels:
            allowed_ports = self.vessel_allowed_ports.get(v, [self.primary_port_map.get(v)])
            for p in allowed_ports:
                vessel_port_pairs.append((v, p))

        u = pulp.LpVariable.dicts("vessel_port_choice",
                                 vessel_port_pairs,
                                 cat='Binary')

        # z[p,pl,t] = number of rakes from port p to plant pl in period t
        z = pulp.LpVariable.dicts("rake_assignment",
                                 [(p, pl, t) for p in ports for pl in plants for t in time_periods],
                                 lowBound=0, cat='Integer')
        
        # Auxiliary variables for costs
        demurrage_cost = pulp.LpVariable.dicts("demurrage", vessels, lowBound=0)
        storage_days = pulp.LpVariable.dicts(
            "storage_days",
            [(v, p) for v in vessels for p in ports],
            lowBound=0,
            cat='Continuous'
        )
        
        # Objective Function: Minimize total cost
        ocean_freight_cost = pulp.lpSum([
            x[v, p, pl, t] * self.vessel_freight_inr.get(v, 0.0)
            for v in vessels for p in ports for pl in plants for t in time_periods
        ])

        port_handling_cost = pulp.lpSum([
            x[v, p, pl, t] * self.port_lookup[p]['handling_cost_per_mt']
            for v in vessels for p in ports for pl in plants for t in time_periods
        ])
        
        rail_transport_cost = pulp.lpSum([
            x[v, p, pl, t] * self._get_rail_cost(p, pl)
            for v in vessels for p in ports for pl in plants for t in time_periods
        ])
        
        total_demurrage = pulp.lpSum([demurrage_cost[v] for v in vessels])

        storage_cost = pulp.lpSum([
            storage_days[v, p] * self.vessel_lookup[v]['cargo_mt'] * self.port_storage_costs.get(p, 0.0)
            for v in vessels for p in ports
        ])

        rerouting_penalty = pulp.lpSum([
            self.vessel_lookup[v]['cargo_mt'] * self.secondary_port_penalty_per_mt * u[v, p]
            for v in vessels
            for p in self.vessel_allowed_ports.get(v, [self.primary_port_map.get(v)])
            if p is not None and p != self.primary_port_map.get(v)
        ])

        prob += ocean_freight_cost + port_handling_cost + rail_transport_cost + total_demurrage + storage_cost + rerouting_penalty
        
        # Constraints
        
        # 1. Vessel cargo capacity constraint
        for v in vessels:
            vessel_cargo = self.vessel_lookup[v]['cargo_mt']
            prob += pulp.lpSum([x[v, p, pl, t] for p in ports for pl in plants 
                               for t in time_periods]) == vessel_cargo
        
        # 2. Vessel can only berth at its designated port
        for v in vessels:
            allowed_ports = self.vessel_allowed_ports.get(v, [self.primary_port_map.get(v)])
            if allowed_ports:
                prob += pulp.lpSum([u[v, p] for p in allowed_ports]) == 1

            for p in ports:
                if p not in allowed_ports:
                    for t in time_periods:
                        prob += y[v, p, t] == 0
                else:
                    for t in time_periods:
                        prob += y[v, p, t] <= u[v, p]
        
        # 3. Vessel can berth only after ETA
        for v in vessels:
            vessel_eta = float(self.vessel_lookup[v]['eta_day'])
            allowed_ports = self.vessel_allowed_ports.get(v, [self.primary_port_map.get(v)])
            for p in allowed_ports:
                for t in time_periods:
                    if t < vessel_eta:
                        prob += y[v, p, t] == 0
        
        # 4. Vessel berthing schedule limits and exclusivity
        for v in vessels:
            allowed_ports = self.vessel_allowed_ports.get(v, [self.primary_port_map.get(v)])
            if not allowed_ports:
                continue

            for p in allowed_ports:
                service_limit = self.vessel_service_day_limits.get(v, {}).get(p, 1)
                prob += pulp.lpSum([y[v, p, t] for t in time_periods]) <= service_limit * u[v, p]
                free_days = self.port_free_days.get(p, 0)
                prob += storage_days[v, p] >= pulp.lpSum([y[v, p, t] for t in time_periods]) - free_days * u[v, p]
                prob += storage_days[v, p] <= self.time_horizon * u[v, p]

            for t in time_periods:
                prob += pulp.lpSum([y[v, p, t] for p in allowed_ports]) <= 1
        
        # 5. Cargo flow only when vessel berths
        for v in vessels:
            vessel_cargo = self.vessel_lookup[v]['cargo_mt']
            allowed_ports = self.vessel_allowed_ports.get(v, [self.primary_port_map.get(v)])
            for p in allowed_ports:
                for pl in plants:
                    for t in time_periods:
                        prob += x[v, p, pl, t] <= vessel_cargo * y[v, p, t]

        # 5b. Block cargo flows from non-designated ports entirely
        for v in vessels:
            allowed_ports = self.vessel_allowed_ports.get(v, [self.primary_port_map.get(v)])
            for p in ports:
                if p in allowed_ports:
                    continue
                for pl in plants:
                    for t in time_periods:
                        prob += x[v, p, pl, t] == 0
        
        # 6. Port capacity constraints
        for p in ports:
            port_capacity = self.port_lookup[p]['daily_capacity_mt']
            for t in time_periods:
                prob += pulp.lpSum([x[v, p, pl, t] for v in vessels for pl in plants]) <= port_capacity
        
        # 7. Rake capacity constraints
        for p in ports:
            for pl in plants:
                for t in time_periods:
                    prob += pulp.lpSum([x[v, p, pl, t] for v in vessels]) <= z[p, pl, t] * self.rake_capacity_mt
        
        # 8. Rake availability constraints
        for p in ports:
            rakes_available = self.port_lookup[p]['rakes_available_per_day']
            for t in time_periods:
                prob += pulp.lpSum([z[p, pl, t] for pl in plants]) <= rakes_available
        
        # 9. Plant demand constraints (soft constraint with penalty)
        # This is handled in post-processing for simplicity
        
        # 10. Demurrage cost calculation (simplified)
        for v in vessels:
            vessel_eta = float(self.vessel_lookup[v]['eta_day'])
            demurrage_rate = float(self.vessel_lookup[v]['demurrage_rate'])

            delay_terms = []
            for p in self.vessel_allowed_ports.get(v, [self.primary_port_map.get(v)]):
                inherent_delay = self.predicted_delay_days.get(v, {}).get(p, 0.0)
                for t in time_periods:
                    effective_delay = max(0.0, (t + inherent_delay) - vessel_eta)
                    if effective_delay > 0:
                        delay_terms.append(demurrage_rate * effective_delay * y[v, p, t])

            if delay_terms:
                prob += demurrage_cost[v] >= pulp.lpSum(delay_terms)
            else:
                prob += demurrage_cost[v] >= 0
        
        variables = {
            'cargo_flow': x,
            'vessel_berth': y, 
            'vessel_port_choice': u,
            'storage_days': storage_days,
            'rake_assignment': z,
            'demurrage_cost': demurrage_cost
        }
        
        return prob, variables
    
    def solve_milp(self, solver_name: str = 'CBC', time_limit: int = 300) -> Dict:
        """Solve the MILP model and return results"""
        
        start_time = time.time()
        
        try:
            prob, variables = self.build_milp_model(time_limit)
            
            # Set solver
            if solver_name.upper() == 'CBC':
                solver = pulp.PULP_CBC_CMD(timeLimit=time_limit, msg=1)
            elif solver_name.upper() == 'GUROBI':
                try:
                    solver = pulp.GUROBI_CMD(timeLimit=time_limit, msg=1)
                except:
                    print("Gurobi not available, falling back to CBC")
                    solver = pulp.PULP_CBC_CMD(timeLimit=time_limit, msg=1)
            else:
                solver = pulp.PULP_CBC_CMD(timeLimit=time_limit, msg=1)
            
            # Solve
            prob.solve(solver)
            
            solve_time = time.time() - start_time
            
            # Extract results
            status = pulp.LpStatus[prob.status]
            objective_value = pulp.value(prob.objective) if prob.status == pulp.LpStatusOptimal else None
            
            assignments = []
            if prob.status == pulp.LpStatusOptimal:
                assignments = self._extract_assignments(variables)
            
            results = {
                'status': status,
                'objective_value': objective_value,
                'solve_time': solve_time,
                'assignments': assignments,
                'solver_used': solver_name,
                'variables_count': prob.numVariables(),
                'constraints_count': prob.numConstraints()
            }
            
            print(f"MILP solved in {solve_time:.2f}s - Status: {status}")
            if objective_value:
                print(f"Objective value: ${objective_value:,.2f}")
            
            return results
            
        except Exception as e:
            print(f"MILP solver error: {e}")
            return {
                'status': 'Error',
                'error': str(e),
                'solve_time': time.time() - start_time,
                'assignments': []
            }
    
    def _get_rail_cost(self, port_id: str, plant_id: str) -> float:
        """Get rail transport cost between port and plant"""
        try:
            cost_row = self.rail_costs_df[
                (self.rail_costs_df['port_id'] == port_id) & 
                (self.rail_costs_df['plant_id'] == plant_id)
            ]
            return cost_row.iloc[0]['cost_per_mt'] if not cost_row.empty else 100.0
        except:
            return 100.0  # Default cost
    
    def _extract_assignments(self, variables: Dict) -> List[Dict]:
        """Extract assignment solution from MILP variables"""
        assignments = []
        
        cargo_flow = variables['cargo_flow']
        vessel_berth = variables['vessel_berth']
        storage_days_var = variables.get('storage_days', {})
        
        for v in self.vessels_df['vessel_id']:
            for p in self.ports_df['port_id']:
                for pl in self.plants_df['plant_id']:
                    for t in range(1, self.time_horizon + 1):
                        cargo_amount = pulp.value(cargo_flow[v, p, pl, t])
                        if cargo_amount is None or cargo_amount <= 0.1:
                            continue

                        cargo_amount = float(cargo_amount)

                        # Check if vessel actually berths in this period
                        berth_status = pulp.value(vessel_berth[v, p, t])
                        if berth_status is None or berth_status < 0.5:
                            continue

                        scheduled_day = int(t)
                        predicted_delay = float(self.predicted_delay_days.get(v, {}).get(p, 0.0))
                        planned_eta = float(self.vessel_lookup[v]['eta_day'])
                        actual_berth_time = float(scheduled_day + predicted_delay)
                        billable_storage_days = float(pulp.value(storage_days_var.get((v, p), 0)) or 0.0)
                        delay_days = max(0.0, actual_berth_time - planned_eta)
                        free_days = self.port_free_days.get(p, 0)
                        dwell_days = billable_storage_days + free_days if billable_storage_days > 0 else max(predicted_delay, delay_days)

                        assignment = {
                            'vessel_id': v,
                            'port_id': p,
                            'plant_id': pl,
                            'time_period': scheduled_day,
                            'scheduled_day': scheduled_day,
                            'cargo_mt': round(cargo_amount, 2),
                            'berth_time': actual_berth_time,
                            'actual_berth_time': actual_berth_time,
                            'planned_berth_time': planned_eta,
                            'predicted_delay_days': predicted_delay,
                            'rakes_required': int(math.ceil(cargo_amount / self.rake_capacity_mt)),
                            'eta_day': planned_eta,
                            'primary_port_id': self.primary_port_map.get(v),
                            'billable_storage_days': round(billable_storage_days, 2),
                            'dwell_days': round(dwell_days, 2),
                            'delay_days': round(delay_days, 2)
                        }
                        assignments.append(assignment)
        
        return assignments
    
    def create_baseline_solution(self) -> Dict:
        """Create a simple FCFS (First Come First Served) baseline solution"""
        print("Creating FCFS baseline solution...")
        
        assignments = []
        port_utilization: Dict[str, float] = {}  # Track when each port is busy
        
        # Sort vessels by ETA
        vessels_sorted = self.vessels_df.sort_values('eta_day')
        
        # Simple assignment: each vessel to closest plant with matching requirements
        for _, vessel in vessels_sorted.iterrows():
            vessel_id = vessel['vessel_id']
            primary_port = vessel['port_id']
            cargo_grade = vessel['cargo_grade']
            cargo_mt = vessel['cargo_mt']
            eta = float(vessel['eta_day'])

            # Find plants that can accept this cargo type
            compatible_plants = self.plants_df[
                self.plants_df['quality_requirements'] == cargo_grade
            ]
            
            if compatible_plants.empty:
                continue

            target_plant = compatible_plants.loc[compatible_plants['daily_demand_mt'].idxmax()]

            allowed_ports = self.vessel_allowed_ports.get(vessel_id, [primary_port])
            best_choice = None
            best_score = None

            for candidate_port in allowed_ports:
                predicted_delay = self.predicted_delay_days.get(vessel_id, {}).get(candidate_port, 0.0)
                arrival_with_delay = eta + predicted_delay
                port_available = port_utilization.get(candidate_port, eta)
                actual_start = max(arrival_with_delay, port_available)
                bias = 0.0 if candidate_port == primary_port else self.secondary_port_bias_days
                score = actual_start + bias

                if best_score is None or score < best_score:
                    best_score = score
                    best_choice = {
                        'port': candidate_port,
                        'predicted_delay': predicted_delay,
                        'actual_start': actual_start
                    }

            if not best_choice:
                continue

            chosen_port = best_choice['port']
            actual_berth_time = best_choice['actual_start']
            predicted_delay = best_choice['predicted_delay']

            # Assume port takes 1-2 days to handle cargo (baseline is slower)
            port_handling_days = 1.5  # Baseline is less efficient
            port_utilization[chosen_port] = actual_berth_time + port_handling_days

            scheduled_day = int(math.ceil(actual_berth_time))

            assignment = {
                'vessel_id': vessel_id,
                'port_id': chosen_port,
                'plant_id': target_plant['plant_id'],
                'time_period': scheduled_day,
                'scheduled_day': scheduled_day,
                'cargo_mt': cargo_mt,
                'berth_time': actual_berth_time,
                'actual_berth_time': actual_berth_time,
                'planned_berth_time': eta,
                'predicted_delay_days': predicted_delay,
                'rakes_required': int(np.ceil(cargo_mt / self.rake_capacity_mt))
            }
            assignments.append(assignment)
        
        # Calculate baseline costs (now includes demurrage from delays)
        baseline_cost = self._calculate_assignment_cost(assignments)
        
        print(f"Baseline FCFS cost: ${baseline_cost:,.2f}")
        
        return {
            'status': 'Baseline_FCFS',
            'objective_value': baseline_cost,
            'assignments': assignments,
            'solve_time': 0.1,
            'method': 'First Come First Served (No Optimization)'
        }
    
    def _calculate_assignment_cost(self, assignments: List[Dict]) -> float:
        """Calculate total cost for a set of assignments"""
        total_cost = 0.0
        
        for assignment in assignments:
            port_id = assignment['port_id']
            plant_id = assignment['plant_id']
            cargo_mt = assignment['cargo_mt']
            vessel_id = assignment['vessel_id']
            berth_time = assignment.get('actual_berth_time')
            if berth_time is None:
                berth_time = assignment.get('berth_time', assignment.get('time_period', 0))
            
            # Port handling cost
            port_data = self.port_lookup[port_id]
            port_cost = port_data['handling_cost_per_mt'] * cargo_mt
            
            # Rail transport cost
            rail_cost = self._get_rail_cost(port_id, plant_id) * cargo_mt
            
            # Demurrage cost (critical for realistic baseline)
            vessel_info = self.vessel_lookup[vessel_id]
            vessel_eta = float(assignment.get('planned_berth_time', vessel_info['eta_day']))
            demurrage_rate = vessel_info['demurrage_rate']
            
            # Calculate delay in days (berth time - planned ETA)
            delay_days = max(0, float(berth_time) - vessel_eta) if berth_time is not None else 0
            demurrage_cost = delay_days * demurrage_rate

            # Storage cost using dwell minus free days
            storage_rate = float(port_data.get('storage_cost_per_mt_per_day', 0.0) or 0.0)
            free_days = float(port_data.get('free_storage_days', 0.0) or 0.0)
            benchmark = PORT_BENCHMARKS.get(port_id)
            if storage_rate <= 0 and benchmark:
                storage_rate = benchmark.storage_cost_per_mt_per_day
            if free_days <= 0 and benchmark:
                free_days = benchmark.free_storage_days
            dwell_days = float(assignment.get('dwell_days', delay_days) or 0.0)
            billable_days = max(0.0, float(assignment.get('billable_storage_days', dwell_days - free_days)) or 0.0)
            storage_cost = cargo_mt * billable_days * storage_rate

            ocean_freight = cargo_mt * self.vessel_freight_inr.get(vessel_id, 0.0)
            
            secondary_penalty = 0.0
            if port_id != self.primary_port_map.get(vessel_id):
                secondary_penalty = cargo_mt * self.secondary_port_penalty_per_mt

            total_cost += (
                port_cost +
                rail_cost +
                demurrage_cost +
                secondary_penalty +
                storage_cost +
                ocean_freight
            )
        
        return total_cost