"""
Local Verification & A2UI Visual Test Runner for GEAP Agent
Validates GEAP tool responses and A2UI card generation.
"""

import sys
import os

# Add root directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geap_agent.agent_service import handle_morning_triage, handle_evaluate_mitigations, handle_execute_sap


def run_local_geap_tests():
    print("=" * 80)
    print("  PEPSICO GEAP ADK AGENT - LOCAL A2UI VERIFICATION")
    print("  Testing Gemini Enterprise Tool Endpoints & Visual Card Generation")
    print("=" * 80)
    print()

    # 1. Test Morning Triage Tool
    print(">>> 1. Testing /tools/morning-triage (SOP-SC-042 Step 1 & 2)...")
    triage_res = handle_morning_triage()
    assert triage_res["status"] == "SUCCESS"
    assert "a2ui_card_html" in triage_res
    assert len(triage_res["a2ui_card_html"]) > 100
    print(f"    [OK] Detected {triage_res['kpis']['total_exceptions']} exceptions (${triage_res['kpis']['daily_revenue_at_risk_usd']:,.2f}/day exposure).")
    print(f"    [OK] Generated A2UI.TriageScorecard HTML ({len(triage_res['a2ui_card_html'])} chars).\n")

    # 2. Test Mitigation Simulation Tool
    print(">>> 2. Testing /tools/evaluate-mitigations (SOP-SC-042 Step 3)...")
    mit_res = handle_evaluate_mitigations(sku_id="SKU-FL-101", dc_id="DC-ATL-03")
    assert mit_res["status"] == "SUCCESS"
    assert mit_res["recommended_option_id"] == "OPT-A-STO"
    assert "a2ui_card_html" in mit_res
    print(f"    [OK] Generated 3-way quantitative matrix for SKU-FL-101 at DC-ATL-03.")
    print(f"    [OK] Recommended Action: {mit_res['recommended_option_id']}")
    print(f"    [OK] Generated A2UI.MitigationMatrix HTML ({len(mit_res['a2ui_card_html'])} chars).\n")

    # 3. Test SAP Execution Tool
    print(">>> 3. Testing /tools/execute-sap (SOP-SC-042 Step 4)...")
    exec_res = handle_execute_sap(
        sku_id="SKU-FL-101",
        dc_id="DC-ATL-03",
        option_id="OPT-A-STO",
        planner_note="GEAP Local Verification Test"
    )
    assert exec_res["status"] == "SUCCESS"
    assert exec_res["sap_document_number"].startswith("4500")
    assert "a2ui_card_html" in exec_res
    print(f"    [OK] Confirmed SAP Purchase Order: #{exec_res['sap_document_number']} ({exec_res['transaction_code']}).")
    print(f"    [OK] Generated A2UI.SAPConfirmationToast HTML ({len(exec_res['a2ui_card_html'])} chars).\n")

    print("=" * 80)
    print("  [ALL TESTS PASSED] GEAP Agent & A2UI Components Ready for Gemini Enterprise!")
    print("=" * 80)


if __name__ == "__main__":
    run_local_geap_tests()
