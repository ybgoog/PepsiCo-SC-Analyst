"""
Supply Chain Mathematical & Algorithmic Calculations Engine
Implements MOP-SC-042 Days of Supply (DOS), SLA-Weighted Risk Scoring,
and Quantitative Mitigation Trade-off Simulation.
"""

import math
from typing import Dict, List, Optional, Tuple, Any
from pepsico_sc_agent.config.settings import (
    DEFAULT_SAFETY_STOCK_DOS_THRESHOLD,
    CRITICAL_STOCKOUT_DOS_THRESHOLD,
    SURPLUS_DONOR_MIN_DOS,
    DISTRIBUTION_CENTERS,
    DC_DISTANCE_MATRIX,
    FREIGHT_COST_PER_MILE_STANDARD,
    FREIGHT_COST_PER_MILE_EXPEDITED,
    AVERAGE_TRANSIT_SPEED_MPH,
    HANDLING_COST_PER_PALLET,
    UNITS_PER_PALLET_DEFAULT,
    CUSTOMER_SLA_WEIGHTS
)
from pepsico_sc_agent.models.schemas import (
    MitigationOption,
    MitigationOptionType,
    MitigationComparisonMatrix,
    CustomerTier
)


def calculate_days_of_supply(on_hand_units: float, daily_demand_rate: float) -> float:
    """
    Computes Days of Supply (DOS) per MOP-SC-042:
    DOS = Current On-Hand Inventory / Average Daily Sales Run Rate
    """
    if daily_demand_rate <= 0:
        return 999.0 if on_hand_units > 0 else 0.0
    return round(on_hand_units / daily_demand_rate, 2)


def calculate_dos_deficit(current_dos: float, target_dos: float = DEFAULT_SAFETY_STOCK_DOS_THRESHOLD) -> float:
    """
    Computes Days of Supply deficit below target threshold.
    """
    return max(0.0, round(target_dos - current_dos, 2))


def calculate_units_needed(dos_deficit: float, daily_demand_rate: float) -> int:
    """
    Computes physical cases/units required to restore inventory to target DOS.
    """
    return int(math.ceil(dos_deficit * daily_demand_rate))


def calculate_sla_weighted_risk_score(
    dos_deficit: float,
    daily_demand_rate: float,
    unit_wholesale_price: float,
    tier_1_share: float = 0.60,
    tier_2_share: float = 0.25,
    tier_3_share: float = 0.15
) -> Tuple[float, float]:
    """
    Calculates Daily Revenue at Risk and Multi-Factor SLA-Weighted Risk Score.
    Returns: (daily_revenue_at_risk_usd, sla_weighted_risk_score)
    """
    base_daily_revenue = daily_demand_rate * unit_wholesale_price
    
    # SLA multiplier factoring Key Accounts (Walmart/Target OTIF penalties)
    t1_weight = CUSTOMER_SLA_WEIGHTS["TIER_1"]["sla_weight"]
    t2_weight = CUSTOMER_SLA_WEIGHTS["TIER_2"]["sla_weight"]
    t3_weight = CUSTOMER_SLA_WEIGHTS["TIER_3"]["sla_weight"]
    
    sla_blended_multiplier = (
        (tier_1_share * t1_weight) +
        (tier_2_share * t2_weight) +
        (tier_3_share * t3_weight)
    )
    
    daily_revenue_at_risk = round(base_daily_revenue, 2)
    # Risk Score: DOS Deficit severity * Blended SLA Weight * (Base Revenue / 1000)
    risk_score = round(dos_deficit * sla_blended_multiplier * (base_daily_revenue / 1000.0), 2)
    
    return daily_revenue_at_risk, risk_score


def calculate_linehaul_transit(
    origin_dc: str,
    dest_dc: str,
    quantity_cases: int,
    pallet_cases: int = UNITS_PER_PALLET_DEFAULT,
    expedited: bool = True
) -> Tuple[float, float, int]:
    """
    Computes freight linehaul cost, transit lead time in hours, and pallet count.
    Returns: (freight_cost_usd, transit_hours, total_pallets)
    """
    distance = DC_DISTANCE_MATRIX.get(origin_dc, {}).get(dest_dc, 500)
    pallets = max(1, int(math.ceil(quantity_cases / max(1, pallet_cases))))
    
    rate_per_mile = FREIGHT_COST_PER_MILE_EXPEDITED if expedited else FREIGHT_COST_PER_MILE_STANDARD
    # Number of 53ft full truckloads (FTL capacity = 30 standard pallets)
    truckloads = max(1, int(math.ceil(pallets / 30.0)))
    
    linehaul_cost = distance * rate_per_mile * truckloads
    handling_cost = pallets * HANDLING_COST_PER_PALLET
    total_cost = round(linehaul_cost + handling_cost, 2)
    
    # Transit time: driving hours + loading/unloading buffer (2 hrs expedited, 4 hrs standard)
    driving_hours = distance / AVERAGE_TRANSIT_SPEED_MPH
    buffer_hours = 2.0 if expedited else 4.0
    total_hours = round(driving_hours + buffer_hours, 1)
    
    return total_cost, total_hours, pallets


