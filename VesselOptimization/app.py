"""
Main Dash application for SIH Logistics Optimization Simulator
Production-quality web interface with interactive optimization and visualization
"""
import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import json
import time
import io
import zipfile
from typing import Dict, List, Optional

# Import our modules
from data_loader import DataLoader
from milp_optimizer import MILPOptimizer
from heuristics import HeuristicOptimizer
from simulation import LogisticsSimulator
from visuals import LogisticsVisualizer
from utils import ETAPredictor, ScenarioGenerator, calculate_kpis, format_currency
from seed_utils import reseed_for_phase, set_global_seed

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP
    ],
    suppress_callback_exceptions=True
)

app.title = "SIH Logistics Optimization Simulator"

# Establish a deterministic baseline seed for all stochastic components.
BASE_RANDOM_SEED = set_global_seed(quiet=True)

# Global variables for storing data and results
current_data = None
current_solution = None
current_simulation = None
baseline_solution = None

# Initialize ETA predictor
eta_predictor = ETAPredictor()


def get_data_frames(stored_data: Optional[str]) -> Dict[str, pd.DataFrame]:
    """Rehydrate cached dataset JSON back into pandas DataFrames."""
    if not stored_data:
        return {}

    try:
        if isinstance(stored_data, str):
            data_dict = json.loads(stored_data)
        else:
            data_dict = stored_data

        if not isinstance(data_dict, dict):
            return {}

        frames = {}
        for name, records in data_dict.items():
            try:
                frames[name] = pd.DataFrame(records)
            except Exception:
                frames[name] = pd.DataFrame()
        return frames
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}


def parse_solution_payload(stored_solution: Optional[str]) -> Dict:
    """Return a dict representation of the stored solution payload."""
    if not stored_solution:
        return {}

    if isinstance(stored_solution, dict):
        return stored_solution

    try:
        return json.loads(stored_solution)
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}


def build_dispatch_export(trigger_source: str,
                          stored_solution: Optional[str],
                          stored_simulation: Optional[str],
                          stored_data: Optional[str]):
    """Create dispatch export payload based on trigger source."""
    solution = parse_solution_payload(stored_solution)
    assignments = solution.get('assignments', []) if isinstance(solution, dict) else []
    if not assignments:
        print("Dispatch export skipped: no assignments available.")
        return None

    df = pd.DataFrame(assignments)
    if df.empty:
        print("Dispatch export skipped: assignment dataframe empty.")
        return None

    if trigger_source == "export-csv-btn":
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_buffer:
            zip_buffer.writestr("dispatch_plan.csv", df.to_csv(index=False))

            simulation = parse_solution_payload(stored_simulation)
            data_frames = get_data_frames(stored_data)

            kpis = solution.get('kpis', {})
            if not kpis and isinstance(simulation, dict):
                kpis = simulation.get('kpis', {})

            if not kpis and data_frames:
                kpis = calculate_kpis(
                    assignments,
                    data_frames.get('vessels', pd.DataFrame()),
                    data_frames.get('plants', pd.DataFrame()),
                    simulation.get('kpis') if isinstance(simulation, dict) else None,
                    data_frames.get('ports', pd.DataFrame()),
                    data_frames.get('rail_costs', pd.DataFrame())
                )

            if kpis:
                kpi_df = pd.DataFrame([kpis])
                zip_buffer.writestr("kpi_summary.csv", kpi_df.to_csv(index=False))

            try:
                summary_df = (
                    df.groupby(['port_id', 'plant_id'], dropna=False)
                      .agg(assignments=('vessel_id', 'count'), cargo_mt=('cargo_mt', 'sum'))
                      .reset_index()
                )
                zip_buffer.writestr("port_plant_summary.csv", summary_df.to_csv(index=False))
            except Exception as exc:
                print(f"Dispatch export summary error: {exc}")

            summary_lines = [
                "SIH Logistics Optimization Export",
                "This archive contains the current dispatch plan and KPIs.",
                "Files:",
                "- dispatch_plan.csv: Vessel to plant assignments with timing.",
                "- kpi_summary.csv: Key performance indicators (if available).",
                "Generated by the sidebar Export CSV button.",
                f"Assignments exported: {len(df)}"
            ]
            zip_buffer.writestr("README.txt", "\n".join(summary_lines))

        buffer.seek(0)
        return dcc.send_bytes(buffer.getvalue(), "dispatch_export_bundle.zip")

    return dcc.send_data_frame(df.to_csv, filename="dispatch_plan.csv", index=False)


def build_sap_export(trigger_source: str,
                     stored_solution: Optional[str],
                     stored_data: Optional[str]):
    """Create SAP export payload based on trigger source."""
    solution = parse_solution_payload(stored_solution)
    data_frames = get_data_frames(stored_data)

    assignments = pd.DataFrame(solution.get('assignments', [])) if isinstance(solution, dict) else pd.DataFrame()
    vessels = data_frames.get('vessels', pd.DataFrame())

    if assignments.empty:
        print("SAP export skipped: no assignments available.")
        return None

    sap = assignments.merge(
        vessels[['vessel_id', 'eta_day', 'port_id']].drop_duplicates(),
        on='vessel_id', how='left'
    )
    sap = sap.rename(columns={
        'vessel_id': 'Vessel',
        'port_id': 'Port',
        'plant_id': 'Plant',
        'cargo_mt': 'Quantity_MT',
        'time_period': 'Planned_Day',
        'berth_time': 'Planned_Berth_Day'
    })

    cols = ['Vessel', 'Port', 'Plant', 'Quantity_MT', 'Planned_Day', 'Planned_Berth_Day', 'eta_day']
    for c in cols:
        if c not in sap.columns:
            sap[c] = None
    sap = sap[cols]

    if trigger_source == "export-sap-btn":
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_buffer:
            zip_buffer.writestr("sap_dispatch_template.csv", sap.to_csv(index=False))

            if not vessels.empty:
                meta_cols = ['_id', 'vessel_id', 'cargo_mt', 'eta_day', 'port_id', 'demurrage_rate']
                available_meta_cols = [col for col in meta_cols if col in vessels.columns]
                if available_meta_cols:
                    vessel_meta = vessels[available_meta_cols].copy()
                    if '_id' in vessel_meta.columns:
                        vessel_meta = vessel_meta.rename(columns={'_id': 'RecordID'})
                    zip_buffer.writestr("vessel_metadata.csv", vessel_meta.to_csv(index=False))

            zip_buffer.writestr("assignment_details.csv", assignments.to_csv(index=False))

            instructions = [
                "SAP Upload Package",
                "Use sap_dispatch_template.csv to upload into SAP.",
                "Reference vessel_metadata.csv for demurrage and ETA information.",
                "Generated via the sidebar Export SAP button."
            ]
            zip_buffer.writestr("README.txt", "\n".join(instructions))

        buffer.seek(0)
        return dcc.send_bytes(buffer.getvalue(), "sap_export_bundle.zip")

    return dcc.send_data_frame(sap.to_csv, filename="dispatch_sap_export.csv", index=False)


def make_json_safe(value):
    """Recursively convert numpy/pandas objects to JSON-safe Python types."""
    if isinstance(value, dict):
        return {key: make_json_safe(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [make_json_safe(item) for item in value]
    if isinstance(value, (np.integer, np.int64, np.int32)):
        return int(value)
    if isinstance(value, (np.floating, np.float64, np.float32)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, pd.DataFrame):
        return value.to_dict("records")
    if isinstance(value, (pd.Series, pd.Index)):
        return value.tolist()
    return value


def attach_solution_kpis(solution: Dict, data_frames: Dict[str, pd.DataFrame],
                         simulation_results: Optional[Dict] = None) -> Dict:
    """Compute and embed KPI metrics into the solution payload."""
    try:
        assignments = solution.get('assignments', [])
        vessels_df = data_frames.get('vessels', pd.DataFrame())
        plants_df = data_frames.get('plants', pd.DataFrame())
        ports_df = data_frames.get('ports', pd.DataFrame())
        rail_costs_df = data_frames.get('rail_costs', pd.DataFrame())

        kpis = calculate_kpis(
            assignments,
            vessels_df,
            plants_df,
            simulation_results,
            ports_df,
            rail_costs_df
        )
        solution['kpis'] = kpis
    except Exception as exc:
        print(f"Solution KPI attachment error: {exc}")
    return solution

def create_header():
    """Create application header"""
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.NavbarBrand("Port-Plant Logistics Optimization System", className="fw-bold"),
                    html.Small(
                        "System-driven planning for eastern India steel supply chains",
                        className="text-muted"
                    )
                ], width="auto"),
                dbc.Col(
                    dbc.Badge("Enterprise preview", color="secondary"),
                    width="auto", className="ms-auto"
                )
            ], align="center", className="w-100 flex-wrap")
        ], fluid=True),
        color="primary",
        dark=True,
        className="mb-3"
    )


def create_controls_panel():
    """Create left controls panel"""
    return dbc.Card([
        dbc.CardHeader(html.H5("Planning controls", className="mb-0")),
        dbc.CardBody([
            html.H6("Data management", className="text-primary mb-3"),
            dbc.ButtonGroup([
                dbc.Button("Load sample data", id="load-sample-btn", color="primary", size="sm"),
                dbc.Button("CSV guide", id="csv-guide-btn", color="info", size="sm", outline=True)
            ], className="mb-3 w-100"),

            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    html.Strong("Upload planning datasets"),
                    html.P("Drag and drop or choose CSV files.", className="text-muted small mb-2"),
                    html.Small(
                        [
                            "Required files: ",
                            html.Code("vessels.csv"), ", ",
                            html.Code("ports.csv"), ", ",
                            html.Code("plants.csv"), ", ",
                            html.Code("rail_costs.csv")
                        ],
                        className="text-muted"
                    )
                ], className="text-center"),
                style={
                    'width': '100%', 'minHeight': '120px', 'lineHeight': '1.4',
                    'borderWidth': '2px', 'borderStyle': 'dashed',
                    'borderRadius': '8px', 'textAlign': 'center',
                    'padding': '20px', 'backgroundColor': '#f8f9fa'
                },
                multiple=True,
                className="mb-3"
            ),

            html.Div(id="data-status", className="mb-3"),

            dbc.Collapse([
                dbc.Card([
                    dbc.CardHeader("CSV format guide", className="bg-info text-white"),
                    dbc.CardBody([
                        html.P("Required CSV files and their columns:", className="fw-bold"),
                        html.Ul([
                            html.Li([html.Code("vessels.csv"), ": vessel_id, cargo_mt, eta_day, port_id, demurrage_rate, cargo_grade"]),
                            html.Li([html.Code("ports.csv"), ": port_id, port_name, handling_cost_per_mt, daily_capacity_mt, rakes_available_per_day"]),
                            html.Li([html.Code("plants.csv"), ": plant_id, plant_name, daily_demand_mt, quality_requirements"]),
                            html.Li([html.Code("rail_costs.csv"), ": port_id, plant_id, cost_per_mt, distance_km, transit_days"])
                        ]),
                        dbc.Button("Download templates", id="download-templates-btn", color="light", size="sm", className="mt-2")
                    ])
                ])
            ], id="csv-guide-collapse", is_open=False, className="mb-3"),

            html.Hr(),

            html.H6("Scenario planning", className="text-primary mb-2"),
            html.P(
                "Adjust assumptions before solving to test sensitivity to delays, rake availability, and demand changes.",
                className="text-muted small mb-3"
            ),
            dbc.Label("ETA delay profile"),
            dcc.Dropdown(
                id="eta-delay-scenario",
                options=[
                    {"label": "No additional delay", "value": "none"},
                    {"label": "Weather disruption (+12h)", "value": "moderate"},
                    {"label": "Port congestion (+24h)", "value": "severe"}
                ],
                value="none",
                className="mb-3"
            ),
            dbc.Label("Rake availability reduction (%)"),
            dcc.Slider(
                id="rake-reduction",
                min=0,
                max=50,
                step=5,
                value=0,
                marks={i: f"{i}%" for i in range(0, 55, 10)},
                tooltip={"placement": "bottom", "always_visible": False}
            ),
            html.Div(id="rake-reduction-value", className="text-muted small mb-3"),

            dbc.Label("Demand spike (%)"),
            dbc.Row([
                dbc.Col(dbc.Input(id="demand-spike", type="number", value=0, min=0, max=100)),
                dbc.Col(dbc.FormText("Applies to selected plant", className="text-muted"))
            ], className="align-items-center g-2 mb-3"),

            dbc.Label("Target plant for spike"),
            dcc.Dropdown(id="spike-plant", className="mb-3"),

            html.Hr(),

            html.H6("Execution", className="text-primary mb-3"),
            dbc.Button("Run baseline plan", id="run-baseline-btn", color="secondary", size="sm", className="mb-2 w-100"),
            dbc.Button("Run optimized plan", id="run-optimized-btn", color="success", size="sm", className="mb-2 w-100"),
            dbc.Button("Simulate dispatch performance", id="run-simulation-btn", color="info", size="sm", className="mb-2 w-100"),
            dbc.Button("Compare scenario outcomes", id="compare-scenarios-btn", color="warning", size="sm", className="mb-3 w-100"),
            dbc.FormText(
                "Run the baseline plan first, then generate an optimized plan before launching simulation, comparison, or exports.",
                className="text-muted mb-3"
            ),

            dbc.Accordion([
                dbc.AccordionItem([
                    html.P(
                        "Tune solver parameters before running the optimized plan.",
                        className="text-muted small mb-3"
                    ),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Optimization method"),
                            dcc.Dropdown(
                                id="optimization-method",
                                options=[
                                    {"label": "MILP (exact optimization)", "value": "milp"},
                                    {"label": "Genetic algorithm", "value": "ga"},
                                    {"label": "MILP warm start + GA", "value": "milp_ga"},
                                    {"label": "Hybrid (MILP + GA + SA)", "value": "hybrid"}
                                ],
                                value="milp",
                                clearable=False
                            )
                        ], md=6),
                        dbc.Col([
                            dbc.Label("MILP solver"),
                            dcc.Dropdown(
                                id="solver-selection",
                                options=[
                                    {"label": "PuLP CBC", "value": "CBC"},
                                    {"label": "Gurobi", "value": "GUROBI"}
                                ],
                                value="CBC",
                                clearable=False
                            )
                        ], md=6)
                    ], className="g-3 mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("MILP time limit (seconds)"),
                            dbc.Input(
                                id="time-limit",
                                type="number",
                                value=300,
                                min=60,
                                max=3600,
                                step=30
                            ),
                            dbc.FormText("Increase for harder planning problems.", className="text-muted")
                        ], md=6),
                        dbc.Col([
                            dbc.Label("GA generations"),
                            dbc.Input(
                                id="ga-generations",
                                type="number",
                                value=40,
                                min=10,
                                max=200,
                                step=5
                            ),
                            dbc.FormText("Higher values improve quality but take longer.", className="text-muted")
                        ], md=6)
                    ], className="g-3")
                ], title="Advanced optimization settings", item_id="advanced-optimization")
            ], start_collapsed=True, flush=True, className="mb-3"),

            html.Hr(),
            html.H6("Exports", className="text-primary mb-3"),
            dbc.ButtonGroup([
                dbc.Button("Dispatch bundle (ZIP)", id="export-csv-btn", color="outline-dark", size="sm", className="w-50"),
                dbc.Button("SAP bundle (ZIP)", id="export-sap-btn", color="outline-dark", size="sm", className="w-50")
            ], className="mb-3"),

            dbc.Alert(id="action-status", color="light", className="mb-0", style={"display": "none"}),
            dbc.Alert(id="simulation-status", color="light", className="mt-3", style={"display": "none"})
        ])
    ], className="h-100")

