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

    args = parser.parse_args()

    # Always ensure database exists
    populate_seed_data()

    if args.generate_brief:
        print("[*] Running Autonomous Morning Health Check & Generating Brief...")
        filepath = run_generate_daily_brief()
        print(f"[SUCCESS] Daily Exception Brief generated at: {filepath}")

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
