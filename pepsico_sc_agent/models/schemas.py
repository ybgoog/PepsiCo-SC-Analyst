"""
Data Models & Schemas for PepsiCo Supply Chain Agent
Adheres to SAP ERP tables (MARC, MARD, VBBE) and MOP-SC-042 structures.
Built with standard library dataclasses for zero-dependency portability.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime


class ProductCategory(str, Enum):
    SALTY_SNACKS = "Frito-Lay Salty Snacks"
    CARBONATED_BEVERAGES = "Pepsi Beverages"
    SPORTS_HYDRATION = "Gatorade Sports Hydration"
    CONVENIENT_FOODS = "Quaker Convenient Foods"


class CustomerTier(str, Enum):
    TIER_1 = "TIER_1"  # Walmart, Target, Kroger, Costco
    TIER_2 = "TIER_2"  # Regional Supermarkets
    TIER_3 = "TIER_3"  # Convenience & Small Format


class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"    # DOS < 3.0 or High Revenue Risk
    WARNING = "WARNING"      # DOS < 7.0 (Safety Stock breach)
    HEALTHY = "HEALTHY"      # DOS >= 7.0


class MitigationOptionType(str, Enum):
    OPTION_A_INTER_DC_STO = "OPTION_A"          # Expedite Inter-DC Stock Transfer Order
    OPTION_B_SAFETY_STOCK_REBALANCE = "OPTION_B" # Dynamic Safety Stock Buffer Adjustment
    OPTION_C_ORDER_THROTTLING = "OPTION_C"       # Defer/Throttle Non-Critical Replenishment


@dataclass
class SKUMaster:
    sku_id: str
    name: str
    brand: str
    category: str
    unit_wholesale_price: float
    case_pack: int = 12
    pallet_cases: int = 60
    weight_lbs_per_case: float = 15.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InventoryRecord:
    plant_id: str
    sku_id: str
    storage_location: str = "0001"
    unrestricted_stock: int = 0
    quality_inspection_stock: int = 0
    blocked_stock: int = 0
    safety_stock_units: int = 0
    safety_stock_dos_target: float = 7.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DemandProfile:
    dc_id: str
    sku_id: str
    baseline_daily_demand: float
    overnight_actual_orders: float
    surge_variance_pct: float = 0.0
    tier_1_order_share: float = 0.60
    tier_2_order_share: float = 0.25
    tier_3_order_share: float = 0.15

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExceptionAlert:
    exception_id: str
    dc_id: str
    dc_name: str
    sku_id: str
    sku_name: str
    brand: str
    category: str
    current_on_hand: int
    daily_demand_rate: float
    current_dos: float
    safety_stock_dos_threshold: float
    dos_deficit_days: float
    units_needed_for_target_dos: int
    daily_revenue_at_risk: float
    sla_weighted_risk_score: float
    severity: SeverityLevel
    root_cause_narrative: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity.value
        d["timestamp"] = self.timestamp.isoformat()
        return d


@dataclass
class MitigationOption:
    option_id: str
    option_type: MitigationOptionType
    title: str
    description: str
    transfer_quantity_cases: int
    execution_cost_usd: float
    recovery_lead_time_hours: float
    post_mitigation_dos: float
    protected_revenue_usd: float
    fill_rate_projection_pct: float
    risk_confidence_score: float
    sap_transaction_code: str
    trade_off_summary: str
    donor_dc_id: Optional[str] = None
    donor_dc_name: Optional[str] = None
    donor_dc_available_dos: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["option_type"] = self.option_type.value
        return d


@dataclass
class MitigationComparisonMatrix:
    exception_id: str
    sku_id: str
    dc_id: str
    options: List[MitigationOption]
    recommended_option_id: str
    recommendation_rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exception_id": self.exception_id,
            "sku_id": self.sku_id,
            "dc_id": self.dc_id,
            "options": [opt.to_dict() for opt in self.options],
            "recommended_option_id": self.recommended_option_id,
            "recommendation_rationale": self.recommendation_rationale
        }


@dataclass
class SAPExecutionOrder:
    order_id: str
    sap_document_number: str
    transaction_code: str
    sku_id: str
    destination_plant: str
    quantity_cases: int
    execution_status: str
    audit_message: str
    source_plant: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    executed_by: str = "HITL_PLANNER"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["created_at"] = self.created_at.isoformat()
        return d