def create_main_content():
    """Create main content area with tabs"""
    return dbc.Card([
        dbc.CardHeader([
            dbc.Tabs(
                id="main-tabs",
                active_tab="overview",
                className="tabs-with-export",
                children=[
                    dbc.Tab(label="Overview", tab_id="overview"),
                    dbc.Tab(label="Gantt & Schedules", tab_id="gantt"),
                    dbc.Tab(label="Cost Breakdown", tab_id="costs"),
                    dbc.Tab(label="Rake Dashboard", tab_id="rakes"),
                    dbc.Tab(label="Simulation Comparator", tab_id="simcompare"),
                    dbc.Tab(label="Scenario Analysis", tab_id="whatif"),
                    dbc.Tab(
                        label="Logs & Export",
                        tab_id="logs",
                        tabClassName="ms-auto",
                        tab_style={"whiteSpace": "nowrap"}
                    )
                ]
            )
        ]),
        dbc.CardBody([
            html.Div(id="tab-content")
        ])
    ])

def create_overview_tab():
    """Create overview tab content"""
    return html.Div([
        # KPI Cards Row
        dbc.Row(id="kpi-cards-row", className="mb-4"),
        
        # Charts Row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("System Status"),
                    dbc.CardBody([
                        html.Div(id="system-status")
                    ])
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Quick Insights"),
                    dbc.CardBody([
                        html.Div(id="quick-insights")
                    ])
                ])
            ], width=8)
        ], className="mb-4"),
        
        # Data Summary
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Data Summary"),
                    dbc.CardBody([
                        html.Div(id="data-summary-table")
                    ])
                ])
            ], width=12)
        ])
    ])

def create_gantt_tab():
    """Create Gantt chart tab content"""
    return html.Div([
        dbc.Alert([
            html.H6("Timeline interpretation", className="mb-2"),
            html.P(
                "The schedule view plots each vessel from ETA through completion of unloading. "
                "Use it to confirm berth sequencing, overlaps, and demurrage exposure.",
                className="mb-2"
            ),
            html.Ul([
                html.Li("Each bar spans the handling window for a vessel."),
                html.Li("The y-axis lists vessels; the x-axis shows elapsed days."),
                html.Li("Hover to see assigned port, plant destination, cargo tonnage, and timing."),
                html.Li("Look for bars extending beyond ETA to spot likely demurrage.")
            ], className="mb-0 small")
        ], color="light", className="mb-3 border"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(
                        dbc.Row([
                            dbc.Col(html.Strong("Vessel and rake schedule timeline"), align="center"),
                            dbc.Col(
                                dbc.ButtonGroup([
                                    dbc.Button("Refresh", id="refresh-gantt-btn", size="sm", color="outline-primary"),
                                    dbc.Button("Export", id="export-gantt-btn", size="sm", color="outline-secondary")
                                ], className="float-end"),
                                width="auto",
                                align="center"
                            )
                        ], className="g-2"),
                        className="d-flex align-items-center"
                    ),
                    dbc.CardBody([
                        dcc.Graph(id="gantt-chart", style={"height": "600px"})
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Schedule details"),
                    dbc.CardBody([
                        html.Div(id="schedule-details")
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Schedule summary"),
                    dbc.CardBody([
                        html.Div(id="schedule-summary")
                    ])
                ])
            ], width=6)
        ])
    ])

def create_cost_tab():
    """Create cost breakdown tab content"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.Strong("Cost structure")),
                    dbc.CardBody([
                        html.P(
                            "Break down total logistics cost into handling, rail, and demurrage components. "
                            "Use the chart to pinpoint where scenario changes drive savings or penalties.",
                            className="text-muted small"
                        ),
                        dcc.Graph(id="cost-breakdown-chart", style={"height": "420px"})
                    ])
                ])
            ], width=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Key cost drivers"),
                    dbc.CardBody([
                        html.Div(id="cost-drivers-analysis")
                    ])
                ])
            ], width=4)
        ], className="mb-4"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Cost timeline and baseline comparison"),
                    dbc.CardBody([
                        dcc.Graph(id="cost-timeline-chart", style={"height": "400px"})
                    ])
                ])
            ], width=12)
        ])
    ])

def create_rake_tab():
    """Create rake dashboard tab content"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.Strong("Rake utilization heatmap")),
                    dbc.CardBody([
                        html.P(
                            "Assess rake loading intensity across the horizon. Darker cells indicate higher trip counts per port/plant pair.",
                            className="text-muted small"
                        ),
                        dcc.Graph(id="rake-heatmap", style={"height": "400px"})
                    ])
                ])
            ], width=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Rake statistics"),
                    dbc.CardBody([
                        html.Div(id="rake-statistics")
                    ])
                ])
            ], width=4)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Rake assignment detail"),
                    dbc.CardBody([
                        html.Div(id="rake-assignment-table")
                    ])
                ])
            ], width=12)
        ])
    ])


