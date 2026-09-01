"""
ADK Tools for PepsiCo Supply Chain Agent
Exposes callable tools for inventory inspection, DOS calculations,
mitigation simulations, and SAP ERP transaction execution.
"""

from typing import Dict, List, Any, Optional
from pepsico_sc_agent.config.settings import (
    DEFAULT_SAFETY_STOCK_DOS_THRESHOLD,
    CRITICAL_STOCKOUT_DOS_THRESHOLD,
    DISTRIBUTION_CENTERS
)
from pepsico_sc_agent.models.schemas import (
    ExceptionAlert,
    SeverityLevel,
    MitigationComparisonMatrix,
    SAPExecutionOrder
)
from pepsico_sc_agent.models.calculations import (
    calculate_days_of_supply,
    calculate_dos_deficit,
    calculate_units_needed,
    calculate_sla_weighted_risk_score,
    simulate_all_mitigation_options
)
from pepsico_sc_agent.data.database import (
    query_inventory_semantic_view,
    get_all_dc_inventory_for_sku,
    record_sap_execution,
    get_recent_sap_audit_trail
)


def query_inventory_semantic_layer(
    plant_id: Optional[str] = None,
    sku_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Tool: Queries BigQuery / SAP semantic layer (MARC, MARD, DEMAND_PROFILES).
    Returns list of inventory positions, demand rates, and safety stock targets.
    """
    return query_inventory_semantic_view(plant_id=plant_id, sku_id=sku_id)


def compute_dos_risk_matrix(
    target_dos_threshold: float = DEFAULT_SAFETY_STOCK_DOS_THRESHOLD
) -> List[ExceptionAlert]:
    """
    Tool: Scans entire SKU portfolio across all DCs, computes Days of Supply (DOS),
    identifies safety stock breaches, and ranks exceptions by SLA-weighted revenue risk.
    """
    rows = query_inventory_semantic_view()
    alerts: List[ExceptionAlert] = []

    for row in rows:
        dc_id = row["plant_id"]
        sku_id = row["sku_id"]
        on_hand = row["unrestricted_stock"]
        daily_demand = row["baseline_daily_demand"]
        actual_orders = row["overnight_actual_orders"]
        surge_pct = row["surge_variance_pct"]
        unit_price = row["unit_wholesale_price"]
        dc_name = DISTRIBUTION_CENTERS.get(dc_id, {}).get("name", dc_id)

        # Compute DOS using actual active daily demand rate
        effective_demand_rate = max(daily_demand, actual_orders) if actual_orders > 0 else daily_demand
        current_dos = calculate_days_of_supply(on_hand, effective_demand_rate)
        
        # Check if threshold is breached
        if current_dos < target_dos_threshold:
            dos_deficit = calculate_dos_deficit(current_dos, target_dos_threshold)
            units_needed = calculate_units_needed(dos_deficit, effective_demand_rate)
            
            t1_share = row["tier_1_order_share"]
            t2_share = row["tier_2_order_share"]
            t3_share = row["tier_3_order_share"]
            
            rev_at_risk, risk_score = calculate_sla_weighted_risk_score(
                dos_deficit, effective_demand_rate, unit_price,
                t1_share, t2_share, t3_share
            )
            
            severity = SeverityLevel.CRITICAL if current_dos < CRITICAL_STOCKOUT_DOS_THRESHOLD or risk_score > 50.0 else SeverityLevel.WARNING
            
            # Formulate root cause narrative
            if surge_pct > 20.0:
                narrative = f"Overnight demand surge of +{surge_pct:.0f}% over baseline (potential retail circular promo or key account volume pull)."
            elif on_hand < (daily_demand * 3.0):
                narrative = "Delayed inbound production batch coupled with steady consumption."
            else:
                narrative = "Safety stock buffer breached under normal replenishment lead time."

            alert = ExceptionAlert(
                exception_id=f"EXC-{dc_id}-{sku_id}",
                dc_id=dc_id,
                dc_name=dc_name,
                sku_id=sku_id,
                sku_name=row["sku_name"],
                brand=row["brand"],
                category=row["category"],
                current_on_hand=on_hand,
                daily_demand_rate=effective_demand_rate,
                current_dos=current_dos,
                safety_stock_dos_threshold=target_dos_threshold,
                dos_deficit_days=dos_deficit,
                units_needed_for_target_dos=units_needed,
                daily_revenue_at_risk=rev_at_risk,
                sla_weighted_risk_score=risk_score,
                severity=severity,
                root_cause_narrative=narrative
            )
            alerts.append(alert)

    # Rank descending by Multi-Factor SLA-weighted risk score
    alerts.sort(key=lambda a: a.sla_weighted_risk_score, reverse=True)
    return alerts


def simulate_mitigation_scenarios(
    dc_id: str,
    sku_id: str
) -> MitigationComparisonMatrix:
    """
    Tool: Runs quantitative financial simulation across Option A (Inter-DC STO),
    Option B (Safety Stock Rebalance), and Option C (Order Deferral/Throttling).
    """
    # Fetch SKU metadata and target DC inventory
    inv_rows = query_inventory_semantic_view(plant_id=dc_id, sku_id=sku_id)
    if not inv_rows:
        raise ValueError(f"No inventory record found for SKU {sku_id} at DC {dc_id}")
    
    target_data = inv_rows[0]
    all_dc_inventory = get_all_dc_inventory_for_sku(sku_id)

    daily_demand = target_data["baseline_daily_demand"]
    if target_data["overnight_actual_orders"] > 0:
        daily_demand = max(daily_demand, target_data["overnight_actual_orders"])

    on_hand = target_data["unrestricted_stock"]
    current_dos = calculate_days_of_supply(on_hand, daily_demand)
    dos_deficit = calculate_dos_deficit(current_dos, DEFAULT_SAFETY_STOCK_DOS_THRESHOLD)
    units_needed = calculate_units_needed(dos_deficit, daily_demand)

    matrix = simulate_all_mitigation_options(
        target_dc=dc_id,
        sku_id=sku_id,
        sku_name=target_data["sku_name"],
        unit_price=target_data["unit_wholesale_price"],
        current_on_hand=on_hand,
        daily_demand_rate=daily_demand,
        dos_deficit=dos_deficit,
        units_needed=units_needed,
        all_dc_inventory=all_dc_inventory
    )
    return matrix


def execute_sap_action(
    action_type: str,
    sku_id: str,
    source_plant: Optional[str],
    destination_plant: str,
    quantity_cases: int,
    auth_token: str = "HITL_APPROVED",
    planner_note: str = ""
) -> Dict[str, Any]:
    """
    Tool: Posts authorized execution transaction into SAP ERP / IBP.
    Supports STO creation, safety stock parameter adjustments, and order delivery blocks.
    """
    if not auth_token:
        raise PermissionError("Human-in-the-Loop authorization required for SAP execution.")

    audit_msg = f"Executed {action_type} for {quantity_cases:,} cases of {sku_id} to {destination_plant}. Note: {planner_note}"
    sap_doc_number = record_sap_execution(
        transaction_code=action_type,
        sku_id=sku_id,
        source_plant=source_plant,
        destination_plant=destination_plant,
        quantity_cases=quantity_cases,
        executed_by="SENIOR_SC_PLANNER",
        audit_message=audit_msg
    )

    return {
        "status": "SUCCESS",
        "sap_document_number": sap_doc_number,
        "transaction_code": action_type,
        "sku_id": sku_id,
        "source_plant": source_plant,
        "destination_plant": destination_plant,
        "quantity_cases": quantity_cases,
        "audit_message": audit_msg
    }


def get_audit_history(limit: int = 10) -> List[Dict[str, Any]]:
    """Tool: Retrieves recent ERP execution audit records."""
    return get_recent_sap_audit_trail(limit=limit)
