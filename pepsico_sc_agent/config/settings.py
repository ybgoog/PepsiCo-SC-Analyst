"""
PepsiCo Supply Chain Planner Agent - Configuration Settings
Defines regional DC network topology, distance matrix, customer SLA tiers,
freight rates, and safety stock default thresholds per SOP-SC-042 & MOP-SC-042.
"""

from typing import Dict, Any

# General Agent Configuration
AGENT_NAME = "PepsiCo-SC-Exception-Triage-Agent"
AGENT_VERSION = "1.0.0"
SOP_DOCUMENT_ID = "SOP-SC-042"
MOP_DOCUMENT_ID = "MOP-SC-042"

# Supply Chain Thresholds
DEFAULT_SAFETY_STOCK_DOS_THRESHOLD = 7.0  # Alert if DOS < 7 days
CRITICAL_STOCKOUT_DOS_THRESHOLD = 3.0     # Critical if DOS < 3 days
SURPLUS_DONOR_MIN_DOS = 14.0             # Donor DC must have > 14 DOS to support STO

# Regional Distribution Center (DC) Master Data
DISTRIBUTION_CENTERS: Dict[str, Dict[str, Any]] = {
    "DC-DAL-01": {
        "name": "Dallas Regional Distribution Hub",
        "state": "TX",
        "region": "South Central",
        "plant_code": "PLNT-1010",
        "capacity_pallets": 45000,
        "is_manufacturing_plant": True
    },
    "DC-CHI-02": {
        "name": "Chicago Central Distribution Center",
        "state": "IL",
        "region": "Midwest",
        "plant_code": "PLNT-2020",
        "capacity_pallets": 60000,
        "is_manufacturing_plant": True
    },
    "DC-ATL-03": {
        "name": "Atlanta Metro Distribution Center",
        "state": "GA",
        "region": "Southeast",
        "plant_code": "PLNT-3030",
        "capacity_pallets": 38000,
        "is_manufacturing_plant": False
    },
    "DC-NE-04": {
        "name": "Northeast Regional Hub (Breinigsville)",
        "state": "PA",
        "region": "Northeast",
        "plant_code": "PLNT-4040",
        "capacity_pallets": 52000,
        "is_manufacturing_plant": True
    }
}

# Inter-DC Distance Matrix (Highway Miles)
DC_DISTANCE_MATRIX: Dict[str, Dict[str, int]] = {
    "DC-DAL-01": {"DC-DAL-01": 0, "DC-CHI-02": 920, "DC-ATL-03": 780, "DC-NE-04": 1450},
    "DC-CHI-02": {"DC-DAL-01": 920, "DC-CHI-02": 0, "DC-ATL-03": 710, "DC-NE-04": 680},
    "DC-ATL-03": {"DC-DAL-01": 780, "DC-CHI-02": 710, "DC-ATL-03": 0, "DC-NE-04": 790},
    "DC-NE-04": {"DC-DAL-01": 1450, "DC-CHI-02": 680, "DC-ATL-03": 790, "DC-NE-04": 0}
}

# Logistics & Transportation Cost Models
FREIGHT_COST_PER_MILE_STANDARD = 2.85   # Standard dedicated dry-van
FREIGHT_COST_PER_MILE_EXPEDITED = 4.20  # Team-driver expedited linehaul
AVERAGE_TRANSIT_SPEED_MPH = 48.0        # Effective transit speed including DOT stops
HANDLING_COST_PER_PALLET = 15.00        # Cross-dock / pick-pack loading fee
UNITS_PER_PALLET_DEFAULT = 60           # Average cases/units per standard 48x40 pallet

# Customer SLA Severity Tiers & Penalties
CUSTOMER_SLA_WEIGHTS: Dict[str, Dict[str, Any]] = {
    "TIER_1": {
        "name": "Strategic Key Accounts (Walmart, Target, Kroger, Costco)",
        "sla_weight": 2.5,
        "otif_penalty_pct": 0.03,  # 3% invoice penalty for On-Time In-Full violation
        "priority_rank": 1
    },
    "TIER_2": {
        "name": "Regional Grocery & Mass Merchandisers",
        "sla_weight": 1.5,
        "otif_penalty_pct": 0.015,
        "priority_rank": 2
    },
    "TIER_3": {
        "name": "Convenience, Gas & Direct Store Delivery (DSD) Small Format",
        "sla_weight": 1.0,
        "otif_penalty_pct": 0.0,
        "priority_rank": 3
    }
}