def create_simulation_tab():
    """Create simulation comparator tab content"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.H6("Simulation fidelity review", className="mb-2"),
                    html.P(
                        "Benchmark the optimized plan against simulated execution. Run the simulation to see realized costs, service levels, and asset utilization side by side.",
                        className="mb-0"
                    )
                ], color="light", className="mb-3 border")
            ])
        ]),

        dbc.Row([
            dbc.Col([
                dcc.Loading(
                    id="simulation-summary-loading",
                    type="default",
                    className="w-100",
                    children=dbc.Card([
                        dbc.CardHeader("Execution status", className="fw-semibold"),
                        dbc.CardBody([
                            html.Div(id="simulation-comparator-summary")
                        ])
                    ])
                )
            ], width=4),
            dbc.Col([
                dcc.Loading(
                    id="simulation-kpi-loading",
                    type="default",
                    className="w-100",
                    children=dbc.Card([
                        dbc.CardHeader("Service & cost headline KPIs", className="fw-semibold"),
                        dbc.CardBody([
                            html.Div(id="simulation-kpi-cards")
                        ])
                    ])
                )
            ], width=8)
        ], className="mb-4 g-3"),

        dbc.Row([
            dbc.Col([
                dcc.Loading(
                    id="simulation-chart-loading",
                    type="default",
                    className="w-100",
                    children=dbc.Card([
                        dbc.CardHeader("Plan vs simulated cost structure", className="fw-semibold"),
                        dbc.CardBody([
                            dcc.Graph(id="simulation-performance-chart", style={"height": "380px"})
                        ])
                    ])
                )
            ], width=8),
            dbc.Col([
                dcc.Loading(
                    id="simulation-table-loading",
                    type="circle",
                    className="w-100",
                    children=dbc.Card([
                        dbc.CardHeader("Readiness checklist", className="fw-semibold"),
                        dbc.CardBody([
                            html.Div(id="simulation-readiness-list")
                        ])
                    ])
                )
            ], width=4)
        ], className="mb-4 g-3"),

        dbc.Row([
            dbc.Col([
                dcc.Loading(
                    id="simulation-detail-loading",
                    type="circle",
                    className="w-100",
                    children=dbc.Card([
                        dbc.CardHeader("Detailed variance matrix", className="fw-semibold"),
                        dbc.CardBody([
                            html.Div(id="simulation-variance-table")
                        ])
                    ])
                )
            ])
        ])
    ])

# App Layout
app.layout = dbc.Container([
    create_header(),
    
    dbc.Row([
        dbc.Col([
            create_controls_panel()
        ], width=3),
        dbc.Col([
            create_main_content()
        ], width=9)
    ]),
    
    # Hidden divs for storing data
    html.Div(id="stored-data", style={"display": "none"}),
    html.Div(id="stored-solution", style={"display": "none"}),
    html.Div(id="stored-simulation", style={"display": "none"}),

    dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle("Scenario comparison overview"),
                close_button=False
            ),
            dbc.ModalBody([
                html.Div(id="modal-scenario-summary", className="mb-3"),
                dcc.Graph(id="modal-scenario-chart", style={"height": "320px"}),
                html.Div(id="modal-scenario-meta", className="small mt-3")
            ]),
            dbc.ModalFooter(
                dbc.Button("Close", id="scenario-modal-close", color="secondary")
            )
        ],
        id="scenario-comparison-modal",
        is_open=False,
        size="xl",
        centered=True,
        scrollable=True,
        backdrop="static"
    ),

    # Download targets (kept global so buttons work from any tab)
    dcc.Download(id="download-dispatch-csv-file"),
    dcc.Download(id="download-sap-file"),
    dcc.Download(id="download-full-report-file"),
    dcc.Download(id="download-gantt-csv"),
    dcc.Download(id="sample-csv-download"),
    
    # Interval component for progress updates
    dcc.Interval(id="progress-interval", interval=1000, n_intervals=0, disabled=True)
    
], fluid=True)

# Callbacks

@app.callback(
    [Output("stored-data", "children"),
     Output("data-status", "children"),
     Output("spike-plant", "options")],
    [Input("load-sample-btn", "n_clicks"),
     Input("upload-data", "contents")],
    [State("upload-data", "filename")]
)
def load_data(load_sample_clicks, upload_contents, upload_filenames):
    """Load sample data or process uploaded files"""
    global current_data
    
    ctx = callback_context
    if not ctx.triggered:
        return None, "", []
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "load-sample-btn" and load_sample_clicks:
        # Load sample data
        set_global_seed(BASE_RANDOM_SEED, quiet=True)
        current_data = DataLoader.get_toy_dataset()
        # Restore the base seed so downstream stages start from the same RNG state
        set_global_seed(BASE_RANDOM_SEED, quiet=True)
        
        status = dbc.Alert("Sample data loaded successfully.", color="success")
        
        # Plant options for spike scenario
        plant_options = [
            {"label": row['plant_name'], "value": row['plant_id']} 
            for _, row in current_data['plants'].iterrows()
        ]
        
        return json.dumps({k: v.to_dict('records') for k, v in current_data.items()}), status, plant_options
    
    elif trigger_id == "upload-data" and upload_contents:
        # Process uploaded files
        try:
            uploaded_data = {}
            for content, filename in zip(upload_contents, upload_filenames):
                df = DataLoader.parse_uploaded_file(content, filename)
                if df is not None:
                    # Determine dataset type from filename
                    if 'vessel' in filename.lower():
                        uploaded_data['vessels'] = df
                    elif 'port' in filename.lower():
                        uploaded_data['ports'] = df
                    elif 'plant' in filename.lower():
                        uploaded_data['plants'] = df
                    elif 'rail' in filename.lower():
                        uploaded_data['rail_costs'] = df
            
            cleaned_data = DataLoader.standardize_dataset(uploaded_data)

            # Validate uploaded data
            is_valid, errors = DataLoader.validate_csv_data(cleaned_data)
            
            if is_valid:
                current_data = cleaned_data
                status = dbc.Alert(
                    f"Uploaded {len(uploaded_data)} datasets successfully.",
                    color="success"
                )
                
                plant_options = [
                    {"label": row.get('plant_name', row['plant_id']), "value": row['plant_id']} 
                    for _, row in current_data['plants'].iterrows()
                ]
                
                return json.dumps({k: v.to_dict('records') for k, v in current_data.items()}), status, plant_options
            else:
                status = dbc.Alert(
                    html.Div([html.Strong("Data checks:"), html.Ul([html.Li(err) for err in errors])]),
                    color="danger"
                )
                
                return None, status, []
                
        except Exception as e:
            status = dbc.Alert(f"Error processing uploaded files: {str(e)}", color="danger")
            
            return None, status, []
    
    return None, "", []

# Toggle CSV guide
@app.callback(
    Output("csv-guide-collapse", "is_open"),
    [Input("csv-guide-btn", "n_clicks")],
    [State("csv-guide-collapse", "is_open")]
)
def toggle_csv_guide(n_clicks, is_open):
    """Toggle CSV format guide"""
    if n_clicks:
        return not is_open
    return is_open

@app.callback(
    Output("tab-content", "children"),
    [Input("main-tabs", "active_tab")]
)
def render_tab_content(active_tab):
    """Render content based on active tab"""
    if active_tab == "overview":
        return create_overview_tab()
    elif active_tab == "gantt":
        return create_gantt_tab()
    elif active_tab == "costs":
        return create_cost_tab()
    elif active_tab == "rakes":
        return create_rake_tab()
    elif active_tab == "simcompare":
        return create_simulation_tab()
    elif active_tab == "whatif":
        return create_whatif_tab()
    elif active_tab == "logs":
        return create_logs_tab()
    else:
        return html.Div("Select a tab to view content")

def create_whatif_tab():
    """Create what-if analysis tab"""
    return html.Div([
        dbc.Alert([
            html.H6("Scenario comparison", className="mb-2"),
            html.P(
                "Use this workspace to evaluate the financial and operational impact of alternate planning assumptions. "
                "Run multiple scenarios from the control panel, then review their KPIs and cost differentials side by side.",
                className="mb-0"
            )
        ], color="light", className="mb-3 border"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Scenario summary"),
                    dbc.CardBody([
                        html.Div(id="scenario-comparison-summary")
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Scenario impact analysis"),
                    dbc.CardBody([
                        dcc.Graph(id="scenario-comparison-chart", style={"height": "500px"})
                    ])
                ])
            ], width=12)
        ])
    ])

def create_logs_tab():
    """Create logs and export tab"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Optimization logs"),
                    dbc.CardBody([
                        html.Div(id="solver-logs", style={"maxHeight": "300px", "overflowY": "auto"})
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Audit trail"),
                    dbc.CardBody([
                        html.Div(id="audit-trail")
                    ])
                ])
            ], width=6)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Export deliverables"),
                    dbc.CardBody([
                        dbc.Alert(
                            "Downloads become available after a plan is generated. Run baseline and optimized plans first. Use the buttons here for quick CSVs, or the sidebar export controls for a zipped planning bundle.",
                            color="light",
                            className="mb-3 border"
                        ),
                        html.H6("Download planning outputs", className="mb-3"),
                        dbc.ButtonGroup([
                            dbc.Button("Dispatch plan (CSV)", id="download-dispatch-csv", color="primary", className="mb-2"),
                            dbc.Button("SAP upload template", id="download-sap-format", color="secondary", className="mb-2"),
                            dbc.Button("Full JSON report", id="download-full-report", color="info", className="mb-2")
                        ], vertical=True, className="w-100"),
                        html.Hr(),
                        html.H6("Preview sample rows", className="mt-3"),
                        html.Div(id="export-preview")
                    ])
                ])
            ], width=12)
        ])
    ])

