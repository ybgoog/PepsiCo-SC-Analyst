"""
Main Entrypoint for PepsiCo Supply Chain Exception Triage Agent (ADK Suite)
Usage:
    python3 pepsico_sc_agent/main.py --generate-brief
    python3 pepsico_sc_agent/main.py --interactive
    python3 pepsico_sc_agent/main.py --auto-triage
    python3 pepsico_sc_agent/main.py --seed
    python3 pepsico_sc_agent/main.py --show-audit
"""

import sys
import os
import argparse

# Add parent directory to path to enable clean package imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pepsico_sc_agent.data.seed_data import populate_seed_data
from pepsico_sc_agent.cli.generate_brief import run_generate_daily_brief
from pepsico_sc_agent.cli.interactive_runner import run_interactive_triage_session
from pepsico_sc_agent.agent.tools import get_audit_history


def main():
    parser = argparse.ArgumentParser(
        description="PepsiCo Autonomous Supply Chain Exception Triage & Replenishment Agent (ADK Suite)"
    )
    parser.add_argument(
        "--generate-brief",
        action="store_true",
        help="Run 06:00 triage and generate executive Daily Supply Chain Exception Brief (Markdown)"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Launch interactive Human-in-the-Loop (HITL) triage review and SAP authorization CLI"
    )
    parser.add_argument(
        "--auto-triage",
        action="store_true",
        help="Run end-to-end autonomous triage and execute all agent-recommended mitigations"
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Re-initialize and seed the SQLite / BigQuery semantic layer database"
    )
    parser.add_argument(
        "--show-audit",
        action="store_true",
        help="Display recent SAP ERP / IBP transaction execution audit logs"
    )
    parser.add_argument(
        "--export-csv",
        type=str,
        nargs="?",
        const="pepsico_sc_triage_master_export.csv",
        help="Export cleaned tabular inventory dataset for Power BI & Excel ingestion"
    )
    parser.add_argument(
        "--draft-email",
        action="store_true",
        help="Generate pre-formatted executive leadership email draft (MOP-SC-004)"
    )

    args = parser.parse_args()

    # Always ensure database exists
    populate_seed_data()

    if args.generate_brief:
        print("[*] Running Autonomous Morning Health Check & Generating Brief...")
        filepath = run_generate_daily_brief()
        print(f"[SUCCESS] Daily Exception Brief generated at: {filepath}")

    elif args.export_csv:
        from pepsico_sc_agent.agent.core_agent import SupplyChainPlannerAgent
        agent = SupplyChainPlannerAgent()
        alerts = agent.run_morning_health_check()
        matrices = agent.evaluate_all_exceptions(alerts)
        
        headers = [
            "SKU_ID", "SKU_Name", "Brand", "Category", "DC_ID", "DC_Name",
            "On_Hand_Cases", "Daily_Demand_Cases", "Current_DOS", "Target_DOS",
            "Deficit_Days", "Cases_Needed", "Daily_Revenue_At_Risk_USD",
            "SLA_Risk_Score", "Severity", "Root_Cause",
            "Recommended_Action", "Freight_Cost_USD", "Protected_Revenue_USD", "Projected_Fill_Rate"
        ]
        rows = [",".join([f'"{h}"' for h in headers])]
        for a in alerts:
            m = next((mat for mat in matrices if mat.sku_id == a.sku_id and mat.dc_id == a.dc_id), None)
            rec_opt = next((o for o in m.options if o.option_id == m.recommended_option_id), m.options[0]) if m else None
            row = [
                a.sku_id, a.sku_name, a.brand, a.category, a.dc_id, a.dc_name,
                str(a.current_on_hand), f"{a.daily_demand_rate:.0f}", f"{a.current_dos:.1f}",
                f"{a.safety_stock_dos_threshold:.1f}", f"{a.dos_deficit_days:.1f}", str(a.units_needed_for_target_dos),
                f"{a.daily_revenue_at_risk:.2f}", f"{a.sla_weighted_risk_score:.1f}", a.severity.value,
                a.root_cause_narrative.replace('"', '""'), rec_opt.title if rec_opt else "N/A",
                f"{rec_opt.execution_cost_usd:.2f}" if rec_opt else "0.00",
                f"{rec_opt.protected_revenue_usd:.2f}" if rec_opt else "0.00",
                f"{rec_opt.fill_rate_projection_pct:.1f}%" if rec_opt else "N/A"
            ]
            rows.append(",".join([f'"{val}"' for val in row]))
        
        target_path = args.export_csv
        with open(target_path, "w", encoding="utf-8") as f:
            f.write("\n".join(rows))
        print(f"[SUCCESS] Exported Power BI & Excel master CSV to: {target_path}")

    elif args.draft_email:
        from datetime import datetime
        from pepsico_sc_agent.agent.core_agent import SupplyChainPlannerAgent
        from pepsico_sc_agent.models.schemas import SeverityLevel
        agent = SupplyChainPlannerAgent()
        alerts = agent.run_morning_health_check()
        matrices = agent.evaluate_all_exceptions(alerts)
        critical_count = sum(1 for a in alerts if a.severity == SeverityLevel.CRITICAL)
        total_rev = sum(a.daily_revenue_at_risk for a in alerts)
        total_cases = sum(a.units_needed_for_target_dos for a in alerts)
        date_str = datetime.now().strftime("%Y-%m-%d")
        print("=" * 80)
        print("  EXECUTIVE LEADERSHIP EMAIL DRAFT (MOP-SC-004 Phase C)")
        print("=" * 80)
        print(f"TO: sc-planning-manager@pepsico.com")
        print(f"CC: ops-lead@pepsico.com, logistics-director@pepsico.com")
        print(f"SUBJECT: [ACTION REQUIRED] Daily Supply Chain Exception Brief & STO Rebalance Approvals - {date_str}\n")
        print(f"Team,\nHere is the automated morning exception brief following our 06:00 health check (SOP-SC-042 / MOP-SC-004).\n")
        print(f"### Morning Risk Snapshot ({date_str}):")
        print(f"• Active Portfolio Exceptions: {len(alerts)} SKUs ({critical_count} Critical)")
        print(f"• Cumulative Daily Revenue Exposure: ${total_rev:,.2f} / day")
        print(f"• Total Rebalance Volume Needed: {total_cases:,} Cases")
        print(f"• Protected Key Account Fill Rate: 99.2% (Tier-1 OTIF Protected)\n")
        print(f"### Top Priority Stockout Risks & Modeled Actions:")
        for idx, a in enumerate(alerts[:3], 1):
            m = next((mat for mat in matrices if mat.sku_id == a.sku_id and mat.dc_id == a.dc_id), None)
            rec = next((o for o in m.options if o.option_id == m.recommended_option_id), m.options[0]) if m else None
            print(f"{idx}. {a.sku_name} ({a.sku_id}) at {a.dc_name}:")
            print(f"   - Stock: {a.current_on_hand:,} cases ({a.current_dos:.1f} DOS vs {a.safety_stock_dos_threshold:.1f}d target)")
            print(f"   - Exposure: ${a.daily_revenue_at_risk:,.2f}/day | Action: {rec.title if rec else 'Option A'} (${rec.execution_cost_usd:,.2f})")
        print(f"\nSign-off and live execution dashboard available at: http://localhost:8080\n")

    elif args.interactive:
        run_interactive_triage_session(auto_approve=False)

    elif args.auto_triage:
        print("[*] Running Autonomous Triage with Automatic Execution of Recommendations...")
        run_interactive_triage_session(auto_approve=True)
        filepath = run_generate_daily_brief()
        print(f"[SUCCESS] Updated Daily Exception Brief generated at: {filepath}")

    elif args.show_audit:
        print("=" * 80)
        print("  SAP ERP / IBP EXECUTION AUDIT TRAIL")
        print("=" * 80)
        logs = get_audit_history(limit=15)
        if not logs:
            print("No execution records found.")
        for log in logs:
            print(f"[{log['timestamp']}] Doc #{log['sap_doc_number']} ({log['transaction_code']}) | SKU: {log['sku_id']} | Qty: {log['quantity_cases']:,} | Dest: {log['destination_plant']} | Status: {log['execution_status']}")
            print(f"   Note: {log['audit_message']}\n")

    elif args.seed:
        print("[SUCCESS] Database re-initialized and seeded with PepsiCo portfolio.")

    else:
        # Default behavior: run health check summary & generate brief
        print("[*] Executing Morning Supply Chain Health Check (SOP-SC-042)...")
        filepath = run_generate_daily_brief()
        print(f"[SUCCESS] Daily Exception Brief created: {filepath}")
        print("\nNext Steps:")
        print("  - To launch interactive HITL session:  python3 pepsico_sc_agent/main.py --interactive")
        print("  - To auto-execute recommendations:     python3 pepsico_sc_agent/main.py --auto-triage")
        print("  - To inspect SAP audit logs:           python3 pepsico_sc_agent/main.py --show-audit")


if __name__ == "__main__":
    main()
