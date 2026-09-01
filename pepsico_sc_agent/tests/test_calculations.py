"""
Unit Tests for Supply Chain Algorithmic Calculations (MOP-SC-042)
"""

import unittest
from pepsico_sc_agent.models.calculations import (
    calculate_days_of_supply,
    calculate_dos_deficit,
    calculate_units_needed,
    calculate_sla_weighted_risk_score,
    calculate_linehaul_transit,
    simulate_all_mitigation_options
)


class TestSupplyChainCalculations(unittest.TestCase):

    def test_days_of_supply_normal(self):
        # 1440 cases / 800 cases/day = 1.8 DOS
        dos = calculate_days_of_supply(1440, 800)
        self.assertEqual(dos, 1.8)

    def test_days_of_supply_zero_demand(self):
        dos = calculate_days_of_supply(1000, 0)
        self.assertEqual(dos, 999.0)

    def test_dos_deficit(self):
        # Target 7.0 - Current 1.8 = 5.2 days deficit
        deficit = calculate_dos_deficit(1.8, target_dos=7.0)
        self.assertEqual(deficit, 5.2)

        # Healthy stock -> Deficit is 0.0
        deficit_healthy = calculate_dos_deficit(8.5, target_dos=7.0)
        self.assertEqual(deficit_healthy, 0.0)

    def test_units_needed(self):
        # 5.2 days deficit * 800 demand = 4160 cases
        units = calculate_units_needed(5.2, 800)
        self.assertEqual(units, 4160)

    def test_sla_weighted_risk_score(self):
        # Daily demand: 800, Unit price: $38.50 -> Daily revenue: $30,800
        rev, risk_score = calculate_sla_weighted_risk_score(
            dos_deficit=5.2,
            daily_demand_rate=800,
            unit_wholesale_price=38.50,
            tier_1_share=0.60,
            tier_2_share=0.25,
            tier_3_share=0.15
        )
        self.assertEqual(rev, 30800.0)
        self.assertGreater(risk_score, 0)

    def test_linehaul_transit(self):
        # Dallas to Atlanta: 780 miles
        cost, transit_hrs, pallets = calculate_linehaul_transit(
            origin_dc="DC-DAL-01",
            dest_dc="DC-ATL-03",
            quantity_cases=4160,
            pallet_cases=60,
            expedited=True
        )
        self.assertGreater(cost, 0)
        self.assertGreater(transit_hrs, 10.0)
        self.assertEqual(pallets, 70)  # ceil(4160/60) = 70


if __name__ == "__main__":
    unittest.main()