@app.callback(
    [Output("stored-solution", "children"),
     Output("action-status", "children"),
     Output("action-status", "color"),
     Output("action-status", "style")],
    [Input("run-baseline-btn", "n_clicks"),
     Input("run-optimized-btn", "n_clicks")],
    [State("stored-data", "children"),
     State("optimization-method", "value"),
     State("solver-selection", "value"),
     State("time-limit", "value"),
     State("ga-generations", "value"),
     State("eta-delay-scenario", "value"),
     State("rake-reduction", "value"),
     State("demand-spike", "value"),
     State("spike-plant", "value")]
)
def run_optimization(baseline_clicks, optimized_clicks, stored_data, opt_method, 
                    solver, time_limit, ga_generations, eta_delay, rake_reduction, 
                    demand_spike, spike_plant):
    """Run optimization based on selected method"""
    global current_solution, baseline_solution
    
    ctx = callback_context
    if not ctx.triggered or not stored_data:
        return None, "", "light", {"display": "none"}
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Reset RNGs so repeated runs with the same data stay deterministic.
    set_global_seed(BASE_RANDOM_SEED, quiet=True)
    phase_label = {
        "run-baseline-btn": "baseline",
        "run-optimized-btn": "optimized"
    }.get(trigger_id, "optimization")
    active_seed = reseed_for_phase(f"optimization::{phase_label}", quiet=True)
    opt_method = (opt_method or "milp").lower()
    solver = (solver or "CBC").upper()
    try:
        time_limit = int(time_limit) if time_limit else 300
    except (TypeError, ValueError):
        time_limit = 300
    if time_limit <= 0:
        time_limit = 300
    try:
        ga_generations = int(ga_generations) if ga_generations else 40
    except (TypeError, ValueError):
        ga_generations = 40
    if ga_generations <= 0:
        ga_generations = 40
    
    try:
        # Reconstruct data from stored JSON
        data_dict = json.loads(stored_data)
        data = {k: pd.DataFrame(v) for k, v in data_dict.items()}
        
        # Apply scenario modifications
        if eta_delay != "none":
            data['vessels'] = ScenarioGenerator.apply_eta_delays(data['vessels'], eta_delay)
        
        if rake_reduction > 0:
            data['ports'] = ScenarioGenerator.reduce_rake_availability(data['ports'], rake_reduction)
        
        if demand_spike > 0 and spike_plant:
            data['plants'] = ScenarioGenerator.spike_plant_demand(data['plants'], spike_plant, demand_spike)
        
        if trigger_id == "run-baseline-btn":
            # Run baseline FCFS solution
            status_msg = html.Div("Running baseline FCFS optimization...")
            status_color = "info"
            
            milp_optimizer = MILPOptimizer(data)
            solution = milp_optimizer.create_baseline_solution()
            solution['rng_seed'] = active_seed
            solution = attach_solution_kpis(solution, data)
            solution = make_json_safe(solution)
            baseline_solution = solution
            current_solution = solution
            
            status_msg = html.Div(
                f"Baseline plan completed. Cost: {format_currency(solution.get('objective_value', 0))}"
            )
            status_color = "success"
            
        elif trigger_id == "run-optimized-btn":
            # Run selected optimization method
            status_msg = html.Div(f"Running {opt_method.upper()} optimization...")
            status_color = "info"
            
            if opt_method == "milp":
                milp_optimizer = MILPOptimizer(data)
                solution = milp_optimizer.solve_milp(solver, time_limit)
                
            elif opt_method == "ga":
                heuristic_optimizer = HeuristicOptimizer(data)
                solution = heuristic_optimizer.run_genetic_algorithm(
                    population_size=30, generations=ga_generations
                )
                
            elif opt_method == "milp_ga":
                # MILP + GA pipeline
                milp_optimizer = MILPOptimizer(data)
                milp_solution = milp_optimizer.solve_milp(solver, time_limit // 2)
                
                heuristic_optimizer = HeuristicOptimizer(data)
                solution = heuristic_optimizer.run_genetic_algorithm(
                    population_size=20, generations=ga_generations // 2,
                    seed_solution=milp_solution.get('assignments', [])
                )
                
            elif opt_method == "hybrid":
                # Full hybrid pipeline: MILP + GA + SA
                milp_optimizer = MILPOptimizer(data)
                milp_solution = milp_optimizer.solve_milp(solver, time_limit // 3)
                
                heuristic_optimizer = HeuristicOptimizer(data)
                ga_solution = heuristic_optimizer.run_genetic_algorithm(
                    population_size=20, generations=ga_generations // 2,
                    seed_solution=milp_solution.get('assignments', [])
                )
                
                solution = heuristic_optimizer.run_simulated_annealing(
                    ga_solution, max_iterations=500
                )
            
            if isinstance(solution, dict):
                solution['rng_seed'] = active_seed
            solution = attach_solution_kpis(solution, data)
            solution = make_json_safe(solution)
            current_solution = solution
            
            # Calculate savings if baseline exists
            savings_msg = ""
            if baseline_solution:
                baseline_cost = baseline_solution.get('objective_value', 0)
                optimized_cost = solution.get('objective_value', 0)
                
                # Sanity checks
                if baseline_cost <= 0:
                    savings_msg = " | Baseline cost is zero or invalid."
                elif optimized_cost < 0:
                    savings_msg = " | Optimized cost is negative. Review solver configuration."
                elif optimized_cost > baseline_cost:
                    # Optimization made it worse - this can happen with constraints
                    penalty = optimized_cost - baseline_cost
                    penalty_pct = (penalty / baseline_cost * 100)
                    savings_msg = f" | Cost increased by {format_currency(penalty)} (+{penalty_pct:.1f}%). Review constraints."
                else:
                    savings = baseline_cost - optimized_cost
                    savings_pct = (savings / baseline_cost * 100) if baseline_cost > 0 else 0
                    
                    # Cap at 95% for display (100% is impossible in real logistics)
                    if savings_pct > 95:
                        savings_msg = f" | Savings: {format_currency(savings)} (~{min(savings_pct, 99):.0f}% - exceptional)."
                    else:
                        savings_msg = f" | Savings: {format_currency(savings)} ({savings_pct:.1f}%)."
            
            status_msg = html.Div(
                f"Optimized plan available. Cost: {format_currency(solution.get('objective_value', 0))}{savings_msg}"
            )
            status_color = "success"
        
        # Store solution
        solution_json = json.dumps(solution, default=str)
        
        return solution_json, status_msg, status_color, {"display": "block"}
        
    except Exception as e:
        error_msg = html.Div(f"Error: {str(e)}")
        return None, error_msg, "danger", {"display": "block"}

@app.callback(
    [Output("stored-simulation", "children"),
     Output("simulation-status", "children"),
     Output("simulation-status", "color"),
     Output("simulation-status", "style")],
    [Input("run-simulation-btn", "n_clicks")],
    [State("stored-data", "children"),
     State("stored-solution", "children")]
)
def run_simulation(simulation_clicks, stored_data, stored_solution):
    """Run discrete-time simulation"""
    global current_simulation, current_solution

    if not simulation_clicks or not stored_data or not stored_solution:
        return None, "", "light", {"display": "none"}

    set_global_seed(BASE_RANDOM_SEED, quiet=True)
    active_seed = reseed_for_phase("simulation", quiet=True)

    try:
        data = get_data_frames(stored_data)
        solution = parse_solution_payload(stored_solution)
        assignments = solution.get('assignments', []) if isinstance(solution, dict) else []

        if not assignments:
            print("Simulation skipped: no vessel assignments available.")
            current_simulation = None
            return json.dumps({
                "status": "no_assignments",
                "message": "Run a baseline or optimized plan before simulating."
            }), "No assignments available. Generate a plan first.", "warning", {"display": "block"}

        simulator = LogisticsSimulator(data, time_step_hours=6)
        simulation_results = simulator.run_simulation(assignments, simulation_days=30)
        simulation_results = make_json_safe(simulation_results)
        if isinstance(simulation_results, dict):
            simulation_results['rng_seed'] = active_seed

        current_simulation = simulation_results

        if current_solution:
            enriched_solution = attach_solution_kpis(current_solution, data, simulation_results)
            current_solution = make_json_safe(enriched_solution)

        message = f"Simulation completed for {len(assignments)} vessel assignments."
        if isinstance(simulation_results, dict) and simulation_results.get('simulation_days'):
            message += f" Horizon evaluated: {simulation_results['simulation_days']} days."

        return json.dumps(simulation_results), message, "info", {"display": "block"}

    except Exception as e:
        print(f"Simulation error: {e}")
        return None, f"Simulation error: {e}", "danger", {"display": "block"}


@app.callback(
    Output("download-dispatch-csv-file", "data"),
    [Input("download-dispatch-csv", "n_clicks"),
     Input("export-csv-btn", "n_clicks")],
    [State("stored-solution", "children"),
     State("stored-simulation", "children"),
     State("stored-data", "children")],
    prevent_initial_call=True
)
def download_dispatch_csv(_export_logs_clicks, _export_sidebar_clicks, stored_solution, stored_simulation, stored_data):
    ctx = callback_context
    if not ctx.triggered or not stored_solution:
        return None
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    trigger_clicks = 0
    if trigger_id == "download-dispatch-csv":
        trigger_clicks = _export_logs_clicks or 0
    elif trigger_id == "export-csv-btn":
        trigger_clicks = _export_sidebar_clicks or 0

    if trigger_clicks <= 0:
        return None
    try:
        return build_dispatch_export(trigger_id, stored_solution, stored_simulation, stored_data)
    except Exception as e:
        print(f"Dispatch export error: {e}")
        return None


@app.callback(
    Output("download-sap-file", "data"),
    [Input("download-sap-format", "n_clicks"),
     Input("export-sap-btn", "n_clicks")],
    [State("stored-solution", "children"),
     State("stored-data", "children")],
    prevent_initial_call=True
)
def download_sap_format(_export_logs_clicks, _export_sidebar_clicks, stored_solution, stored_data):
    ctx = callback_context
    if not ctx.triggered or not stored_solution or not stored_data:
        return None

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    trigger_clicks = 0
    if trigger_id == "download-sap-format":
        trigger_clicks = _export_logs_clicks or 0
    elif trigger_id == "export-sap-btn":
        trigger_clicks = _export_sidebar_clicks or 0

    if trigger_clicks <= 0:
        return None

    try:
        return build_sap_export(trigger_id, stored_solution, stored_data)
    except Exception as e:
        print(f"SAP export error: {e}")
        return None


@app.callback(
    Output("download-full-report-file", "data"),
    [Input("download-full-report", "n_clicks")],
    [State("stored-solution", "children"), State("stored-simulation", "children")],
    prevent_initial_call=True
)
def download_full_report(n_clicks, stored_solution, stored_simulation):
    if not n_clicks or not stored_solution:
        return None
    try:
        solution = json.loads(stored_solution)
        sim = json.loads(stored_simulation) if stored_simulation else {}
        report = {
            'solution_summary': {k: v for k, v in solution.items() if k != 'assignments'},
            'kpis': (sim.get('kpis') if sim else {}),
            'cost_components': (sim.get('cost_components') if sim else {}),
        }
        import io
        buf = io.StringIO()
        import json as _json
        buf.write(_json.dumps(report, indent=2))
        return dict(content=buf.getvalue(), filename="full_report.json")
    except Exception:
        return None

@app.callback(
    Output("kpi-cards-row", "children"),
    [Input("stored-solution", "children"),
     Input("stored-simulation", "children")],
    [State("stored-data", "children")]
)
def update_kpi_cards(stored_solution, stored_simulation, stored_data):
    """Update KPI cards in overview tab"""
    if not stored_solution:
        return []
    
    try:
        solution = parse_solution_payload(stored_solution)
        assignments = solution.get('assignments', []) if isinstance(solution, dict) else []
        simulation_results = json.loads(stored_simulation) if stored_simulation else None
        data_frames = {}
        if stored_data:
            data_dict = json.loads(stored_data)
            data_frames = {k: pd.DataFrame(v) for k, v in data_dict.items()}
        vessels_df = data_frames.get('vessels', pd.DataFrame())
        plants_df = data_frames.get('plants', pd.DataFrame())
        ports_df = data_frames.get('ports', pd.DataFrame())
        rail_costs_df = data_frames.get('rail_costs', pd.DataFrame())
        
        kpis = calculate_kpis(
            assignments,
            vessels_df,
            plants_df,
            simulation_results,
            ports_df,
            rail_costs_df
        )
        
        # If no simulation has been run yet, fall back to solution objective
        if not stored_simulation:
            kpis['total_cost'] = kpis.get('total_cost', solution.get('objective_value', 0))
            kpis['demurrage_cost'] = kpis.get('demurrage_cost', 0.0)
        
        # Get baseline KPIs for comparison
        baseline_kpis = None
        if baseline_solution:
            baseline_assignments = baseline_solution.get('assignments', [])
            baseline_kpis = calculate_kpis(
                baseline_assignments,
                vessels_df,
                plants_df,
                None,
                ports_df,
                rail_costs_df
            )
        
        # Create KPI cards
        cards_data = LogisticsVisualizer.create_kpi_cards(kpis, baseline_kpis)
        
        cards = []
        for card_data in cards_data:
            # Determine delta color
            delta_color = "secondary"
            if card_data['delta'] is not None and card_data['delta'] != 0:
                if card_data['title'] in ['Total Cost', 'Demurrage Cost', 'Avg Vessel Wait']:
                    delta_color = "success" if card_data['delta'] < 0 else "danger"
                else:
                    delta_color = "success" if card_data['delta'] > 0 else "danger"

            delta_display = None
            if card_data['delta_pct'] is not None:
                delta_display = html.Div(
                    f"Change vs baseline: {card_data['delta_pct']:+.1f}%",
                    className=f"text-{delta_color} small fw-semibold mt-1"
                )

            tooltip_content = html.Div([
                html.H6(
                    card_data.get('tooltip_title', card_data['title']),
                    className="kpi-tooltip-title mb-2"
                ),
                html.Div([
                    html.Strong("Formula: "),
                    html.Span(card_data.get('formula', 'N/A'), className="kpi-tooltip-formula")
                ], className="mb-2"),
                html.P(
                    card_data.get('description', ''),
                    className="kpi-tooltip-description mb-2 small"
                ),
                html.Div([
                    html.Strong("Key factors", className="d-block mb-1"),
                    html.Ul(
                        [html.Li(factor, className="mb-1") for factor in card_data.get('factors', [])],
                        className="kpi-tooltip-factors ps-3 mb-0"
                    )
                ])
            ], className="kpi-tooltip")

            card_classes = f"kpi-card kpi-card-{card_data['color']} h-100"
            if card_data.get('is_demurrage') and card_data['raw_value'] > 0:
                card_classes += " demurrage-card"

            demurrage_badge = None
            if card_data.get('is_demurrage') and card_data['raw_value'] > 0:
                demurrage_badge = html.Div(
                    "Penalty exposure",
                    className="demurrage-badge text-uppercase",
                    style={'fontSize': '11px', 'padding': '4px 8px'}
                )

            metric_section_children = [
                html.H3(card_data['value'], className="kpi-value mb-1"),
                html.P(card_data['title'], className="text-muted mb-1 fw-semibold")
            ]
            if delta_display:
                metric_section_children.append(delta_display)

            card_body_children = [tooltip_content]
            if demurrage_badge:
                card_body_children.append(demurrage_badge)
            card_body_children.append(
                html.Div(
                    metric_section_children,
                    className="text-center",
                    style={'position': 'relative', 'zIndex': 1}
                )
            )

            card = dbc.Col([
                dbc.Card(
                    dbc.CardBody(
                        card_body_children,
                        style={'position': 'relative'}
                    ),
                    className=card_classes,
                    style={'minHeight': '200px'}
                )
            ], width=2)
            
            cards.append(card)
        
        return cards
        
    except Exception as e:
        print(f"KPI cards error: {e}")
        return []

def build_gantt_dataframe(stored_solution: Optional[str], stored_data: Optional[str]) -> pd.DataFrame:
    """Generate a normalized dataframe used by gantt chart and exports."""
    if not stored_solution or not stored_data:
        return pd.DataFrame()

    try:
        solution = json.loads(stored_solution)
        data_dict = json.loads(stored_data)

        assignments = solution.get('assignments', [])
        if not assignments:
            return pd.DataFrame()

        vessels_df = pd.DataFrame(data_dict.get('vessels', []))
        if vessels_df.empty:
            return pd.DataFrame()

        rows = []
        for assign in assignments:
            vessel_id = assign.get('vessel_id', 'Unknown')
            vessel_row = vessels_df[vessels_df['vessel_id'] == vessel_id]
            if vessel_row.empty:
                continue

            eta_day = vessel_row.iloc[0].get('eta_day', 0)
            try:
                eta_day = float(eta_day)
            except (TypeError, ValueError):
                continue

            cargo_mt = assign.get('cargo_mt', 0)
            try:
                cargo_mt = float(cargo_mt)
            except (TypeError, ValueError):
                cargo_mt = 0.0

            processing_days = max(1.0, cargo_mt / 10000.0) if cargo_mt else 1.0

            rows.append({
                'Vessel': vessel_id,
                'Port': assign.get('port_id', 'Unknown'),
                'Plant': assign.get('plant_id', 'Unknown'),
                'CargoMT': cargo_mt,
                'StartDay': eta_day,
                'FinishDay': eta_day + processing_days,
                'DurationDays': processing_days
            })

        return pd.DataFrame(rows)

    except Exception as e:
        print(f"Gantt data build error: {e}")
        return pd.DataFrame()


@app.callback(
    Output("gantt-chart", "figure"),
    [Input("stored-solution", "children"),
     Input("refresh-gantt-btn", "n_clicks")],
    [State("stored-data", "children")]
)
def update_gantt_chart(stored_solution, refresh_clicks, stored_data):
    """Update Gantt chart with detailed vessel schedules"""
    if not stored_solution or not stored_data:
        return go.Figure().add_annotation(
            text="Run an optimization to see vessel schedule",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="gray")
        )
    
    try:
        gantt_df = build_gantt_dataframe(stored_solution, stored_data)

        if gantt_df.empty:
            return go.Figure().add_annotation(
                text="No vessel assignments found",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )

        # Create figure
        fig = go.Figure()
        
        # Color map for ports
        port_colors = {
            'HALDIA': '#007bff',
            'PARADIP': '#28a745',
            'VIZAG': '#ffc107',
            'MUMBAI': '#dc3545',
            'CHENNAI': '#17a2b8'
        }
        
        gantt_records = gantt_df.to_dict('records')
        for i, row in enumerate(gantt_records):
            color = port_colors.get(row['Port'], '#6c757d')
            
            fig.add_trace(go.Bar(
                x=[row['FinishDay'] - row['StartDay']],
                y=[row['Vessel']],
                base=row['StartDay'],
                orientation='h',
                marker=dict(color=color),
                name=row['Port'],
                showlegend=(i == 0 or row['Port'] not in [gantt_records[j]['Port'] for j in range(i)]),
                hovertemplate=f"<b>{row['Vessel']}</b><br>" +
                             f"Port: {row['Port']}<br>" +
                             f"Plant: {row['Plant']}<br>" +
                             f"Cargo: {row['CargoMT']:,.0f} MT<br>" +
                             f"Days {row['StartDay']:.1f} - {row['FinishDay']:.1f}<br>" +
                             f"Duration: {row['DurationDays']:.1f} days<extra></extra>"
            ))
        
        fig.update_layout(
            title="Vessel Processing Timeline",
            xaxis_title="Time (Days)",
            yaxis_title="Vessels",
            barmode='overlay',
            height=580,
            showlegend=True,
            legend=dict(title="Ports", orientation="h", y=1.1),
            hovermode='closest'
        )
        
        return fig
        
    except Exception as e:
        print(f"Gantt chart error: {e}")
        return go.Figure().add_annotation(
            text=f"Error creating chart: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=12, color="red")
        )


@app.callback(
    Output("download-gantt-csv", "data"),
    [Input("export-gantt-btn", "n_clicks")],
    [State("stored-solution", "children"),
     State("stored-data", "children")],
    prevent_initial_call=True
)
def download_gantt_csv(n_clicks, stored_solution, stored_data):
    if not n_clicks or not stored_solution or not stored_data:
        return None

    gantt_df = build_gantt_dataframe(stored_solution, stored_data)
    if gantt_df.empty:
        return None

    try:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_buffer:
            zip_buffer.writestr("gantt_schedule.csv", gantt_df.to_csv(index=False))

            port_summary = gantt_df.groupby('Port').agg(
                Vessels=('Vessel', 'count'),
                TotalCargoMT=('CargoMT', 'sum'),
                AvgDurationDays=('DurationDays', 'mean')
            ).reset_index()
            zip_buffer.writestr("port_summary.csv", port_summary.to_csv(index=False))

            plant_summary = gantt_df.groupby('Plant').agg(
                Vessels=('Vessel', 'count'),
                TotalCargoMT=('CargoMT', 'sum'),
                AvgDurationDays=('DurationDays', 'mean')
            ).reset_index()
            zip_buffer.writestr("plant_summary.csv", plant_summary.to_csv(index=False))

            readme = [
                "Gantt Schedule Export Package",
                "Included files:",
                "- gantt_schedule.csv: Detailed vessel timeline.",
                "- port_summary.csv: Aggregated stats per port.",
                "- plant_summary.csv: Aggregated stats per plant.",
                "Generated via the Gantt tab export button."
            ]
            zip_buffer.writestr("README.txt", "\n".join(readme))

        buffer.seek(0)
        return dcc.send_bytes(buffer.getvalue(), "gantt_schedule_export.zip")
    except Exception as e:
        print(f"Gantt export error: {e}")
        return None


@app.callback(
    [Output("schedule-details", "children"),
     Output("schedule-summary", "children")],
    [Input("stored-solution", "children")],
    [State("stored-data", "children")]
)
def update_schedule_info(stored_solution, stored_data):
    """Update schedule details and summary"""
    if not stored_solution or not stored_data:
        return "No schedule available", "No summary available"
    
    try:
        solution = json.loads(stored_solution)
        data_dict = json.loads(stored_data)
        assignments = solution.get('assignments', [])
        vessels_df = pd.DataFrame(data_dict['vessels'])
        
        # Schedule details table
        details_data = []
        for assign in assignments[:10]:  # Show first 10
            vessel_id = assign.get('vessel_id', 'N/A')
            vessel_row = vessels_df[vessels_df['vessel_id'] == vessel_id]
            eta = vessel_row.iloc[0]['eta_day'] if not vessel_row.empty else 'N/A'
            
            details_data.append({
                'Vessel': vessel_id,
                'ETA Day': f"{eta:.1f}" if isinstance(eta, (int, float)) else eta,
                'Port': assign.get('port_id', 'N/A'),
                'Plant': assign.get('plant_id', 'N/A')
            })
        
        details_df = pd.DataFrame(details_data)
        details_table = dash_table.DataTable(
            data=details_df.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in details_df.columns],
            style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '13px'},
            style_header={'backgroundColor': '#343a40', 'color': 'white', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'}
            ],
            page_size=10
        )
        
        # Summary stats
        total_vessels = len(assignments)
        ports_used = len(set(a.get('port_id') for a in assignments))
        plants_served = len(set(a.get('plant_id') for a in assignments))
        
        summary = html.Div([
            html.H6("Schedule statistics", className="mb-3"),
            dbc.ListGroup([
                dbc.ListGroupItem([
                    html.Strong("Total Vessels Scheduled: "),
                    html.Span(f"{total_vessels}", className="float-end badge bg-primary")
                ]),
                dbc.ListGroupItem([
                    html.Strong("Ports Utilized: "),
                    html.Span(f"{ports_used}", className="float-end badge bg-success")
                ]),
                dbc.ListGroupItem([
                    html.Strong("Plants Served: "),
                    html.Span(f"{plants_served}", className="float-end badge bg-info")
                ]),
                dbc.ListGroupItem([
                    html.Strong("Avg Vessels per Port: "),
                    html.Span(f"{total_vessels/ports_used:.1f}" if ports_used > 0 else "N/A", 
                             className="float-end badge bg-secondary")
                ])
            ])
        ])
        
        return details_table, summary
        
    except Exception as e:
        return f"Error: {str(e)}", f"Error: {str(e)}"

