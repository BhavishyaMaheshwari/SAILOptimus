"""Data loading utilities for the logistics optimization system."""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import io
import base64
import re

from config import (
    EXCHANGE_RATE_INR_PER_USD,
    PORT_BENCHMARKS,
    PLANT_BENCHMARKS,
    VOYAGE_BENCHMARKS,
    DEFAULT_RAKE_CAPACITY_MT,
    SECONDARY_PORT_PENALTY_PER_MT,
    get_port_ids,
)

class DataLoader:
    """Handles data loading, validation, and toy dataset generation"""

    @staticmethod
    def _normalize_identifier(value: Optional[str]) -> Optional[str]:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        return str(value).strip().upper()

    @staticmethod
    def _normalize_secondary_ports(value: Optional[str]) -> Optional[str]:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        if isinstance(value, (list, tuple, set)):
            tokens = [DataLoader._normalize_identifier(tok) for tok in value if DataLoader._normalize_identifier(tok)]
        else:
            tokens = [
                DataLoader._normalize_identifier(tok)
                for tok in re.split(r"[|;,]+", str(value))
                if DataLoader._normalize_identifier(tok)
            ]
        if not tokens:
            return None
        # Preserve original order but remove duplicates
        seen = set()
        ordered_tokens = []
        for token in tokens:
            if token not in seen:
                seen.add(token)
                ordered_tokens.append(token)
        return "|".join(ordered_tokens)

    @staticmethod
    def _to_numeric(series: pd.Series, default: float = 0.0) -> pd.Series:
        numeric = pd.to_numeric(series, errors='coerce') if series is not None else None
        if numeric is None:
            return pd.Series(default, index=series.index if series is not None else [])
        return numeric.fillna(default)

    @staticmethod
    def standardize_dataset(data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Clean identifiers, enforce numeric types, and backfill benchmark-driven cost columns."""
        if not data:
            return data

        standardized: Dict[str, pd.DataFrame] = {}

        if 'ports' in data and isinstance(data['ports'], pd.DataFrame):
            ports_df = data['ports'].copy()
            if 'port_id' in ports_df.columns:
                ports_df['port_id'] = ports_df['port_id'].apply(DataLoader._normalize_identifier)

            numeric_port_cols = [
                'handling_cost_per_mt',
                'storage_cost_per_mt_per_day',
                'daily_capacity_mt',
                'rakes_available_per_day',
                'free_storage_days'
            ]
            for col in numeric_port_cols:
                if col in ports_df.columns:
                    ports_df[col] = DataLoader._to_numeric(ports_df[col], default=0.0)

            # Fill storage costs and free days from benchmarks when missing or zero
            for col in ['storage_cost_per_mt_per_day', 'free_storage_days', 'handling_cost_per_mt']:
                if col not in ports_df.columns:
                    ports_df[col] = 0.0

            for idx, row in ports_df.iterrows():
                port_id = row.get('port_id')
                benchmark = PORT_BENCHMARKS.get(port_id)
                if benchmark:
                    if ports_df.at[idx, 'storage_cost_per_mt_per_day'] <= 0:
                        ports_df.at[idx, 'storage_cost_per_mt_per_day'] = benchmark.storage_cost_per_mt_per_day
                    if ports_df.at[idx, 'free_storage_days'] <= 0:
                        ports_df.at[idx, 'free_storage_days'] = benchmark.free_storage_days
                    if ports_df.at[idx, 'handling_cost_per_mt'] <= 0:
                        ports_df.at[idx, 'handling_cost_per_mt'] = benchmark.handling_cost_per_mt

            standardized['ports'] = ports_df

        if 'vessels' in data and isinstance(data['vessels'], pd.DataFrame):
            vessels_df = data['vessels'].copy()
            for col in ['vessel_id', 'port_id']:
                if col in vessels_df.columns:
                    vessels_df[col] = vessels_df[col].apply(DataLoader._normalize_identifier)

            if 'secondary_port_id' in vessels_df.columns:
                vessels_df['secondary_port_id'] = vessels_df['secondary_port_id'].apply(DataLoader._normalize_secondary_ports)

            numeric_vessel_cols = ['cargo_mt', 'eta_day', 'demurrage_rate']
            for col in numeric_vessel_cols:
                if col in vessels_df.columns:
                    vessels_df[col] = DataLoader._to_numeric(vessels_df[col], default=0.0)

            # Freight conversion
            if 'freight_inr_per_mt' not in vessels_df.columns:
                vessels_df['freight_inr_per_mt'] = np.nan
            else:
                vessels_df['freight_inr_per_mt'] = DataLoader._to_numeric(vessels_df['freight_inr_per_mt'], default=np.nan)

            if 'freight_usd_per_mt' in vessels_df.columns:
                vessels_df['freight_usd_per_mt'] = DataLoader._to_numeric(vessels_df['freight_usd_per_mt'], default=0.0)
            else:
                vessels_df['freight_usd_per_mt'] = 0.0

            missing_freight_mask = vessels_df['freight_inr_per_mt'].isna() | (vessels_df['freight_inr_per_mt'] <= 0)
            vessels_df.loc[missing_freight_mask, 'freight_inr_per_mt'] = (
                vessels_df.loc[missing_freight_mask, 'freight_usd_per_mt'] * EXCHANGE_RATE_INR_PER_USD
            )
            vessels_df['freight_inr_per_mt'] = vessels_df['freight_inr_per_mt'].fillna(0.0)

            standardized['vessels'] = vessels_df

        if 'plants' in data and isinstance(data['plants'], pd.DataFrame):
            plants_df = data['plants'].copy()
            if 'plant_id' in plants_df.columns:
                plants_df['plant_id'] = plants_df['plant_id'].apply(DataLoader._normalize_identifier)
            if 'daily_demand_mt' in plants_df.columns:
                plants_df['daily_demand_mt'] = DataLoader._to_numeric(plants_df['daily_demand_mt'], default=0.0)
            standardized['plants'] = plants_df

        if 'rail_costs' in data and isinstance(data['rail_costs'], pd.DataFrame):
            rail_df = data['rail_costs'].copy()
            if 'port_id' in rail_df.columns:
                rail_df['port_id'] = rail_df['port_id'].apply(DataLoader._normalize_identifier)
            if 'plant_id' in rail_df.columns:
                rail_df['plant_id'] = rail_df['plant_id'].apply(DataLoader._normalize_identifier)
            for col in ['cost_per_mt', 'distance_km', 'transit_days']:
                if col in rail_df.columns:
                    rail_df[col] = DataLoader._to_numeric(rail_df[col], default=0.0)
            standardized['rail_costs'] = rail_df

        sanitized = data.copy()
        sanitized.update(standardized)
        return sanitized
    
    @staticmethod
    def get_toy_dataset() -> Dict[str, pd.DataFrame]:
        """Generate embedded toy dataset for immediate demo"""
        
        ports_records: List[Dict] = []
        for port_id in get_port_ids():
            bench = PORT_BENCHMARKS[port_id]
            ports_records.append({
                'port_id': port_id,
                'port_name': bench.name,
                'handling_cost_per_mt': bench.handling_cost_per_mt,
                'storage_cost_per_mt_per_day': bench.storage_cost_per_mt_per_day,
                'free_storage_days': bench.free_storage_days,
                'daily_capacity_mt': bench.daily_throughput_mt,
                'rakes_available_per_day': bench.rakes_available_per_day,
                'secondary_port_penalty_per_mt': SECONDARY_PORT_PENALTY_PER_MT,
            })

        vessels_records: List[Dict] = []
        vessel_template = [
            ("MV_COKING_1", 85_000, "AUSTRALIA", "PARADIP", "HALDIA"),
            ("MV_IRON_1", 65_000, "AUSTRALIA", "VIZAG", "DHAMRA"),
            ("MV_LIMESTONE_1", 60_000, "AFRICA", "DHAMRA", "PARADIP"),
            ("MV_COKING_2", 90_000, "AUSTRALIA", "HALDIA", "PARADIP"),
            ("MV_IRON_2", 70_000, "AFRICA", "PARADIP", "VIZAG"),
            ("MV_IRON_3", 62_000, "AUSTRALIA", "VIZAG", "PARADIP"),
            ("MV_COKING_3", 88_000, "AFRICA", "DHAMRA", "HALDIA"),
            ("MV_LIMESTONE_2", 58_000, "AFRICA", "HALDIA", "DHAMRA"),
            ("MV_IRON_4", 74_000, "AUSTRALIA", "PARADIP", "HALDIA"),
        ]

        eta_day = 5
        for vessel_id, cargo_mt, origin_region, primary_port, secondary_port in vessel_template:
            voyage = VOYAGE_BENCHMARKS[origin_region]
            freight_usd_per_mt = 2.6 if origin_region == "AUSTRALIA" else 1.9
            freight_inr_per_mt = freight_usd_per_mt * EXCHANGE_RATE_INR_PER_USD
            demurrage_rate_inr = 95_000 if origin_region == "AUSTRALIA" else 82_000
            vessels_records.append({
                'vessel_id': vessel_id,
                'cargo_mt': cargo_mt,
                'eta_day': eta_day,
                'port_id': primary_port,
                'secondary_port_id': secondary_port,
                'origin_region': origin_region,
                'sea_time_days_min': voyage.sea_time_days_min,
                'sea_time_days_max': voyage.sea_time_days_max,
                'freight_usd_per_mt': freight_usd_per_mt,
                'freight_inr_per_mt': round(freight_inr_per_mt, 2),
                'demurrage_rate': demurrage_rate_inr,
                'cargo_grade': (
                    'COKING_COAL' if 'COKING' in vessel_id else
                    'LIMESTONE' if 'LIMESTONE' in vessel_id else 'IRON_ORE'
                ),
            })
            eta_day += np.random.uniform(1.5, 3.5)

        plants_records: List[Dict] = []
        for plant_id, bench in PLANT_BENCHMARKS.items():
            plants_records.append({
                'plant_id': plant_id,
                'plant_name': bench.name,
                'daily_demand_mt': bench.daily_demand_mt,
                'quality_requirements': bench.preferred_grade,
                'safety_stock_days': bench.safety_stock_days,
            })

        rail_distance_map = {
            ("PARADIP", "PLANT_A"): (450, 135),
            ("PARADIP", "PLANT_B"): (520, 145),
            ("PARADIP", "PLANT_C"): (400, 130),
            ("PARADIP", "PLANT_D"): (220, 115),
            ("PARADIP", "PLANT_E"): (180, 110),
            ("HALDIA", "PLANT_A"): (560, 140),
            ("HALDIA", "PLANT_B"): (240, 110),
            ("HALDIA", "PLANT_C"): (520, 140),
            ("HALDIA", "PLANT_D"): (360, 125),
            ("HALDIA", "PLANT_E"): (300, 120),
            ("DHAMRA", "PLANT_A"): (380, 130),
            ("DHAMRA", "PLANT_B"): (460, 140),
            ("DHAMRA", "PLANT_C"): (320, 120),
            ("DHAMRA", "PLANT_D"): (180, 110),
            ("DHAMRA", "PLANT_E"): (210, 112),
            ("VIZAG", "PLANT_A"): (620, 150),
            ("VIZAG", "PLANT_B"): (660, 152),
            ("VIZAG", "PLANT_C"): (280, 120),
            ("VIZAG", "PLANT_D"): (560, 145),
            ("VIZAG", "PLANT_E"): (600, 148),
        }

        rail_records: List[Dict] = []
        for (port_id, plant_id), (distance_km, base_cost) in rail_distance_map.items():
            variable_cost = base_cost
            transit_days = max(2, int(round(distance_km / 250)))
            rail_records.append({
                'port_id': port_id,
                'plant_id': plant_id,
                'cost_per_mt': variable_cost,
                'distance_km': distance_km,
                'transit_days': transit_days,
            })

        raw_dataset = {
            'ports': pd.DataFrame(ports_records),
            'vessels': pd.DataFrame(vessels_records),
            'plants': pd.DataFrame(plants_records),
            'rail_costs': pd.DataFrame(rail_records)
        }

        return DataLoader.standardize_dataset(raw_dataset)
    
    @staticmethod
    def validate_csv_data(data: Dict[str, pd.DataFrame]) -> Tuple[bool, List[str]]:
        """Validate uploaded CSV data structure and content"""
        errors = []
        
        # Required columns for each dataset
        required_columns = {
            'ports': [
                'port_id', 'port_name', 'handling_cost_per_mt',
                'storage_cost_per_mt_per_day', 'free_storage_days',
                'daily_capacity_mt', 'rakes_available_per_day'
            ],
            'vessels': ['vessel_id', 'cargo_mt', 'eta_day', 'port_id', 'demurrage_rate', 'cargo_grade'],
            'plants': ['plant_id', 'daily_demand_mt', 'quality_requirements'],
            'rail_costs': ['port_id', 'plant_id', 'cost_per_mt']
        }
        
        # Check if all required datasets are present
        for dataset_name in required_columns.keys():
            if dataset_name not in data:
                errors.append(f"Missing required dataset: {dataset_name}")
                continue
                
            df = data[dataset_name]
            
            # Check required columns
            missing_cols = set(required_columns[dataset_name]) - set(df.columns)
            if missing_cols:
                errors.append(f"{dataset_name}: Missing columns {missing_cols}")
            
            # Check for empty dataframes
            if df.empty:
                errors.append(f"{dataset_name}: Dataset is empty")
            
            # Dataset-specific validations
            if dataset_name == 'vessels':
                if 'cargo_mt' in df.columns and (df['cargo_mt'] <= 0).any():
                    errors.append("vessels: cargo_mt must be positive")
                if 'eta_day' in df.columns and (df['eta_day'] < 0).any():
                    errors.append("vessels: eta_day must be non-negative")
                if 'secondary_port_id' in df.columns:
                    secondary_series = df['secondary_port_id'].dropna().astype(str).str.strip()
                    if not secondary_series.empty:
                        port_ids = set(data.get('ports', pd.DataFrame()).get('port_id', []))
                        bad_values = []
                        for entry in secondary_series:
                            if not entry:
                                continue
                            tokens = [tok.strip() for tok in re.split(r'[|;,]+', entry) if tok.strip()]
                            for token in tokens:
                                token = token.upper()
                                if token not in port_ids:
                                    bad_values.append(token)
                        if bad_values:
                            errors.append(
                                f"vessels: secondary_port_id contains unknown ports {sorted(set(bad_values))}"
                            )
            
            elif dataset_name == 'ports':
                if 'daily_capacity_mt' in df.columns and (df['daily_capacity_mt'] <= 0).any():
                    errors.append("ports: daily_capacity_mt must be positive")
                if 'rakes_available_per_day' in df.columns and (df['rakes_available_per_day'] <= 0).any():
                    errors.append("ports: rakes_available_per_day must be positive")
                if 'free_storage_days' in df.columns and (df['free_storage_days'] < 0).any():
                    errors.append("ports: free_storage_days must be non-negative")
            
            elif dataset_name == 'plants':
                if 'daily_demand_mt' in df.columns and (df['daily_demand_mt'] <= 0).any():
                    errors.append("plants: daily_demand_mt must be positive")
        
        return len(errors) == 0, errors   
 
    @staticmethod
    def parse_uploaded_file(contents: str, filename: str) -> Optional[pd.DataFrame]:
        """Parse uploaded CSV file content"""
        try:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            
            if 'csv' in filename:
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            elif 'xlsx' in filename or 'xls' in filename:
                df = pd.read_excel(io.BytesIO(decoded))
            else:
                return None
                
            return df
        except Exception as e:
            print(f"Error parsing file {filename}: {e}")
            return None
    
    @staticmethod
    def create_sample_csvs() -> Dict[str, str]:
        """Create sample CSV content for download templates"""
        toy_data = DataLoader.get_toy_dataset()
        
        csv_contents = {}
        for name, df in toy_data.items():
            csv_contents[f"{name}.csv"] = df.to_csv(index=False)
        
        return csv_contents
    
    @staticmethod
    def get_data_summary(data: Dict[str, pd.DataFrame]) -> Dict[str, any]:
        """Generate summary statistics for loaded data"""
        summary = {}
        
        if 'vessels' in data:
            vessels = data['vessels']
            summary['total_vessels'] = len(vessels)
            summary['total_cargo_mt'] = vessels['cargo_mt'].sum()
            summary['avg_eta_days'] = vessels['eta_day'].mean()
            summary['cargo_types'] = vessels['cargo_grade'].unique().tolist()
        
        if 'ports' in data:
            ports = data['ports']
            summary['total_ports'] = len(ports)
            summary['total_port_capacity'] = ports['daily_capacity_mt'].sum()
            summary['total_rakes_available'] = ports['rakes_available_per_day'].sum()
        
        if 'plants' in data:
            plants = data['plants']
            summary['total_plants'] = len(plants)
            summary['total_demand_mt'] = plants['daily_demand_mt'].sum()
        
        return summary