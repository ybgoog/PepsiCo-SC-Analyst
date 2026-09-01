"""
Unit Tests for ADK Agent Tools
"""

import unittest
import os
from pepsico_sc_agent.data.seed_data import populate_seed_data
from pepsico_sc_agent.agent.tools import (
    query_inventory_semantic_layer,
    compute_dos_risk_matrix,
    simulate_mitigation_scenarios,
    execute_sap_action,
    get_audit_history
)
from pepsico_sc_agent.models.schemas import SeverityLevel


class TestAgentTools(unittest.TestCase):

    def setUp(self):
        populate_seed_data()

    def test_query_inventory_semantic_layer(self):
        rows = query_inventory_semantic_layer(plant_id="DC-ATL-03", sku_id="SKU-FL-101")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["sku_name"], "Lay's Classic Potato Chips 8oz Party Size")
        self.assertEqual(rows[0]["unrestricted_stock"], 1440)

    def test_compute_dos_risk_matrix(self):
        alerts = compute_dos_risk_matrix(target_dos_threshold=7.0)
        self.assertGreater(len(alerts), 0)
        # Verify ranked order (highest risk score first)
        for i in range(len(alerts) - 1):
            self.assertGreaterEqual(alerts[i].sla_weighted_risk_score, alerts[i+1].sla_weighted_risk_score)
        
        # Check that top alert is Critical
        self.assertEqual(alerts[0].severity, SeverityLevel.CRITICAL)

    def test_simulate_mitigation_scenarios(self):
        matrix = simulate_mitigation_scenarios(dc_id="DC-ATL-03", sku_id="SKU-FL-101")
        self.assertEqual(len(matrix.options), 3)
        self.assertEqual(matrix.recommended_option_id, "OPT-A-STO")
        
        opt_a = next(o for o in matrix.options if o.option_id == "OPT-A-STO")
        self.assertEqual(opt_a.donor_dc_id, "DC-DAL-01")
        self.assertGreater(opt_a.protected_revenue_usd, 50000.0)

    def test_execute_sap_action(self):
        result = execute_sap_action(
            action_type="STO-UB-01",
            sku_id="SKU-FL-101",
            source_plant="DC-DAL-01",
            destination_plant="DC-ATL-03",
            quantity_cases=4160,
            auth_token="TEST_TOKEN",
            planner_note="Test Execution"
        )
        self.assertEqual(result["status"], "SUCCESS")
        self.assertIn("sap_document_number", result)
        
        # Verify audit history
        audit = get_audit_history(limit=1)
        self.assertEqual(len(audit), 1)
        self.assertEqual(audit[0]["sku_id"], "SKU-FL-101")


if __name__ == "__main__":
    unittest.main()