def prepare_scenario_comparison(stored_solution):
    """Compute scenario comparison artefacts for reuse across callbacks."""
    placeholder_fig = go.Figure().add_annotation(
        text="Run baseline and optimized plans to compare",
        xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
    )
    placeholder_fig.update_layout(
        template="plotly_white",
        height=360,
        showlegend=False,
        margin=dict(l=60, r=40, t=70, b=60)
    )

    if not stored_solution:
        summary = html.P(
            "Run baseline and optimized solutions to unlock the scenario comparison dashboard.",
            className="text-muted text-center mb-0"
        )
        meta = html.Div(
            "Tip: Generate the baseline plan first, then run an optimized plan for a like-for-like view.",
            className="text-muted small mt-2"
        )
        return {"summary": summary, "figure": placeholder_fig, "meta": meta, "ready": False}

    try:
        if isinstance(stored_solution, str):
            json.loads(stored_solution)
    except (TypeError, ValueError, json.JSONDecodeError):
        message = "Unable to read the stored plan for comparison."
        summary = dbc.Alert(message, color="danger", className="mb-0")
        error_fig = go.Figure().add_annotation(
            text=message,
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(color="red")
        )
        error_fig.update_layout(
            template="plotly_white",
            height=360,
            showlegend=False,
            margin=dict(l=60, r=40, t=70, b=60)
        )
        meta = html.Div(
            "Re-run the optimization workflow to refresh the stored plan before comparing scenarios.",
            className="text-danger small mt-2"
        )
        return {"summary": summary, "figure": error_fig, "meta": meta, "ready": False}

    try:
        global baseline_solution, current_solution

        scenarios: List[str] = []
        costs: List[float] = []
        vessels: List[int] = []

        if baseline_solution:
            scenarios.append("Baseline (FCFS)")
            costs.append(float(baseline_solution.get("objective_value", 0) or 0))
            vessels.append(len(baseline_solution.get("assignments", [])))

        if current_solution:
            scenarios.append("Optimized (AI)")
            costs.append(float(current_solution.get("objective_value", 0) or 0))
            vessels.append(len(current_solution.get("assignments", [])))

        if len(scenarios) < 2:
            summary = dbc.Alert(
                [
                    html.H6("Need both scenarios", className="alert-heading"),
                    html.P(
                        "Run the baseline and optimized plans to unlock the side-by-side comparison.",
                        className="mb-1"
                    ),
                    html.Small(
                        f"Currently available: {', '.join(scenarios) if scenarios else 'None'}",
                        className="text-muted"
                    )
                ],
                color="warning",
                className="mb-0"
            )
            meta = html.Div(
                "Once both plans are solved, this view will quantify savings and throughput deltas automatically.",
                className="text-muted small mt-2"
            )
            return {"summary": summary, "figure": placeholder_fig, "meta": meta, "ready": False}

        baseline_cost = costs[0]
        optimized_cost = costs[1]
        savings = baseline_cost - optimized_cost
        savings_pct = (savings / baseline_cost * 100) if baseline_cost > 0 else 0

        savings_color = "success"
        savings_text = f"{savings_pct:.1f}% reduction"

        if baseline_cost <= 0:
            savings_text = "Invalid baseline cost"
            savings_color = "danger"
        elif optimized_cost > baseline_cost:
            savings_color = "danger"
            savings_text = f"{abs(savings_pct):.1f}% increase (worse)"
        elif savings_pct > 95:
            savings_text = f"~{min(savings_pct, 99):.0f}% reduction (exceptional!)"
            savings_color = "warning"

        summary = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Baseline (FCFS)", className="bg-secondary text-white"),
                    dbc.CardBody([
                        html.H4(format_currency(baseline_cost), className="text-secondary"),
                        html.P(f"{vessels[0]} vessels", className="text-muted mb-0")
                    ])
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Optimized (AI)", className="bg-success text-white"),
                    dbc.CardBody([
                        html.H4(format_currency(optimized_cost), className="text-success"),
                        html.P(f"{vessels[1]} vessels", className="text-muted mb-0")
                    ])
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Savings impact", className=f"bg-{savings_color} text-white"),
                    dbc.CardBody([
                        html.H4(format_currency(savings), className=f"text-{savings_color}"),
                        html.P(savings_text, className="text-muted mb-0")
                    ])
                ])
            ], width=4)
        ])

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Cost Comparison", "Vessel Utilization"),
            specs=[[{"type": "bar"}, {"type": "bar"}]]
        )

        fig.add_trace(
            go.Bar(
                x=scenarios,
                y=costs,
                marker=dict(color=["#6c757d", "#28a745"]),
                text=[format_currency(c) for c in costs],
                textposition="outside",
                name="Cost"
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Bar(
                x=scenarios,
                y=vessels,
                marker=dict(color=["#ffc107", "#007bff"]),
                text=vessels,
                textposition="outside",
                name="Vessels"
            ),
            row=1, col=2
        )

        fig.update_layout(
            height=450,
            showlegend=False,
            title_text="Scenario Analysis Dashboard",
            template="plotly_white",
            margin=dict(l=60, r=40, t=70, b=60)
        )
        fig.update_yaxes(title_text="Total Cost (₹)", row=1, col=1)
        fig.update_yaxes(title_text="Vessels Processed", row=1, col=2)

        meta = html.Div([
            html.Span("Savings vs baseline:", className="text-muted me-1"),
            html.Span(
                f"{format_currency(savings)} ({savings_text})",
                className=f"text-{savings_color} fw-semibold"
            ),
            html.Br(),
            html.Span(
                f"Baseline: {format_currency(baseline_cost)} | Optimized: {format_currency(optimized_cost)}",
                className="text-muted"
            ),
            html.Br(),
            html.Span(
                f"Vessels served: {vessels[0]} → {vessels[1]}",
                className="text-muted"
            )
        ], className="small mt-2")

        return {"summary": summary, "figure": fig, "meta": meta, "ready": True}

    except Exception as exc:
        print(f"Scenario comparison error: {exc}")
        summary = dbc.Alert(f"Error while preparing comparison: {exc}", color="danger", className="mb-0")
        error_fig = go.Figure().add_annotation(
            text=f"Error: {exc}",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(color="red")
        )
        error_fig.update_layout(
            template="plotly_white",
            height=360,
            showlegend=False,
            margin=dict(l=60, r=40, t=70, b=60)
        )
        meta = html.Div(
            "Inspect the logs tab for more detail, then re-run the planning workflow.",
            className="text-danger small mt-2"
        )
        return {"summary": summary, "figure": error_fig, "meta": meta, "ready": False}


@app.callback(
    [Output("scenario-comparison-summary", "children"),
     Output("scenario-comparison-chart", "figure")],
    [Input("stored-solution", "children"),
     Input("compare-scenarios-btn", "n_clicks")]
)
def update_scenario_comparison(stored_solution, compare_clicks):
    """Compare baseline vs optimized scenarios"""
    artefacts = prepare_scenario_comparison(stored_solution)
    return artefacts["summary"], artefacts["figure"]


@app.callback(
    [Output("scenario-comparison-modal", "is_open"),
     Output("modal-scenario-summary", "children"),
     Output("modal-scenario-chart", "figure"),
     Output("modal-scenario-meta", "children")],
    [Input("compare-scenarios-btn", "n_clicks"),
     Input("scenario-modal-close", "n_clicks")],
    [State("scenario-comparison-modal", "is_open"),
     State("stored-solution", "children")],
    prevent_initial_call=True
)
def toggle_scenario_modal(open_clicks, close_clicks, is_open, stored_solution):
    """Open a modal snapshot of the scenario comparison dashboard."""
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger_id == "compare-scenarios-btn" and open_clicks:
        artefacts = prepare_scenario_comparison(stored_solution)
        return True, artefacts["summary"], artefacts["figure"], artefacts["meta"]

    if trigger_id == "scenario-modal-close" and close_clicks:
        return False, dash.no_update, dash.no_update, dash.no_update

    raise PreventUpdate

@app.callback(
    Output("cost-breakdown-chart", "figure"),
    [Input("stored-solution", "children"),
     Input("stored-simulation", "children")],
    [State("stored-data", "children")]
)
def update_cost_breakdown(stored_solution, stored_simulation, stored_data):
    """Update cost breakdown chart - now truly dynamic"""
    if not stored_solution:
        return go.Figure().add_annotation(
            text="Run an optimization to see cost breakdown",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="gray")
        )
    
    try:
        solution = json.loads(stored_solution)
        data_dict = json.loads(stored_data)
        
        # Calculate detailed costs from solution
        assignments = solution.get('assignments', [])
        vessels_df = pd.DataFrame(data_dict['vessels'])
        ports_df = pd.DataFrame(data_dict['ports'])
        rail_costs_df = pd.DataFrame(data_dict['rail_costs'])
        
        # Calculate component costs
        port_handling_cost = 0
        rail_transport_cost = 0
        demurrage_cost = 0
        
        for assign in assignments:
            vessel_id = assign.get('vessel_id')
            port_id = assign.get('port_id')
            plant_id = assign.get('plant_id')
            cargo_mt = assign.get('cargo_mt', 0)
            
            # Port handling
            port_row = ports_df[ports_df['port_id'] == port_id]
            if not port_row.empty:
                handling_rate = port_row.iloc[0]['handling_cost_per_mt']
                port_handling_cost += cargo_mt * handling_rate
            
            # Rail transport
            rail_row = rail_costs_df[
                (rail_costs_df['port_id'] == port_id) & 
                (rail_costs_df['plant_id'] == plant_id)
            ]
            if not rail_row.empty:
                rail_rate = rail_row.iloc[0]['cost_per_mt']
                rail_transport_cost += cargo_mt * rail_rate
            
            # Demurrage (simplified - would need actual wait times)
            vessel_row = vessels_df[vessels_df['vessel_id'] == vessel_id]
            if not vessel_row.empty:
                demurrage_rate = vessel_row.iloc[0]['demurrage_rate']
                # Estimate 0.5 day average delay
                demurrage_cost += demurrage_rate * 12  # 12 hours estimated wait
        
        # Create pie chart
        labels = ['Port Handling', 'Rail Transport', 'Demurrage', 'Other']
        values = [
            port_handling_cost,
            rail_transport_cost,
            demurrage_cost,
            max(0, solution.get('objective_value', 0) - port_handling_cost - rail_transport_cost - demurrage_cost)
        ]
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker=dict(colors=['#007bff', '#28a745', '#ffc107', '#6c757d']),
            textinfo='label+percent',
            textposition='outside'
        )])
        
        fig.update_layout(
            title={
                'text': f'Cost Breakdown - Total: {format_currency(sum(values))}',
                'x': 0.5,
                'xanchor': 'center'
            },
            showlegend=True,
            height=450
        )
        
        return fig
        
    except Exception as e:
        print(f"Cost breakdown error: {e}")
        return go.Figure().add_annotation(
            text=f"Error: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=12, color="red")
        )

