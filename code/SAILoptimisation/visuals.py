"""
Plotly visualization functions for the logistics dashboard
Creates interactive charts, Gantt charts, KPI cards, and heatmaps
"""
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from utils import format_currency, format_tonnage

class LogisticsVisualizer:
    """Creates interactive visualizations for the logistics dashboard"""
    
    @staticmethod
    def create_kpi_cards(kpis: Dict[str, float], baseline_kpis: Optional[Dict[str, float]] = None) -> List[Dict]:
        """Create KPI cards with delta indicators and informative tooltips"""
        
        cards = []
        
        # Define KPI configurations with detailed explanations
        kpi_configs = [
            {
                'title': 'Total Cost',
                'key': 'total_cost',
                'format': 'currency',
                'color': 'danger',
                'tooltip_title': 'Total logistics cost',
                'formula': 'Port Handling + Rail Transport + Demurrage',
                'description': 'Sum of all operational costs across the entire supply chain',
                'factors': [
                    'Port handling fees per MT',
                    'Rail transport costs per MT-km',
                    'Demurrage penalties for delays',
                    'Vessel berth time optimization'
                ]
            },
            {
                'title': 'Demurrage Cost', 
                'key': 'demurrage_cost',
                'format': 'currency',
                'color': 'warning',
                'tooltip_title': 'Vessel delay penalties',
                'formula': 'Σ(Delay Days × Demurrage Rate per vessel)',
                'description': 'Penalties charged when vessels wait beyond their scheduled berth time',
                'factors': [
                    'Actual berth time vs planned/ETA',
                    'Per-vessel demurrage rate ($/day)',
                    'Port congestion levels',
                    'Berth availability optimization'
                ],
                'is_demurrage': True
            },
            {
                'title': 'Demand Fulfillment',
                'key': 'demand_fulfillment_pct',
                'format': 'percentage',
                'color': 'success',
                'tooltip_title': 'Steel plant demand coverage',
                'formula': '(Total Cargo Delivered / Total Plant Demand) × 100%',
                'description': 'Percentage of steel plant raw material requirements successfully met through optimized dispatch',
                'factors': [
                    'Plant-specific quality requirements (coking coal, limestone)',
                    'Cargo successfully delivered via rail to plants',
                    'Total planned demand across 5 steel plants',
                    'Port-plant rail connectivity and capacity',
                    'Higher % = Better supply chain efficiency'
                ]
            },
            {
                'title': 'Avg Vessel Wait',
                'key': 'avg_vessel_wait_hours',
                'format': 'hours',
                'color': 'info',
                'tooltip_title': 'Average waiting time',
                'formula': 'Σ(Planned Berth - ETA) / # vessels with wait',
                'description': 'Average hours vessels wait before berthing (per vessel with delay)',
                'factors': [
                    'Port berth capacity constraints',
                    'Vessel arrival schedule (ETA)',
                    'Optimization vs FCFS scheduling',
                    'Only counts vessels that waited'
                ]
            },
            {
                'title': 'Rake Utilization',
                'key': 'avg_rake_utilization',
                'format': 'decimal',
                'color': 'primary',
                'tooltip_title': 'Rail asset efficiency',
                'formula': 'Total Rake Trips / Theoretical Capacity',
                'description': 'How efficiently rail assets are being used for cargo transport',
                'factors': [
                    'Rakes available per day per port',
                    'Simulation horizon (days)',
                    'Actual trips made vs capacity',
                    'Rake capacity (5000 MT each)'
                ]
            },
            {
                'title': 'Vessels Processed',
                'key': 'vessels_processed_pct',
                'format': 'percentage',
                'color': 'secondary',
                'tooltip_title': 'Fleet processing rate',
                'formula': '(Vessels Handled / Total Vessels) × 100%',
                'description': 'Percentage of fleet successfully processed through the system',
                'factors': [
                    'Vessels with completed unloading',
                    'Total fleet size in schedule',
                    'Port handling capacity',
                    'Time horizon constraints'
                ]
            }
        ]
        
        for config in kpi_configs:
            key = config['key']
            value = kpis.get(key, 0)
            
            # Format value
            if config['format'] == 'currency':
                formatted_value = format_currency(value)
            elif config['format'] == 'percentage':
                formatted_value = f"{value:.1f}%"
            elif config['format'] == 'hours':
                formatted_value = f"{value:.1f}h"
            elif config['format'] == 'decimal':
                formatted_value = f"{value:.2f}"
            else:
                formatted_value = f"{value:.0f}"
            
            # Calculate delta if baseline provided
            delta = None
            delta_pct = None
            if baseline_kpis and key in baseline_kpis:
                baseline_value = baseline_kpis[key]
                if baseline_value != 0:
                    delta = value - baseline_value
                    delta_pct = (delta / baseline_value) * 100
            
            card = {
                'title': config['title'],
                'value': formatted_value,
                'raw_value': value,
                'delta': delta,
                'delta_pct': delta_pct,
                'color': config['color'],
                'tooltip_title': config.get('tooltip_title', ''),
                'formula': config.get('formula', ''),
                'description': config.get('description', ''),
                'factors': config.get('factors', []),
                'is_demurrage': config.get('is_demurrage', False)
            }
            
            cards.append(card)
        
        return cards
    
    @staticmethod
    def create_gantt_chart(assignments: List[Dict], vessels_df: pd.DataFrame, 
                          simulation_results: Optional[Dict] = None) -> go.Figure:
        """Create interactive Gantt chart for vessel and rake schedules"""
        
        if not assignments:
            fig = go.Figure()
            fig.add_annotation(
                text="No assignments to display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        # Prepare data for Gantt chart
        gantt_data = []
        
        # Vessel berth schedules
        vessel_lookup = vessels_df.set_index('vessel_id').to_dict('index')
        
        for assignment in assignments:
            vessel_id = assignment['vessel_id']
            port_id = assignment['port_id']
            plant_id = assignment['plant_id']
            
            if vessel_id in vessel_lookup:
                vessel_data = vessel_lookup[vessel_id]
                eta_day = vessel_data['eta_day']
                berth_time = assignment.get('berth_time', assignment.get('time_period', eta_day))
                
                # Estimate unloading duration (8 hours per 10K MT)
                cargo_mt = assignment.get('cargo_mt', vessel_data['cargo_mt'])
                unloading_hours = max(4, cargo_mt / 10000 * 8)
                
                gantt_data.append({
                    'Task': f"Vessel {vessel_id}",
                    'Start': pd.Timestamp('2024-01-01') + pd.Timedelta(days=berth_time),
                    'Finish': pd.Timestamp('2024-01-01') + pd.Timedelta(days=berth_time, hours=unloading_hours),
                    'Resource': f"{port_id} → {plant_id}",
                    'Type': 'Vessel',
                    'Cargo_MT': cargo_mt,
                    'Port': port_id,
                    'Plant': plant_id
                })
        
        if not gantt_data:
            fig = go.Figure()
            fig.add_annotation(text="No valid assignments found", x=0.5, y=0.5)
            return fig
        
        # Create Gantt chart
        df_gantt = pd.DataFrame(gantt_data)
        
        # Color mapping for different ports
        port_colors = {
            'HALDIA': '#FF6B6B',
            'PARADIP': '#4ECDC4', 
            'VIZAG': '#45B7D1',
            'default': '#96CEB4'
        }
        
        fig = go.Figure()
        
        # Add bars for each assignment
        for i, row in df_gantt.iterrows():
            color = port_colors.get(row['Port'], port_colors['default'])
            
            fig.add_trace(go.Scatter(
                x=[row['Start'], row['Finish'], row['Finish'], row['Start'], row['Start']],
                y=[i-0.4, i-0.4, i+0.4, i+0.4, i-0.4],
                fill='toself',
                fillcolor=color,
                line=dict(color=color, width=2),
                hovertemplate=(
                    f"<b>{row['Task']}</b><br>"
                    f"Port: {row['Port']}<br>"
                    f"Plant: {row['Plant']}<br>"
                    f"Cargo: {format_tonnage(row['Cargo_MT'])}<br>"
                    f"Start: {row['Start'].strftime('%Y-%m-%d %H:%M')}<br>"
                    f"End: {row['Finish'].strftime('%Y-%m-%d %H:%M')}<br>"
                    "<extra></extra>"
                ),
                name=row['Resource'],
                showlegend=i == 0 or row['Resource'] not in [df_gantt.iloc[j]['Resource'] for j in range(i)]
            ))
        
        # Update layout
        fig.update_layout(
            title="Vessel Berth and Unloading Schedule",
            xaxis_title="Timeline",
            yaxis_title="Vessels",
            yaxis=dict(
                tickmode='array',
                tickvals=list(range(len(df_gantt))),
                ticktext=df_gantt['Task'].tolist()
            ),
            height=max(400, len(df_gantt) * 40),
            hovermode='closest',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return fig
    
    @staticmethod
    def create_cost_breakdown_chart(kpis: Dict[str, float], 
                                  scenarios: Optional[List[Dict]] = None) -> go.Figure:
        """Create cost breakdown visualization"""
        
        # Cost components
        cost_components = {
            'Port Handling': kpis.get('port_handling_cost', 0),
            'Rail Transport': kpis.get('rail_transport_cost', 0),
            'Demurrage': kpis.get('demurrage_cost', 0)
        }
        
        # Filter out zero costs
        cost_components = {k: v for k, v in cost_components.items() if v > 0}
        
        if not cost_components:
            fig = go.Figure()
            fig.add_annotation(text="No cost data available", x=0.5, y=0.5)
            return fig
        
        if scenarios and len(scenarios) > 1:
            # Multi-scenario comparison
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=("Cost Breakdown", "Scenario Comparison"),
                specs=[[{"type": "pie"}, {"type": "bar"}]]
            )
            
            # Pie chart for current scenario
            fig.add_trace(
                go.Pie(
                    labels=list(cost_components.keys()),
                    values=list(cost_components.values()),
                    hole=0.3,
                    textinfo='label+percent',
                    textposition='outside'
                ),
                row=1, col=1
            )
            
            # Bar chart for scenario comparison
            scenario_names = [s.get('name', f'Scenario {i+1}') for i, s in enumerate(scenarios)]
            total_costs = [s.get('kpis', {}).get('total_cost', 0) for s in scenarios]
            
            fig.add_trace(
                go.Bar(
                    x=scenario_names,
                    y=total_costs,
                    text=[format_currency(cost) for cost in total_costs],
                    textposition='auto',
                    marker_color='lightblue'
                ),
                row=1, col=2
            )
            
        else:
            # Single scenario pie chart
            fig = go.Figure(data=[
                go.Pie(
                    labels=list(cost_components.keys()),
                    values=list(cost_components.values()),
                    hole=0.3,
                    textinfo='label+percent+value',
                    texttemplate='%{label}<br>%{percent}<br>%{text}',
                    text=[format_currency(v) for v in cost_components.values()],
                    textposition='outside'
                )
            ])
        
        total_cost = sum(cost_components.values())
        fig.update_layout(
            title=f"Cost Breakdown - Total: {format_currency(total_cost)}",
            height=500
        )
        
        return fig
    
    @staticmethod
    def create_rake_heatmap(assignments: List[Dict], ports_df: pd.DataFrame, 
                           simulation_days: int = 30) -> go.Figure:
        """Create heatmap of rake utilization by port and day"""
        
        if not assignments:
            fig = go.Figure()
            fig.add_annotation(text="No assignment data for heatmap", x=0.5, y=0.5)
            return fig
        
        # Initialize utilization matrix
        ports = ports_df['port_id'].tolist()
        days = list(range(1, simulation_days + 1))
        
        utilization_matrix = np.zeros((len(ports), len(days)))
        availability_matrix = np.zeros((len(ports), len(days)))
        
        # Fill availability matrix
        port_lookup = ports_df.set_index('port_id').to_dict('index')
        for i, port_id in enumerate(ports):
            daily_rakes = port_lookup[port_id]['rakes_available_per_day']
            availability_matrix[i, :] = daily_rakes
        
        # Fill utilization matrix from assignments
        for assignment in assignments:
            port_id = assignment.get('port_id')
            # Be robust: get time_period, or fallback to berth_time, default to day 1
            tp_val = assignment.get('time_period')
            if tp_val is None:
                tp_val = assignment.get('berth_time')
            if tp_val is None:
                tp_val = 1
            try:
                day_val = int(float(tp_val))
            except Exception:
                day_val = 1
            rakes_required = assignment.get('rakes_required', 1)

            if port_id in ports:
                port_idx = ports.index(port_id)
                day_idx = min(max(day_val - 1, 0), len(days) - 1)
                utilization_matrix[port_idx, day_idx] += rakes_required
        
        # Calculate utilization percentage
        utilization_pct = np.divide(utilization_matrix, availability_matrix, 
                                  out=np.zeros_like(utilization_matrix), 
                                  where=availability_matrix!=0) * 100
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=utilization_pct,
            x=[f"Day {d}" for d in days],
            y=ports,
            colorscale='RdYlBu_r',
            text=utilization_matrix.astype(int),
            texttemplate="%{text}",
            textfont={"size": 10},
            hovertemplate=(
                "Port: %{y}<br>"
                "Day: %{x}<br>"
                "Rakes Used: %{text}<br>"
                "Utilization: %{z:.1f}%<br>"
                "<extra></extra>"
            ),
            colorbar=dict(title="Utilization %")
        ))
        
        fig.update_layout(
            title="Rake Utilization Heatmap by Port and Day",
            xaxis_title="Days",
            yaxis_title="Ports",
            height=300 + len(ports) * 50
        )
        
        return fig
    
    @staticmethod
    def create_plant_fulfillment_chart(kpis: Dict[str, float], plants_df: pd.DataFrame,
                                     simulation_results: Optional[Dict] = None) -> go.Figure:
        """Create plant demand fulfillment chart"""
        
        plant_data = []
        
        if simulation_results and 'plant_deliveries' in simulation_results:
            plant_deliveries = simulation_results['plant_deliveries']
            
            for _, plant in plants_df.iterrows():
                plant_id = plant['plant_id']
                demand = plant['daily_demand_mt'] * 30  # Assume 30-day simulation
                delivered = plant_deliveries.get(plant_id, 0)
                fulfillment_pct = (delivered / demand * 100) if demand > 0 else 0
                
                plant_data.append({
                    'Plant': plant.get('plant_name', plant_id),
                    'Demand': demand,
                    'Delivered': delivered,
                    'Fulfillment_Pct': fulfillment_pct
                })
        else:
            # Use dummy data if simulation results not available
            for _, plant in plants_df.iterrows():
                demand = plant['daily_demand_mt'] * 30
                delivered = demand * np.random.uniform(0.7, 1.0)  # Random fulfillment
                fulfillment_pct = (delivered / demand * 100)
                
                plant_data.append({
                    'Plant': plant.get('plant_name', plant['plant_id']),
                    'Demand': demand,
                    'Delivered': delivered,
                    'Fulfillment_Pct': fulfillment_pct
                })
        
        if not plant_data:
            fig = go.Figure()
            fig.add_annotation(text="No plant data available", x=0.5, y=0.5)
            return fig
        
        df_plants = pd.DataFrame(plant_data)
        
        # Create subplot with bar chart and fulfillment percentage
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Demand vs Delivered", "Fulfillment Percentage"),
            specs=[[{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Bar chart for demand vs delivered
        fig.add_trace(
            go.Bar(
                name='Demand',
                x=df_plants['Plant'],
                y=df_plants['Demand'],
                marker_color='lightcoral',
                text=[format_tonnage(d) for d in df_plants['Demand']],
                textposition='auto'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(
                name='Delivered',
                x=df_plants['Plant'],
                y=df_plants['Delivered'],
                marker_color='lightblue',
                text=[format_tonnage(d) for d in df_plants['Delivered']],
                textposition='auto'
            ),
            row=1, col=1
        )
        
        # Fulfillment percentage chart
        colors = ['green' if pct >= 90 else 'orange' if pct >= 70 else 'red' 
                 for pct in df_plants['Fulfillment_Pct']]
        
        fig.add_trace(
            go.Bar(
                x=df_plants['Plant'],
                y=df_plants['Fulfillment_Pct'],
                marker_color=colors,
                text=[f"{pct:.1f}%" for pct in df_plants['Fulfillment_Pct']],
                textposition='auto',
                showlegend=False
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            title="Plant Demand Fulfillment Analysis",
            height=500,
            showlegend=True
        )
        
        fig.update_xaxes(title_text="Plants", row=1, col=1)
        fig.update_xaxes(title_text="Plants", row=1, col=2)
        fig.update_yaxes(title_text="Tonnage (MT)", row=1, col=1)
        fig.update_yaxes(title_text="Fulfillment (%)", row=1, col=2)
        
        return fig
    
    @staticmethod
    def create_timeline_chart(simulation_results: Dict) -> go.Figure:
        """Create timeline chart of key events"""
        
        if not simulation_results or 'simulation_log' not in simulation_results:
            fig = go.Figure()
            fig.add_annotation(text="No simulation log available", x=0.5, y=0.5)
            return fig
        
        log = simulation_results['simulation_log']
        
        # Filter important events
        important_events = ['vessel_arrival', 'vessel_berth', 'vessel_departure', 'cargo_delivery']
        filtered_log = [entry for entry in log if entry.get('event') in important_events]
        
        if not filtered_log:
            fig = go.Figure()
            fig.add_annotation(text="No timeline events to display", x=0.5, y=0.5)
            return fig
        
        # Create timeline data
        timeline_data = []
        for entry in filtered_log[:50]:  # Limit to first 50 events
            time_step = entry.get('time_step', 0)
            event_type = entry.get('event', 'unknown')
            
            timeline_data.append({
                'Time_Step': time_step,
                'Event': event_type.replace('_', ' ').title(),
                'Description': f"{entry.get('vessel_id', entry.get('rake_id', 'N/A'))} - {entry.get('port_id', entry.get('plant_id', 'N/A'))}",
                'Value': 1
            })
        
        df_timeline = pd.DataFrame(timeline_data)
        
        # Create scatter plot timeline
        fig = px.scatter(
            df_timeline, 
            x='Time_Step', 
            y='Event',
            hover_data=['Description'],
            title="Simulation Timeline - Key Events"
        )
        
        fig.update_traces(marker=dict(size=8))
        fig.update_layout(
            height=400,
            xaxis_title="Time Steps",
            yaxis_title="Event Type"
        )
        
        return fig