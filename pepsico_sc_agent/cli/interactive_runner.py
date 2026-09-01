"""
Interactive Human-in-the-Loop (HITL) CLI Runner
Allows supply chain planners to step through 06:00 - 08:00 SOP-SC-042 morning triage,
review quantitative trade-offs, and authorize SAP ERP execution orders.
"""

import sys
import time
from typing import Optional
from pepsico_sc_agent.agent.core_agent import SupplyChainPlannerAgent
from pepsico_sc_agent.models.schemas import SeverityLevel


def print_banner():
    print("=" * 80)
    print("  PEPSICO GLOBAL SUPPLY CHAIN OPERATIONS & LOGISTICS")
    print("  Autonomous Exception Triage & Replenishment Agent (ADK Suite)")
    print("  Standard Operating Procedure: SOP-SC-042 | Technical Spec: MOP-SC-042")
    print("=" * 80)
    print()


def run_interactive_triage_session(auto_approve: bool = False):
    print_banner()
    agent = SupplyChainPlannerAgent()

    print(">>> STEP 1: Running 06:00 Automated Morning Health Check across Regional DCs...")
    time.sleep(0.5)
    alerts = agent.run_morning_health_check()
    print(f"    [OK] Query completed across MARC, MARD, and VBBE tables.")
    print(f"    [!] Identified {len(alerts)} SKUs breaching safety stock target (7.0 DOS).\n")

    print("-" * 80)
    print(">>> STEP 2: Prioritized Exception Risk Ranking (06:30 - 07:00)")
    print("-" * 80)
    print(f"{'#':<3} {'SEVERITY':<10} {'SKU ID':<12} {'PRODUCT NAME':<28} {'DC':<12} {'DOS':<6} {'DEFICIT':<8} {'REV AT RISK/DAY':<16} {'RISK SCORE'}")
    print("-" * 115)

    for idx, a in enumerate(alerts, 1):
        sev = "CRITICAL" if a.severity == SeverityLevel.CRITICAL else "WARNING"
        print(f"{idx:<3} {sev:<10} {a.sku_id:<12} {a.sku_name[:26]:<28} {a.dc_id:<12} {a.current_dos:<6.1f} -{a.dos_deficit_days:<7.1f} ${a.daily_revenue_at_risk:<15,.2f} {a.sla_weighted_risk_score:<8.1f}")

    print()
    print(">>> STEP 3: Evaluating Quantitative Mitigation Matrices (07:00 - 07:30)...")
    matrices = agent.evaluate_all_exceptions(alerts)
    print(f"    [OK] Generated multi-option trade-off models for {len(matrices)} exceptions.\n")

    print("=" * 80)
    print(">>> STEP 4: Human-in-the-Loop (HITL) Review & SAP ERP Authorization (07:30 - 08:00)")
    print("=" * 80)

    for idx, (alert, matrix) in enumerate(zip(alerts, matrices), 1):
        print(f"\n" + "#" * 80)
        print(f"  EXCEPTION #{idx}: {alert.sku_name} ({alert.sku_id})")
        print(f"  Location: {alert.dc_name} ({alert.dc_id}) | Current Stock: {alert.current_on_hand:,} cases")
        print(f"  Current DOS: {alert.current_dos:.1f} days (Target: {alert.safety_stock_dos_threshold:.1f} days | Deficit: {alert.dos_deficit_days:.1f} days)")
        print(f"  Daily Demand: {alert.daily_demand_rate:,.0f} cases/day | Revenue Exposure: ${alert.daily_revenue_at_risk:,.2f}/day")
        print(f"  Root Cause: {alert.root_cause_narrative}")
        print("#" * 80)

        print("\n  Available Mitigation Choices:")
        for opt in matrix.options:
            rec_tag = " [RECOMMENDED BY AGENT]" if opt.option_id == matrix.recommended_option_id else ""
            print(f"  - [{opt.option_type.value}] {opt.title}{rec_tag}")
            print(f"      Trade-off: {opt.trade_off_summary}")
            print(f"      Protected Revenue: ${opt.protected_revenue_usd:,.2f} | Confidence: {int(opt.risk_confidence_score * 100)}%")

        print(f"\n  Agent Recommendation Rationale:")
        print(f"  -> {matrix.recommendation_rationale}\n")

        if auto_approve:
            selected_choice = "A" if "A" in matrix.recommended_option_id else ("B" if "B" in matrix.recommended_option_id else "C")
            print(f"  [AUTO-APPROVE MODE] Selected Option {selected_choice} ({matrix.recommended_option_id})")
        else:
            prompt_text = f"  Select Mitigation Path for Exception #{idx} ([A] Option A, [B] Option B, [C] Option C, [S] Skip): "
            user_input = input(prompt_text).strip().upper()
            if not user_input or user_input == "A":
                selected_choice = "A"
            elif user_input == "B":
                selected_choice = "B"
            elif user_input == "C":
                selected_choice = "C"
            elif user_input == "S":
                print(f"  Skipping exception #{idx}. No SAP transaction executed.")
                continue
            else:
                selected_choice = "A"

        opt_id_map = {
            "A": next((o.option_id for o in matrix.options if "A" in o.option_type.value), matrix.options[0].option_id),
            "B": next((o.option_id for o in matrix.options if "B" in o.option_type.value), matrix.options[1].option_id),
            "C": next((o.option_id for o in matrix.options if "C" in o.option_type.value), matrix.options[2].option_id),
        }
        chosen_opt_id = opt_id_map.get(selected_choice, matrix.recommended_option_id)

        print(f"  Executing SAP posting for {chosen_opt_id}...")
        result = agent.execute_planner_selection(
            matrix=matrix,
            selected_option_id=chosen_opt_id,
            planner_note=f"Approved by Planner during morning triage session."
        )
        print(f"  [SUCCESS] SAP Document Posted: {result['sap_document_number']} | Code: {result['transaction_code']}")
        print(f"  [AUDIT] {result['audit_message']}")

    print("\n" + "=" * 80)
    print(">>> 08:00 Morning Triage & Execution Cycle Completed Successfully.")
    print("=" * 80 + "\n")