@app.callback(
    Output("cost-drivers-analysis", "children"),
    [Input("stored-solution", "children")],
    [State("stored-data", "children")]
)
def update_cost_drivers(stored_solution, stored_data):
    """Analyze and display key cost drivers"""
    if not stored_solution or not stored_data:
        return html.P("No data available", className="text-muted")
    
    try:
        solution = json.loads(stored_solution)
        data_dict = json.loads(stored_data)
        
        drivers = []
        
        # Port utilization driver
        assignments = solution.get('assignments', [])
        port_counts = {}
        for assign in assignments:
            port = assign.get('port_id', 'Unknown')
            port_counts[port] = port_counts.get(port, 0) + 1
        
        if port_counts:
            max_port = max(port_counts, key=port_counts.get)
            drivers.append(
                html.Div([
                    html.H6("Port utilization", className="text-primary"),
                    html.P(f"Busiest: {max_port} ({port_counts[max_port]} vessels)", className="mb-1"),
                    html.Small(f"Total ports used: {len(port_counts)}", className="text-muted")
                ], className="mb-3")
            )
        
        # Cargo distribution
        total_cargo = sum(assign.get('cargo_mt', 0) for assign in assignments)
        if total_cargo > 0:
            drivers.append(
                html.Div([
                    html.H6("Cargo volume", className="text-success"),
                    html.P(f"Total: {total_cargo:,.0f} MT", className="mb-1"),
                    html.Small(f"Avg per vessel: {total_cargo/len(assignments):,.0f} MT", className="text-muted")
                ], className="mb-3")
            )
        
        # Cost per MT insight
        total_cost = solution.get('objective_value', 0)
        if total_cargo > 0:
            cost_per_mt = total_cost / total_cargo
            drivers.append(
                html.Div([
                    html.H6("Cost efficiency", className="text-info"),
                    html.P(f"Cost per MT: ₹{cost_per_mt:.2f}", className="mb-1"),
                    html.Small("Lower is better", className="text-muted")
                ], className="mb-3")
            )
        
        return drivers
        
    except Exception as e:
        return html.P(f"Error: {str(e)}", className="text-danger")

@app.callback(
    Output("cost-timeline-chart", "figure"),
    [Input("stored-solution", "children")],
    [State("stored-data", "children")]
)
def update_cost_timeline(stored_solution, stored_data):
    """Create cost timeline and baseline comparison"""
    if not stored_solution:
        return go.Figure().add_annotation(
            text="Run optimization to see cost timeline",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    try:
        solution = json.loads(stored_solution)
        
        # Create comparison chart if baseline exists
        scenarios = ['Current Solution']
        costs = [solution.get('objective_value', 0)]
        colors = ['#28a745']
        
        if baseline_solution:
            scenarios.insert(0, 'Baseline (FCFS)')
            costs.insert(0, baseline_solution.get('objective_value', 0))
            colors.insert(0, '#6c757d')
        
        # Create bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=scenarios,
                y=costs,
                marker=dict(color=colors),
                text=[format_currency(c) for c in costs],
                textposition='outside'
            )
        ])
        
        # Add savings annotation if baseline exists
        if baseline_solution and len(costs) > 1:
            savings = costs[0] - costs[1]
            savings_pct = (savings / costs[0] * 100) if costs[0] > 0 else 0
            
            fig.add_annotation(
                x=1, y=costs[1],
                text=f"💰 Savings: {format_currency(savings)}<br>({savings_pct:.1f}% reduction)",
                showarrow=True,
                arrowhead=2,
                arrowcolor='green',
                font=dict(size=12, color='green'),
                bgcolor='rgba(200,255,200,0.8)',
                bordercolor='green'
            )
        
        fig.update_layout(
            title="Cost Comparison Across Scenarios",
            yaxis_title="Total Cost (₹)",
            showlegend=False,
            height=380,
            margin=dict(t=50, b=50)
        )
        
        return fig
        
    except Exception as e:
        print(f"Cost timeline error: {e}")
        return go.Figure().add_annotation(
            text=f"Error: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=12, color="red")
        )

@app.callback(
    Output("rake-heatmap", "figure"),
    [Input("stored-solution", "children")],
    [State("stored-data", "children")]
)
def update_rake_heatmap(stored_solution, stored_data):
    """Update rake utilization heatmap"""
    if not stored_solution or not stored_data:
        return go.Figure()
    
    try:
        solution = json.loads(stored_solution)
        data_dict = json.loads(stored_data)
        
        assignments = solution.get('assignments', [])
        ports_df = pd.DataFrame(data_dict['ports'])
        
        return LogisticsVisualizer.create_rake_heatmap(assignments, ports_df)
        
    except Exception as e:
        print(f"Rake heatmap error: {e}")
        return go.Figure()


@app.callback(
    [Output("rake-statistics", "children"),
     Output("rake-assignment-table", "children")],
    [Input("stored-solution", "children"),
     Input("stored-simulation", "children")],
    [State("stored-data", "children")]
)
def update_rake_panels(stored_solution, stored_simulation, stored_data):
    """Render rake summary stats and detailed assignment table."""
    if not stored_solution:
        empty_msg = html.P("Run an optimization to view rake utilization", className="text-muted")
        return empty_msg, empty_msg

    try:
        solution = json.loads(stored_solution)
        assignments = solution.get('assignments', [])

        if not assignments:
            empty_msg = html.P("No rake movements planned.", className="text-muted")
            return empty_msg, empty_msg

        df = pd.DataFrame(assignments)

        # Compute stats
        total_rakes = int(df.get('rakes_required', pd.Series(dtype=int)).sum()) if 'rakes_required' in df else 0
        total_cargo = float(df.get('cargo_mt', pd.Series(dtype=float)).sum()) if 'cargo_mt' in df else 0.0
        unique_ports = df['port_id'].nunique() if 'port_id' in df else 0
        unique_plants = df['plant_id'].nunique() if 'plant_id' in df else 0

        simulation = json.loads(stored_simulation) if stored_simulation else {}
        kpis = simulation.get('kpis', {}) if isinstance(simulation, dict) else {}
        rake_utilization = kpis.get('avg_rake_utilization')

        stats_items = []
        stats_items.append(dbc.ListGroupItem([
            html.Strong("Total Rakes Scheduled"),
            html.Span(f"{total_rakes}", className="badge bg-primary float-end")
        ]))
        stats_items.append(dbc.ListGroupItem([
            html.Strong("Cargo Moved"),
            html.Span(f"{total_cargo:,.0f} MT", className="badge bg-success float-end")
        ]))
        stats_items.append(dbc.ListGroupItem([
            html.Strong("Ports Involved"),
            html.Span(str(unique_ports), className="badge bg-info float-end")
        ]))
        stats_items.append(dbc.ListGroupItem([
            html.Strong("Plants Served"),
            html.Span(str(unique_plants), className="badge bg-warning text-dark float-end")
        ]))
        if rake_utilization is not None:
            stats_items.append(dbc.ListGroupItem([
                html.Strong("Average Rake Utilization"),
                html.Span(f"{rake_utilization:.2%}", className="badge bg-secondary float-end")
            ]))

        stats_component = dbc.ListGroup(stats_items, flush=True)

        # Prepare detailed table
        display_df = df.rename(columns={
            'vessel_id': 'Vessel',
            'port_id': 'Port',
            'plant_id': 'Plant',
            'cargo_mt': 'Cargo (MT)',
            'rakes_required': 'Rakes Required',
            'scheduled_day': 'Scheduled Day',
            'berth_time': 'Berth Day',
            'eta_day': 'ETA Day'
        })

        display_columns = [col for col in ['Vessel', 'Port', 'Plant', 'Cargo (MT)',
                                           'Rakes Required', 'Scheduled Day', 'Berth Day', 'ETA Day']
                           if col in display_df.columns]

        table = dash_table.DataTable(
            data=display_df[display_columns].to_dict('records'),
            columns=[{'name': col, 'id': col} for col in display_columns],
            page_size=10,
            style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': 12},
            style_header={'backgroundColor': '#0d6efd', 'color': 'white', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'}
            ],
            sort_action='native'
        )

        return stats_component, table

    except Exception as exc:
        error = html.P(f"Error building rake metrics: {exc}", className="text-danger")
        return error, error


