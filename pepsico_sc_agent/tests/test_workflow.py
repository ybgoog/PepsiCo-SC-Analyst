"""
End-to-End Workflow Integration Test (SOP-SC-042 Steps 1 to 4)
"""

import unittest
from pepsico_sc_agent.data.seed_data import populate_seed_data
from pepsico_sc_agent.agent.core_agent import SupplyChainPlannerAgent
from pepsico_sc_agent.cli.generate_brief import generate_morning_brief_markdown


class TestWorkflowEndToEnd(unittest.TestCase):

    def setUp(self):
        populate_seed_data()
        self.agent = SupplyChainPlannerAgent()

    def test_complete_sop_sc_042_cycle(self):
        # Step 1 & 2: Automated Morning Health Check & Ranking
        alerts = self.agent.run_morning_health_check()
        self.assertTrue(len(alerts) >= 3, "Should detect at least 3 critical inventory exceptions")

        # Step 3: Mitigation Option Modeling
        matrices = self.agent.evaluate_all_exceptions(alerts)
        self.assertEqual(len(matrices), len(alerts))

        # Generate Executive Commentary
        commentary = self.agent.generate_executive_commentary(alerts, matrices)
        self.assertIn("Executive Summary", commentary)

        # Generate Brief Markdown
        brief_md = generate_morning_brief_markdown(alerts, matrices, commentary)
        self.assertIn("PepsiCo Daily Supply Chain Exception & Action Brief", brief_md)
        self.assertIn("SOP-SC-042", brief_md)
        self.assertIn("MOP-SC-042", brief_md)

        # Step 4: HITL Selection & SAP Execution
        top_matrix = matrices[0]
        exec_result = self.agent.execute_planner_selection(
            matrix=top_matrix,
            selected_option_id=top_matrix.recommended_option_id,
            planner_note="Approved during test cycle"
        )
        self.assertEqual(exec_result["status"], "SUCCESS")
        self.assertTrue(exec_result["sap_document_number"].startswith("4500"))


if __name__ == "__main__":
    unittest.main()