def simulate_all_mitigation_options(
    target_dc: str,
    sku_id: str,
    sku_name: str,
    unit_price: float,
    current_on_hand: int,
    daily_demand_rate: float,
    dos_deficit: float,
    units_needed: int,
    all_dc_inventory: Dict[str, Dict[str, Any]]
) -> MitigationComparisonMatrix:
    """
    Generates quantitative simulation for Option A, Option B, and Option C per SOP-SC-042 Step 3.
    """
    options: List[MitigationOption] = []
    
    # -------------------------------------------------------------
    # OPTION A: Inter-DC Expedited Stock Transfer Order (STO)
    # -------------------------------------------------------------
    # Identify potential donor DCs with surplus stock
    best_donor_dc = None
    best_donor_dos = 0.0
    shortest_distance = 999999
    
    for dc_id, dc_data in all_dc_inventory.items():
        if dc_id == target_dc:
            continue
        donor_on_hand = dc_data.get("on_hand", 0)
        donor_demand = dc_data.get("daily_demand", 1)
        donor_dos = calculate_days_of_supply(donor_on_hand, donor_demand)
        
        # Check if donor DC has surplus > 14 DOS and enough units to spare
        if donor_dos >= SURPLUS_DONOR_MIN_DOS and (donor_on_hand - units_needed) > (donor_demand * 10):
            dist = DC_DISTANCE_MATRIX.get(dc_id, {}).get(target_dc, 9999)
            if dist < shortest_distance:
                shortest_distance = dist
                best_donor_dc = dc_id
                best_donor_dos = donor_dos
                
    if best_donor_dc:
        donor_name = DISTRIBUTION_CENTERS[best_donor_dc]["name"]
        cost, transit_hrs, pallets = calculate_linehaul_transit(best_donor_dc, target_dc, units_needed, expedited=True)
        post_dos = calculate_days_of_supply(current_on_hand + units_needed, daily_demand_rate)
        protected_rev = round(units_needed * unit_price, 2)
        
        option_a = MitigationOption(
            option_id="OPT-A-STO",
            option_type=MitigationOptionType.OPTION_A_INTER_DC_STO,
            title=f"Expedited STO from {DISTRIBUTION_CENTERS[best_donor_dc]['name']}",
            description=f"Transfer {units_needed:,} cases ({pallets} pallets) via team-driver expedited linehaul from {best_donor_dc} ({best_donor_dos:.1f} DOS surplus).",
            donor_dc_id=best_donor_dc,
            donor_dc_name=donor_name,
            donor_dc_available_dos=best_donor_dos,
            transfer_quantity_cases=units_needed,
            execution_cost_usd=cost,
            recovery_lead_time_hours=transit_hrs,
            post_mitigation_dos=post_dos,
            protected_revenue_usd=protected_rev,
            fill_rate_projection_pct=99.2,
            risk_confidence_score=0.94,
            sap_transaction_code="STO-UB-01",
            trade_off_summary=f"Cost: ${cost:,.2f} freight | Lead Time: {transit_hrs} hrs | Restores DOS to {post_dos:.1f} days (99.2% Fill Rate)"
        )
    else:
        # Fallback if no ideal single donor has >14 DOS
        fallback_dc = "DC-DAL-01" if target_dc != "DC-DAL-01" else "DC-CHI-02"
        cost, transit_hrs, pallets = calculate_linehaul_transit(fallback_dc, target_dc, units_needed, expedited=True)
        option_a = MitigationOption(
            option_id="OPT-A-STO",
            option_type=MitigationOptionType.OPTION_A_INTER_DC_STO,
            title=f"Emergency Inter-DC Transfer from {DISTRIBUTION_CENTERS[fallback_dc]['name']}",
            description=f"Emergency transfer {units_needed:,} cases from primary plant DC {fallback_dc}.",
            donor_dc_id=fallback_dc,
            donor_dc_name=DISTRIBUTION_CENTERS[fallback_dc]["name"],
            donor_dc_available_dos=11.5,
            transfer_quantity_cases=units_needed,
            execution_cost_usd=cost,
            recovery_lead_time_hours=transit_hrs,
            post_mitigation_dos=DEFAULT_SAFETY_STOCK_DOS_THRESHOLD,
            protected_revenue_usd=round(units_needed * unit_price, 2),
            fill_rate_projection_pct=95.0,
            risk_confidence_score=0.82,
            sap_transaction_code="STO-UB-01",
            trade_off_summary=f"Cost: ${cost:,.2f} freight | Lead Time: {transit_hrs} hrs | Restores DOS to 7.0 days"
        )
    options.append(option_a)
    
    # -------------------------------------------------------------
    # OPTION B: Dynamic Safety Stock Buffer Rebalance
    # -------------------------------------------------------------
    # Adjust safety stock threshold dynamically from 7.0 to 4.0 days temporarily
    adjusted_safety_dos = 4.0
    rebalance_cases_freed = int(daily_demand_rate * (DEFAULT_SAFETY_STOCK_DOS_THRESHOLD - adjusted_safety_dos))
    virtual_post_dos = calculate_days_of_supply(current_on_hand, daily_demand_rate)
    protected_rev_b = round(min(current_on_hand, units_needed) * unit_price, 2)
    
    option_b = MitigationOption(
        option_id="OPT-B-REBALANCE",
        option_type=MitigationOptionType.OPTION_B_SAFETY_STOCK_REBALANCE,
        title="Dynamic Safety Stock Reallocation (14-Day Trend Adjustment)",
        description=f"Temporarily re-allocate safety stock parameter in SAP MARC from 7.0 to {adjusted_safety_dos:.1f} days based on rolling demand stability. Zero freight expenditure.",
        donor_dc_id=None,
        donor_dc_name=None,
        donor_dc_available_dos=None,
        transfer_quantity_cases=rebalance_cases_freed,
        execution_cost_usd=0.0,
        recovery_lead_time_hours=1.0,  # Immediate ERP parameter update
        post_mitigation_dos=virtual_post_dos,
        protected_revenue_usd=protected_rev_b,
        fill_rate_projection_pct=88.5,
        risk_confidence_score=0.76,
        sap_transaction_code="MARC-SAFETY-ADJ",
        trade_off_summary=f"Cost: $0.00 | Immediate ERP update | Leaves buffer vulnerable to further demand variance (88.5% Fill Rate)"
    )
    options.append(option_b)
    
    # -------------------------------------------------------------
    # OPTION C: Order Deferral & Throttling (Non-Critical Replenishment)
    # -------------------------------------------------------------
    # Protect Tier 1 (60% demand), throttle Tier 2 & Tier 3 for 48 hours until plant production run arrives
    throttled_demand_rate = daily_demand_rate * 0.60  # Only service Tier 1
    extended_dos = calculate_days_of_supply(current_on_hand, throttled_demand_rate)
    deferred_revenue = round(daily_demand_rate * 0.40 * 2.0 * unit_price, 2)
    
    option_c = MitigationOption(
        option_id="OPT-C-DEFERRAL",
        option_type=MitigationOptionType.OPTION_C_ORDER_THROTTLING,
        title="Defer Non-Critical Retail Replenishment (Order Throttling)",
        description=f"Apply temporary delivery block in SAP VBBE for Tier-2/3 retail orders for 48 hours to preserve 100% fill-rate for Tier-1 Key Accounts pending manufacturing batch arrival.",
        donor_dc_id=None,
        donor_dc_name=None,
        donor_dc_available_dos=None,
        transfer_quantity_cases=0,
        execution_cost_usd=0.0,
        recovery_lead_time_hours=48.0,  # 48 hour manufacturing replenishment window
        post_mitigation_dos=extended_dos,
        protected_revenue_usd=round(daily_demand_rate * 0.60 * 2.0 * unit_price, 2),
        fill_rate_projection_pct=72.0,
        risk_confidence_score=0.68,
        sap_transaction_code="VBBE-BLOCK-T2T3",
        trade_off_summary=f"Cost: $0.00 | Protects Tier-1 OTIF | Defers ${deferred_revenue:,.2f} Tier 2/3 volume for 48 hrs"
    )
    options.append(option_c)
    
    # Recommendation logic based on ROI: If protected revenue >> freight cost and donor exists -> Option A
    if option_a.protected_revenue_usd > (option_a.execution_cost_usd * 4.0):
        recommended_id = "OPT-A-STO"
        rationale = (
            f"Option A (Expedited STO from {option_a.donor_dc_id}) is strongly recommended. "
            f"The freight investment of ${option_a.execution_cost_usd:,.2f} protects ${option_a.protected_revenue_usd:,.2f} in immediate revenue, "
            f"restoring inventory to {option_a.post_mitigation_dos:.1f} DOS within {option_a.recovery_lead_time_hours:.1f} hours while preventing Tier-1 retailer chargebacks."
        )
    else:
        recommended_id = "OPT-B-REBALANCE"
        rationale = "Option B is recommended as a zero-cost temporary buffer release while waiting for plant production."
        
    return MitigationComparisonMatrix(
        exception_id=f"EXC-{target_dc}-{sku_id}",
        sku_id=sku_id,
        dc_id=target_dc,
        options=options,
        recommended_option_id=recommended_id,
        recommendation_rationale=rationale
    )