@app.callback(
    [
        Output("simulation-comparator-summary", "children"),
        Output("simulation-kpi-cards", "children"),
        Output("simulation-performance-chart", "figure"),
        Output("simulation-readiness-list", "children"),
        Output("simulation-variance-table", "children")
    ],
    [
        Input("stored-simulation", "children"),
        Input("stored-solution", "children"),
        Input("stored-data", "children")
    ]
)
def update_simulation_comparator(stored_simulation, stored_solution, stored_data):
    """Populate the Simulation Comparator tab with summary metrics and visuals."""
    global baseline_solution

    def placeholder_figure(message: str) -> go.Figure:
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color="gray")
        )
        fig.update_layout(margin=dict(l=30, r=30, t=40, b=40))
        return fig

    def fmt_currency_signed(value: Optional[float]) -> str:
        if value is None:
            return "—"
        if value == 0:
            return format_currency(0)
        sign = "-" if value < 0 else ""
        return f"{sign}{format_currency(abs(value))}"

    def fmt_value(value: Optional[float], mode: str) -> str:
        if value is None:
            return "—"
        if mode == "currency":
            return format_currency(value)
        if mode == "percentage":
            return f"{value:.1f}%"
        if mode == "hours":
            return f"{value:.1f}h"
        if mode == "ratio":
            return f"{value:.2f}"
        return f"{value}"

    def make_kpi_grid(cards_data: List[Dict]) -> html.Div:
        if not cards_data:
            return html.Div(dbc.Alert("No KPI data available yet.", color="light", className="mb-0"))

        columns = []
        for card in cards_data:
            delta_color = "secondary"
            delta_text = None
            raw_delta = card.get('delta')
            raw_delta_pct = card.get('delta_pct')

            if raw_delta is not None and raw_delta != 0:
                if card['title'] in ['Total Cost', 'Demurrage Cost', 'Avg Vessel Wait']:
                    delta_color = "success" if raw_delta < 0 else "danger"
                else:
                    delta_color = "success" if raw_delta > 0 else "danger"

            if raw_delta_pct is not None:
                delta_text = html.Div(
                    f"{raw_delta_pct:+.1f}% vs plan",
                    className=f"text-{delta_color} small fw-semibold"
                )

            columns.append(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.Div(card['title'], className="text-muted small mb-1"),
                            html.H4(card['value'], className="mb-1"),
                            delta_text if delta_text else html.Div(" ", className="small"),
                            html.Div(
                                card.get('description', ''),
                                className="text-muted small mt-2"
                            )
                        ]),
                        className="shadow-sm h-100"
                    ),
                    xs=12, sm=6, lg=4
                )
            )

        return html.Div(dbc.Row(columns, className="g-3"))

    if not stored_solution or not stored_data:
        alert = dbc.Alert(
            "Load data and run an optimization to unlock simulation comparisons.",
            color="light",
            className="mb-3"
        )
        empty_fig = placeholder_figure("Awaiting optimization run")
        return (
            alert,
            html.Div(dbc.Alert("Simulation KPIs will appear here once available.", color="secondary", className="mb-0")),
            empty_fig,
            html.Div(dbc.Alert("Checklist will populate after the first simulation.", color="secondary", className="mb-0")),
            html.Div(dbc.Alert("Variance table activates when simulation completes.", color="secondary", className="mb-0"))
        )

    data_frames = get_data_frames(stored_data)
    vessels_df = data_frames.get('vessels', pd.DataFrame())
    plants_df = data_frames.get('plants', pd.DataFrame())
    ports_df = data_frames.get('ports', pd.DataFrame())
    rail_costs_df = data_frames.get('rail_costs', pd.DataFrame())

    solution = parse_solution_payload(stored_solution)
    assignments = solution.get('assignments', []) if isinstance(solution, dict) else []

    plan_kpis = calculate_kpis(
        assignments,
        vessels_df,
        plants_df,
        None,
        ports_df,
        rail_costs_df
    ) if assignments else {}

    baseline_kpis = None
    if baseline_solution and isinstance(baseline_solution, dict):
        baseline_assignments = baseline_solution.get('assignments', [])
        if baseline_assignments:
            baseline_kpis = calculate_kpis(
                baseline_assignments,
                vessels_df,
                plants_df,
                None,
                ports_df,
                rail_costs_df
            )

    if not stored_simulation:
        summary = dbc.Alert(
            [
                html.Div("Simulation results pending.", className="fw-semibold mb-1"),
                html.Div(
                    "Run the simulation to validate execution risk, cost realism, and service KPIs.",
                    className="small mb-2"
                ),
                html.Div(
                    f"Assignments queued for simulation: {len(assignments)}",
                    className="small text-muted"
                )
            ],
            color="warning",
            className="mb-3"
        )

        kpi_panel = html.Div([
            html.Div("Current plan KPIs (pre-simulation)", className="text-muted small fw-semibold mb-2"),
            make_kpi_grid(LogisticsVisualizer.create_kpi_cards(plan_kpis, baseline_kpis) if plan_kpis else [])
        ])

        empty_fig = placeholder_figure("Trigger the simulation to unlock cost realism charts")

        checklist = html.Div(
            dbc.Alert(
                "Run the simulation to generate readiness insights (service level, demurrage exposure, rake utilization).",
                color="light",
                className="mb-0"
            )
        )

        variance = html.Div(
            dbc.Alert(
                "Variance table will populate once simulated metrics are available.",
                color="light",
                className="mb-0"
            )
        )

        return summary, kpi_panel, empty_fig, checklist, variance

    simulation_results = parse_solution_payload(stored_simulation)
    if not simulation_results or simulation_results.get('status') == 'no_assignments':
        summary = dbc.Alert(
            "Simulation skipped because no vessel assignments were available. Run optimization first.",
            color="warning",
            className="mb-0"
        )
        empty_fig = placeholder_figure("No simulation output to display")
        return (
            summary,
            html.Div(dbc.Alert("Simulation KPIs require a successful run.", color="light", className="mb-0")),
            empty_fig,
            html.Div(dbc.Alert("Checklist unavailable without simulation data.", color="light", className="mb-0")),
            html.Div(dbc.Alert("Variance table unavailable without simulation data.", color="light", className="mb-0"))
        )

    sim_kpis = calculate_kpis(
        assignments,
        vessels_df,
        plants_df,
        simulation_results,
        ports_df,
        rail_costs_df
    ) if assignments else simulation_results.get('kpis', {})

    plan_cost = plan_kpis.get('total_cost', solution.get('objective_value', 0) if isinstance(solution, dict) else 0)
    sim_cost = sim_kpis.get('total_cost', simulation_results.get('cost_components', {}).get('total', 0))
    cost_delta = sim_cost - plan_cost
    cost_delta_pct = None
    if plan_cost and plan_cost != 0:
        cost_delta_pct = (cost_delta / plan_cost) * 100

    service_level = sim_kpis.get('demand_fulfillment_pct', 0)
    vessels_processed_pct = sim_kpis.get('vessels_processed_pct', 0)
    demurrage_plan = plan_kpis.get('demurrage_cost', 0)
    demurrage_sim = sim_kpis.get('demurrage_cost', simulation_results.get('cost_components', {}).get('demurrage', 0))
    demurrage_delta = demurrage_sim - demurrage_plan
    rake_utilization = sim_kpis.get('avg_rake_utilization', 0)
    simulation_days = simulation_results.get('simulation_days', 0)

    delta_badge_color = "secondary"
    if cost_delta < 0:
        delta_badge_color = "success"
    elif cost_delta > 0:
        delta_badge_color = "danger"

    summary = html.Div([
        dbc.Card([
            dbc.CardBody([
                html.Div("Cost realism check", className="text-muted small mb-2"),
                html.Div([
                    html.Div("Planned cost", className="text-muted small"),
                    html.Div(format_currency(plan_cost) if plan_cost else "—", className="fw-semibold")
                ], className="d-flex justify-content-between"),
                html.Div([
                    html.Div("Simulated cost", className="text-muted small"),
                    html.Div(format_currency(sim_cost) if sim_cost else "—", className="fw-semibold")
                ], className="d-flex justify-content-between"),
                html.Div([
                    html.Div("Delta", className="text-muted small"),
                    html.Div([
                        dbc.Badge(
                            fmt_currency_signed(cost_delta),
                            color=delta_badge_color,
                            className="me-2"
                        ),
                        html.Span(
                            f"{cost_delta_pct:+.1f}%" if cost_delta_pct is not None else "—",
                            className=f"text-{delta_badge_color} small fw-semibold"
                        )
                    ], className="d-flex align-items-center")
                ], className="d-flex justify-content-between mt-2"),
                html.Hr(),
                dbc.ListGroup([
                    dbc.ListGroupItem([
                        html.Div("Service level", className="text-muted small"),
                        html.Div(f"{service_level:.1f}%", className="fw-semibold")
                    ], className="d-flex justify-content-between"),
                    dbc.ListGroupItem([
                        html.Div("Vessels processed", className="text-muted small"),
                        html.Div(f"{vessels_processed_pct:.1f}%", className="fw-semibold")
                    ], className="d-flex justify-content-between"),
                    dbc.ListGroupItem([
                        html.Div("Simulation horizon", className="text-muted small"),
                        html.Div(f"{simulation_days} days", className="fw-semibold")
                    ], className="d-flex justify-content-between")
                ], flush=True)
            ])
        ], className="shadow-sm border-0"),
        html.Div(
            f"Assignments evaluated: {len(assignments)}",
            className="text-muted small mt-3"
        )
    ])

    kpi_panel = html.Div([
        html.Div("Simulated KPIs vs planned expectations", className="text-muted small fw-semibold mb-2"),
        make_kpi_grid(LogisticsVisualizer.create_kpi_cards(sim_kpis, plan_kpis))
    ])

    component_labels = ["Port Handling", "Rail Transport", "Demurrage"]
    plan_components = [
        plan_kpis.get('port_handling_cost', 0),
        plan_kpis.get('rail_transport_cost', 0),
        plan_kpis.get('demurrage_cost', demurrage_plan)
    ]
    sim_components = [
        sim_kpis.get('port_handling_cost', simulation_results.get('cost_components', {}).get('port_handling', 0)),
        sim_kpis.get('rail_transport_cost', simulation_results.get('cost_components', {}).get('rail_transport', 0)),
        sim_kpis.get('demurrage_cost', demurrage_sim)
    ]

    performance_fig = go.Figure()
    performance_fig.add_trace(go.Bar(
        x=component_labels,
        y=plan_components,
        name="Planned",
        marker_color="#6c757d",
        text=[format_currency(value) for value in plan_components],
        textposition="outside"
    ))
    performance_fig.add_trace(go.Bar(
        x=component_labels,
        y=sim_components,
        name="Simulated",
        marker_color="#007bff",
        text=[format_currency(value) for value in sim_components],
        textposition="outside"
    ))
    performance_fig.update_layout(
        title="Plan vs simulated cost structure",
        barmode="group",
        height=360,
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", x=0.5, xanchor="center", y=1.15)
    )
    performance_fig.update_yaxes(title_text="Cost (₹)")

    readiness_items = []

    service_target = 95
    service_color = "success" if service_level >= service_target else "danger"
    readiness_items.append(
        dbc.ListGroupItem([
            html.Div("Service fulfilment", className="fw-semibold"),
            html.Div(f"{service_level:.1f}% vs {service_target}% target", className=f"text-{service_color}")
        ], color=service_color if service_level else "light")
    )

    cost_color = "success" if cost_delta <= 0 else "danger"
    readiness_items.append(
        dbc.ListGroupItem([
            html.Div("Cost discipline", className="fw-semibold"),
            html.Div(
                f"{fmt_currency_signed(cost_delta)} vs plan",
                className=f"text-{cost_color}"
            )
        ], color=cost_color if cost_delta else "light")
    )

    demurrage_color = "success" if demurrage_delta <= 0 else "danger"
    readiness_items.append(
        dbc.ListGroupItem([
            html.Div("Demurrage exposure", className="fw-semibold"),
            html.Div(
                f"{fmt_currency_signed(demurrage_delta)} change",
                className=f"text-{demurrage_color}"
            )
        ], color=demurrage_color if demurrage_delta else "light")
    )

    utilization_target = 0.65
    utilization_color = "success" if rake_utilization >= utilization_target else "warning"
    readiness_items.append(
        dbc.ListGroupItem([
            html.Div("Rake utilization", className="fw-semibold"),
            html.Div(
                f"{rake_utilization:.2f} vs {utilization_target:.2f} target",
                className=f"text-{utilization_color}"
            )
        ], color=utilization_color if rake_utilization else "light")
    )

    readiness_list = dbc.ListGroup(readiness_items, flush=True, className="shadow-sm")

    metrics_config = [
        ("Total Cost", "total_cost", "currency"),
        ("Demurrage Cost", "demurrage_cost", "currency"),
        ("Port Handling Cost", "port_handling_cost", "currency"),
        ("Rail Transport Cost", "rail_transport_cost", "currency"),
        ("Demand Fulfillment", "demand_fulfillment_pct", "percentage"),
        ("Avg Vessel Wait (hrs)", "avg_vessel_wait_hours", "hours"),
        ("Rake Utilization", "avg_rake_utilization", "ratio"),
        ("Vessels Processed", "vessels_processed_pct", "percentage")
    ]

    variance_rows = []
    for label, key, mode in metrics_config:
        plan_value = plan_kpis.get(key)
        sim_value = sim_kpis.get(key) if sim_kpis else None
        delta = None
        delta_pct_display = "—"
        if plan_value is not None and sim_value is not None:
            delta = sim_value - plan_value
            if plan_value not in (0, None):
                delta_pct_display = f"{(delta / plan_value) * 100:+.1f}%"
        delta_display = "—"
        if delta is not None:
            if mode == "currency":
                delta_display = fmt_currency_signed(delta)
            elif mode == "percentage":
                delta_display = f"{delta:+.1f}%"
            elif mode == "hours":
                delta_display = f"{delta:+.1f}h"
            elif mode == "ratio":
                delta_display = f"{delta:+.2f}"
            else:
                delta_display = f"{delta:+.2f}"

        variance_rows.append({
            "Metric": label,
            "Planned": fmt_value(plan_value, mode),
            "Simulated": fmt_value(sim_value, mode),
            "Delta": delta_display,
            "Delta %": delta_pct_display
        })

    variance_df = pd.DataFrame(variance_rows)
    variance_table = dash_table.DataTable(
        data=variance_df.to_dict("records"),
        columns=[{"name": col, "id": col} for col in variance_df.columns],
        style_table={"overflowX": "auto"},
        style_cell={
            "padding": "8px",
            "fontSize": "13px"
        },
        style_header={
            "backgroundColor": "#f8f9fa",
            "fontWeight": "bold"
        },
        page_size=8
    )

    return summary, kpi_panel, performance_fig, readiness_list, variance_table

