"""Central configuration and realistic operating benchmarks for the
Port-to-Plant logistics optimization platform.

All financial values are expressed in Indian Rupees (INR) unless
explicitly mentioned. Voyage timings are expressed in days.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


EXCHANGE_RATE_INR_PER_USD: float = 83.0
"""Representative INR/USD exchange rate used for freight conversion."""


@dataclass(frozen=True)
class PortBenchmark:
    """Realistic cost and capacity assumptions for Indian east-coast ports."""

    name: str
    handling_cost_per_mt: float  # INR / MT
    storage_cost_per_mt_per_day: float  # INR / MT / day
    free_storage_days: int
    daily_throughput_mt: int
    rakes_available_per_day: int


PORT_BENCHMARKS: Dict[str, PortBenchmark] = {
    "PARADIP": PortBenchmark(
        name="Paradip Port",
        handling_cost_per_mt=125.0,
        storage_cost_per_mt_per_day=0.95,
        free_storage_days=4,
        daily_throughput_mt=250_000,
        rakes_available_per_day=36,
    ),
    "HALDIA": PortBenchmark(
        name="Haldia Dock Complex",
        handling_cost_per_mt=135.0,
        storage_cost_per_mt_per_day=1.05,
        free_storage_days=3,
        daily_throughput_mt=180_000,
        rakes_available_per_day=28,
    ),
    "DHAMRA": PortBenchmark(
        name="Dhamra Port",
        handling_cost_per_mt=115.0,
        storage_cost_per_mt_per_day=0.85,
        free_storage_days=5,
        daily_throughput_mt=220_000,
        rakes_available_per_day=30,
    ),
    "VIZAG": PortBenchmark(
        name="Visakhapatnam Port",
        handling_cost_per_mt=130.0,
        storage_cost_per_mt_per_day=0.95,
        free_storage_days=4,
        daily_throughput_mt=210_000,
        rakes_available_per_day=32,
    ),
}


@dataclass(frozen=True)
class VoyageBenchmark:
    """Voyage timing assumptions for typical source regions."""

    sea_time_days_min: int
    sea_time_days_max: int


VOYAGE_BENCHMARKS: Dict[str, VoyageBenchmark] = {
    "AUSTRALIA": VoyageBenchmark(sea_time_days_min=18, sea_time_days_max=25),
    "AFRICA": VoyageBenchmark(sea_time_days_min=12, sea_time_days_max=18),
}


@dataclass(frozen=True)
class PlantBenchmark:
    """Steel plant demand and service characteristics."""

    name: str
    daily_demand_mt: int
    preferred_grade: str
    safety_stock_days: int


PLANT_BENCHMARKS: Dict[str, PlantBenchmark] = {
    "PLANT_A": PlantBenchmark("Bokaro Steel Plant", 24_000, "IRON_ORE", 5),
    "PLANT_B": PlantBenchmark("Durgapur Steel Plant", 18_000, "COKING_COAL", 4),
    "PLANT_C": PlantBenchmark("Rourkela Steel Plant", 22_000, "IRON_ORE", 6),
    "PLANT_D": PlantBenchmark("Kalinganagar Steel Plant", 16_000, "COKING_COAL", 5),
    "PLANT_E": PlantBenchmark("Angul Steel Plant", 14_000, "LIMESTONE", 4),
}


DEFAULT_RAKE_CAPACITY_MT: int = 4_000
"""Average rake capacity considered in the model."""


# Redirection penalty when a vessel discharges at a non-primary port (INR/MT)
SECONDARY_PORT_PENALTY_PER_MT: float = 90.0

# Demurrage reference rate multiplier (₹ per MT per extra day at berth)
DEMURRAGE_PENALTY_PER_MT_PER_DAY: float = 35.0

# Rail transit time (days) by distance band (km)
RAIL_TRANSIT_BANDS: Dict[str, Dict[str, float]] = {
    "SHORT": {"max_km": 300, "transit_days": 2.0},
    "MEDIUM": {"max_km": 600, "transit_days": 3.0},
    "LONG": {"max_km": 900, "transit_days": 4.0},
    "ULTRA": {"max_km": 1_200, "transit_days": 5.0},
}


def classify_rail_transit(distance_km: float) -> float:
    """Return the benchmark rail transit time in days for a given distance."""
    for band in ("SHORT", "MEDIUM", "LONG", "ULTRA"):
        spec = RAIL_TRANSIT_BANDS[band]
        if distance_km <= spec["max_km"]:
            return spec["transit_days"]
    return RAIL_TRANSIT_BANDS["ULTRA"]["transit_days"]


def get_port_ids() -> List[str]:
    return list(PORT_BENCHMARKS.keys())