@app.callback(
    Output("system-status", "children"),
    [Input("stored-data", "children"),
     Input("stored-solution", "children"),
     Input("stored-simulation", "children")]
)
def update_system_status(stored_data, stored_solution, stored_simulation):
    """Update system status display"""
    status_items = []
    
    # Data status
    if stored_data:
        status_items.append(html.Div("Data loaded", className="text-success fw-semibold"))
    else:
        status_items.append(html.Div("No data loaded", className="text-danger fw-semibold"))
    
    # Solution status
    if stored_solution:
        solution = json.loads(stored_solution)
        status_items.append(
            html.Div(
                f"Optimization status: {solution.get('status', 'Unknown')}",
                className="text-success"
            )
        )
    else:
        status_items.append(html.Div("Optimization pending", className="text-warning"))
    
    # Simulation status
    if stored_simulation:
        status_items.append(html.Div("Simulation completed", className="text-success"))
    else:
        status_items.append(html.Div("Simulation pending", className="text-warning"))
    
    return status_items

@app.callback(
    Output("quick-insights", "children"),
    [Input("stored-solution", "children"),
     Input("stored-simulation", "children")],
    [State("stored-data", "children")]
)
def update_quick_insights(stored_solution, stored_simulation, stored_data):
    """Generate quick insights from optimization results"""
    if not stored_solution or not stored_data:
        return html.Div(
            "Run an optimization to see insights",
            className="text-muted"
        )
    
    try:
        solution = json.loads(stored_solution)
        data_dict = json.loads(stored_data)
        
        insights = []
        
        # Cost efficiency insight
        total_cost = solution.get('objective_value', 0)
        if baseline_solution:
            baseline_cost = baseline_solution.get('objective_value', 0)
            if baseline_cost > 0:
                improvement = ((baseline_cost - total_cost) / baseline_cost) * 100
                if improvement > 10:
                    insights.append(dbc.Alert(
                        f"Cost reduced by {improvement:.1f}% versus the baseline solution.",
                        color="success",
                        className="mb-2"
                    ))
                elif improvement > 0:
                    insights.append(dbc.Alert(
                        f"Cost reduced by {improvement:.1f}% versus baseline.",
                        color="info",
                        className="mb-2"
                    ))
        
        # Vessel utilization insight
        assignments = solution.get('assignments', [])
        if assignments:
            vessels_df = pd.DataFrame(data_dict['vessels'])
            processed = len(assignments)
            total = len(vessels_df)
            utilization = (processed / total) * 100
            
            insights.append(
                dbc.Alert(
                    f"Processing {processed} of {total} vessels ({utilization:.0f}% utilization).",
                    color="primary" if utilization > 80 else "warning",
                    className="mb-2"
                )
            )
        
        # Bottleneck detection
        ports_df = pd.DataFrame(data_dict['ports'])
        if len(ports_df) > 0:
            port_assignments = {}
            for assign in assignments:
                port = assign.get('port_id', 'Unknown')
                port_assignments[port] = port_assignments.get(port, 0) + 1
            
            if port_assignments:
                max_port = max(port_assignments, key=port_assignments.get)
                max_count = port_assignments[max_port]
                avg_count = sum(port_assignments.values()) / len(port_assignments)
                
                if max_count > avg_count * 1.5:
                    insights.append(dbc.Alert(
                        f"Potential bottleneck detected: {max_port} handles {max_count} vessels, above the portfolio average.",
                        color="warning",
                        className="mb-2"
                    ))
        
        # Optimization method insight
        opt_status = solution.get('status', 'Unknown')
        solver_time = solution.get('solve_time', 0)
        insights.append(dbc.Alert(
            f"Optimization status: {opt_status} | Solve time: {solver_time:.2f}s",
            color="secondary",
            className="mb-2"
        ))
        
        if not insights:
            insights.append(html.Div("Analysis in progress...", className="text-muted"))
        
        return insights
        
    except Exception as e:
        return html.Div(f"Error generating insights: {str(e)}", className="text-danger")

@app.callback(
    Output("data-summary-table", "children"),
    [Input("stored-data", "children")]
)
def update_data_summary(stored_data):
    """Create data summary table"""
    if not stored_data:
        return html.Div(
            "No data loaded. Click 'Load Sample Data' or upload CSV files.",
            className="text-muted text-center p-4"
        )
    
    try:
        data_dict = json.loads(stored_data)
        
        summary_rows = []
        for dataset_name, records in data_dict.items():
            df = pd.DataFrame(records)
            summary_rows.append({
                'Dataset': dataset_name.upper(),
                'Records': len(df),
                'Columns': len(df.columns),
                'Key Columns': ', '.join(df.columns[:3].tolist())
            })
        
        summary_df = pd.DataFrame(summary_rows)
        
        return dash_table.DataTable(
            data=summary_df.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in summary_df.columns],
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': '#343a40', 'color': 'white', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'}
            ]
        )
        
    except Exception as e:
        return html.Div(
            f"Error: {str(e)}",
            className="text-danger"
        )

@app.callback(
    [Output("solver-logs", "children"),
     Output("audit-trail", "children")],
    [Input("stored-solution", "children"),
     Input("stored-simulation", "children")]
)
def update_logs_and_audit(stored_solution, stored_simulation):
    """Update solver logs and audit trail"""
    logs = []
    audit = []
    
    if stored_solution:
        try:
            solution = json.loads(stored_solution)
            
            # Solver logs
            log_entries = solution.get('logs', [])
            if log_entries:
                for entry in log_entries:
                    logs.append(html.P(entry, className="mb-1 font-monospace small"))
            else:
                # Generate synthetic logs from solution
                logs.append(html.P(f"Optimization method: {solution.get('method', 'N/A')}", className="mb-1"))
                logs.append(html.P(f"Status: {solution.get('status', 'N/A')}", className="mb-1"))
                logs.append(html.P(f"Objective value: {format_currency(solution.get('objective_value', 0))}", className="mb-1"))
                logs.append(html.P(f"Solve time: {solution.get('solve_time', 0):.2f}s", className="mb-1"))
                logs.append(html.P(f"Assignments: {len(solution.get('assignments', []))} vessels", className="mb-1"))
            
            # Audit trail
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            audit.append(
                dbc.ListGroupItem([
                    html.Div([
                        html.Strong("Optimization Completed"),
                        html.Br(),
                        html.Small(f"Time: {timestamp}", className="text-muted"),
                        html.Br(),
                        html.Small(f"Method: {solution.get('method', 'Unknown')}", className="text-muted"),
                        html.Br(),
                        html.Small(f"Cost: {format_currency(solution.get('objective_value', 0))}", className="text-muted")
                    ])
                ])
            )
            
        except Exception as e:
            logs.append(html.P(f"Error parsing solution: {str(e)}", className="text-danger"))
    
    if stored_simulation:
        try:
            simulation = json.loads(stored_simulation)
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            audit.append(
                dbc.ListGroupItem([
                    html.Div([
                        html.Strong("Simulation Completed"),
                        html.Br(),
                        html.Small(f"Time: {timestamp}", className="text-muted"),
                        html.Br(),
                        html.Small(f"Duration: {simulation.get('simulation_days', 'N/A')} days", className="text-muted")
                    ])
                ])
            )
        except:
            pass
    
    if not logs:
        logs = [html.P("No logs available. Run an optimization first.", className="text-muted")]
    
    if not audit:
        audit = [html.P("No activities yet.", className="text-muted")]
    
    return logs, dbc.ListGroup(audit)

@app.callback(
    Output("export-preview", "children"),
    [Input("stored-solution", "children")],
    [State("stored-data", "children")]
)
def update_export_preview(stored_solution, stored_data):
    """Show preview of exportable data"""
    if not stored_solution or not stored_data:
        return html.P("Run an optimization to preview export data", className="text-muted")
    
    try:
        solution = json.loads(stored_solution)
        assignments = solution.get('assignments', [])
        
        if not assignments:
            return html.P("No assignments to export", className="text-muted")
        
        # Create preview dataframe
        preview_data = []
        for i, assign in enumerate(assignments[:5]):  # Show first 5
            preview_data.append({
                'Vessel': assign.get('vessel_id', 'N/A'),
                'Port': assign.get('port_id', 'N/A'),
                'Plant': assign.get('plant_id', 'N/A'),
                'Cargo (MT)': f"{assign.get('cargo_mt', 0):,.0f}",
                'ETA Day': assign.get('eta_day', 'N/A')
            })
        
        preview_df = pd.DataFrame(preview_data)
        
        result = [
            html.P(f"Preview (showing 5 of {len(assignments)} assignments):", className="small text-muted mb-2"),
            dash_table.DataTable(
                data=preview_df.to_dict('records'),
                columns=[{'name': col, 'id': col} for col in preview_df.columns],
                style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '12px'},
                style_header={'backgroundColor': '#6c757d', 'color': 'white', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'}
                ]
            )
        ]
        
        return result
        
    except Exception as e:
        return html.P(f"Error: {str(e)}", className="text-danger")

def run_server(debug: Optional[bool] = None, port=5006, host='127.0.0.1'):
    """Run the Dash server"""
    import os
    import logging
    
    if debug is None:
        env_debug = os.getenv("DASH_DEBUG", "").strip().lower()
        debug = env_debug in ("1", "true", "yes", "on")

    # Reduce Flask/Werkzeug logging noise (keeps errors, hides routine logs)
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)  # Only show errors, not every HTTP request
    
    print("Starting SIH Logistics Optimization Simulator...")
    print(f"Dashboard available at: http://{host}:{port}/")
    print("Loading modules and initializing predictive components...")
    print(f"Debug mode: {'ON' if debug else 'OFF'}")
    print(f"Deterministic seed in use: {BASE_RANDOM_SEED}")
    
    # Initialize ML model (guard against duplicate execution under any reloader)
    if os.environ.get("WERKZEUG_RUN_MAIN") in (None, "true"):
        set_global_seed(BASE_RANDOM_SEED, quiet=True)
        reseed_for_phase("eta_model_training", quiet=True)
        eta_predictor.train_stub_model()
        # Restore base seed for downstream callbacks
        set_global_seed(BASE_RANDOM_SEED, quiet=True)
    
    print(f"Server ready at http://{host}:{port}/")
    print("Tip: Leave this terminal open while the dashboard is running.")
    print("Errors will be reported below if they occur.\n")
    
    # Explicitly disable the reloader to prevent the app from starting twice.
    try:
        app.run(
            debug=debug,
            host=host,
            port=port,
            use_reloader=False,
            dev_tools_hot_reload=False,
        )
    except TypeError:
        # Fallback for older Dash versions that may not support all kwargs
        app.run(
            debug=debug,
            host=host,
            port=port,
            use_reloader=False,
        )

if __name__ == "__main__":
    run_server()