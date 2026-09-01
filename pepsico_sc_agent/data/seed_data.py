"""
Seed Data Generator for PepsiCo Supply Chain Agent
Populates synthetic SKU master, inventory balances (MARC/MARD),
and open demand profiles (VBBE) across regional distribution hubs.
"""

from typing import Optional
from pepsico_sc_agent.data.database import (
    get_db_connection,
    init_db,
    DB_FILE_PATH
)
from pepsico_sc_agent.models.schemas import ProductCategory


def populate_seed_data(db_path: str = DB_FILE_PATH):
    """Initializes and seeds the database with realistic PepsiCo supply chain data."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Clear existing seed data (except audit logs)
    cursor.execute("DELETE FROM vbbe_open_requirements")
    cursor.execute("DELETE FROM demand_profiles")
    cursor.execute("DELETE FROM mard_storage_stock")
    cursor.execute("DELETE FROM marc_plant_data")
    cursor.execute("DELETE FROM sku_master")

    # 1. SKU Master Catalog
    skus = [
        ("SKU-FL-101", "Lay's Classic Potato Chips 8oz Party Size", "Lay's", ProductCategory.SALTY_SNACKS.value, 38.50, 12, 60, 14.5),
        ("SKU-FL-102", "Doritos Nacho Cheese Tortilla Chips 9.25oz", "Doritos", ProductCategory.SALTY_SNACKS.value, 42.00, 12, 60, 15.0),
        ("SKU-FL-103", "Cheetos Crunchy Cheese Flavored 8.5oz", "Cheetos", ProductCategory.SALTY_SNACKS.value, 39.00, 12, 60, 14.0),
        ("SKU-PB-201", "Pepsi Cola 12oz 12-Pack Cans", "Pepsi", ProductCategory.CARBONATED_BEVERAGES.value, 28.00, 2, 80, 22.0),
        ("SKU-PB-202", "bubly Sparkling Water 12oz 8-Pack", "bubly", ProductCategory.CARBONATED_BEVERAGES.value, 22.50, 3, 90, 18.0),
        ("SKU-PB-203", "Mountain Dew 20oz Bottles 24-Pack", "Mountain Dew", ProductCategory.CARBONATED_BEVERAGES.value, 32.00, 1, 54, 32.0),
        ("SKU-GT-301", "Gatorade Cool Blue 28oz 15-Pack", "Gatorade", ProductCategory.SPORTS_HYDRATION.value, 34.00, 1, 60, 30.0),
        ("SKU-GT-302", "Gatorade Zero Fruit Punch 20oz 24-Pack", "Gatorade", ProductCategory.SPORTS_HYDRATION.value, 36.50, 1, 54, 33.0),
        ("SKU-QK-401", "Quaker Quick 1-Minute Oats 42oz Canister", "Quaker", ProductCategory.CONVENIENT_FOODS.value, 46.00, 12, 45, 34.0),
        ("SKU-QK-402", "Quaker Chewy Granola Bars Variety 58ct", "Quaker", ProductCategory.CONVENIENT_FOODS.value, 31.00, 6, 60, 20.0),
    ]

    cursor.executemany("""
    INSERT INTO sku_master (sku_id, name, brand, category, unit_wholesale_price, case_pack, pallet_cases, weight_lbs_per_case)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, skus)

    # 2. Plant Master & Inventory Matrix across 4 DCs
    # DC-DAL-01: Dallas Hub (Primary Plant / High Surplus)
    # DC-CHI-02: Chicago Central DC
    # DC-ATL-03: Atlanta Metro DC (High retail demand)
    # DC-NE-04:  Northeast Hub (Breinigsville)

    # Matrix: (plant_id, sku_id, safety_target_dos, unrestricted_cases, daily_demand, surge_pct, t1_share)
    inventory_matrix = [
        # --- Lay's Classic (SKU-FL-101) ---
        ("DC-DAL-01", "SKU-FL-101", 7.0, 18200, 800.0, 0.05, 0.60),  # Surplus donor: 22.7 DOS
        ("DC-CHI-02", "SKU-FL-101", 7.0, 6400, 750.0, 0.10, 0.60),   # Healthy: 8.5 DOS
        ("DC-ATL-03", "SKU-FL-101", 7.0, 1440, 800.0, 0.60, 0.65),   # CRITICAL DEFICIT: 1.8 DOS (Overnight promo surge)
        ("DC-NE-04",  "SKU-FL-101", 7.0, 7200, 700.0, 0.00, 0.55),   # Healthy: 10.3 DOS

        # --- Doritos Nacho Cheese (SKU-FL-102) ---
        ("DC-DAL-01", "SKU-FL-102", 7.0, 13500, 900.0, 0.00, 0.60),  # Surplus: 15.0 DOS
        ("DC-CHI-02", "SKU-FL-102", 7.0, 2160, 900.0, 0.45, 0.70),   # CRITICAL DEFICIT: 2.4 DOS (Sudden Key Account surge)
        ("DC-ATL-03", "SKU-FL-102", 7.0, 6800, 800.0, 0.05, 0.60),   # Healthy: 8.5 DOS
        ("DC-NE-04",  "SKU-FL-102", 7.0, 14400, 850.0, 0.00, 0.55),  # Surplus donor: 16.9 DOS

        # --- Pepsi Cola 12-Pack (SKU-PB-201) ---
        ("DC-DAL-01", "SKU-PB-201", 7.0, 11000, 1000.0, 0.00, 0.60), # Healthy: 11.0 DOS
        ("DC-CHI-02", "SKU-PB-201", 7.0, 8500, 950.0, 0.05, 0.60),   # Healthy: 8.9 DOS
        ("DC-ATL-03", "SKU-PB-201", 7.0, 2610, 900.0, 0.35, 0.65),   # CRITICAL DEFICIT: 2.9 DOS
        ("DC-NE-04",  "SKU-PB-201", 7.0, 16000, 950.0, 0.00, 0.55),  # Surplus donor: 16.8 DOS

        # --- Gatorade Cool Blue (SKU-GT-301) ---
        ("DC-DAL-01", "SKU-GT-301", 7.0, 8400, 600.0, 0.00, 0.60),   # Healthy: 14.0 DOS
        ("DC-CHI-02", "SKU-GT-301", 7.0, 11700, 600.0, 0.00, 0.60),  # Surplus donor: 19.5 DOS
        ("DC-ATL-03", "SKU-GT-301", 7.0, 5200, 550.0, 0.00, 0.60),   # Healthy: 9.45 DOS
        ("DC-NE-04",  "SKU-GT-301", 7.0, 2050, 600.0, 0.25, 0.65),   # WARNING DEFICIT: 3.4 DOS

        # --- bubly Sparkling Water (SKU-PB-202) ---
        ("DC-DAL-01", "SKU-PB-202", 7.0, 4800, 400.0, 0.00, 0.50),   # Healthy: 12.0 DOS
        ("DC-CHI-02", "SKU-PB-202", 7.0, 1680, 400.0, 0.20, 0.55),   # WARNING DEFICIT: 4.2 DOS
        ("DC-ATL-03", "SKU-PB-202", 7.0, 3600, 380.0, 0.00, 0.50),   # Healthy: 9.5 DOS
        ("DC-NE-04",  "SKU-PB-202", 7.0, 4400, 420.0, 0.00, 0.50),   # Healthy: 10.5 DOS

        # --- Cheetos Crunchy (SKU-FL-103) ---
        ("DC-DAL-01", "SKU-FL-103", 7.0, 6000, 500.0, 0.00, 0.60),   # Healthy: 12.0 DOS
        ("DC-CHI-02", "SKU-FL-103", 7.0, 5500, 520.0, 0.00, 0.60),   # Healthy: 10.6 DOS
        ("DC-ATL-03", "SKU-FL-103", 7.0, 4900, 480.0, 0.00, 0.60),   # Healthy: 10.2 DOS
        ("DC-NE-04",  "SKU-FL-103", 7.0, 5800, 500.0, 0.00, 0.60),   # Healthy: 11.6 DOS

        # --- Mountain Dew 20oz (SKU-PB-203) ---
        ("DC-DAL-01", "SKU-PB-203", 7.0, 4500, 450.0, 0.00, 0.60),   # Healthy: 10.0 DOS
        ("DC-CHI-02", "SKU-PB-203", 7.0, 4200, 440.0, 0.00, 0.60),   # Healthy: 9.5 DOS
        ("DC-ATL-03", "SKU-PB-203", 7.0, 4000, 420.0, 0.00, 0.60),   # Healthy: 9.5 DOS
        ("DC-NE-04",  "SKU-PB-203", 7.0, 4800, 460.0, 0.00, 0.60),   # Healthy: 10.4 DOS

        # --- Gatorade Zero (SKU-GT-302) ---
        ("DC-DAL-01", "SKU-GT-302", 7.0, 4200, 400.0, 0.00, 0.60),   # Healthy: 10.5 DOS
        ("DC-CHI-02", "SKU-GT-302", 7.0, 3900, 390.0, 0.00, 0.60),   # Healthy: 10.0 DOS
        ("DC-ATL-03", "SKU-GT-302", 7.0, 3800, 380.0, 0.00, 0.60),   # Healthy: 10.0 DOS
        ("DC-NE-04",  "SKU-GT-302", 7.0, 4100, 400.0, 0.00, 0.60),   # Healthy: 10.25 DOS

        # --- Quaker Oats 42oz (SKU-QK-401) ---
        ("DC-DAL-01", "SKU-QK-401", 7.0, 3600, 300.0, 0.00, 0.50),   # Healthy: 12.0 DOS
        ("DC-CHI-02", "SKU-QK-401", 7.0, 3400, 310.0, 0.00, 0.50),   # Healthy: 11.0 DOS
        ("DC-ATL-03", "SKU-QK-401", 7.0, 3000, 290.0, 0.00, 0.50),   # Healthy: 10.3 DOS
        ("DC-NE-04",  "SKU-QK-401", 7.0, 3500, 320.0, 0.00, 0.50),   # Healthy: 10.9 DOS

        # --- Quaker Chewy Bars (SKU-QK-402) ---
        ("DC-DAL-01", "SKU-QK-402", 7.0, 4000, 350.0, 0.00, 0.50),   # Healthy: 11.4 DOS
        ("DC-CHI-02", "SKU-QK-402", 7.0, 3800, 340.0, 0.00, 0.50),   # Healthy: 11.2 DOS
        ("DC-ATL-03", "SKU-QK-402", 7.0, 3600, 330.0, 0.00, 0.50),   # Healthy: 10.9 DOS
        ("DC-NE-04",  "SKU-QK-402", 7.0, 3900, 360.0, 0.00, 0.50),   # Healthy: 10.8 DOS
    ]

    for item in inventory_matrix:
        plant_id, sku_id, target_dos, unrestricted, daily_demand, surge_pct, t1_share = item
        safety_stock_cases = int(target_dos * daily_demand)
        
        # Insert into MARC
        cursor.execute("""
        INSERT INTO marc_plant_data (plant_id, sku_id, safety_stock_units, safety_stock_dos_target, reorder_point_cases)
        VALUES (?, ?, ?, ?, ?)
        """, (plant_id, sku_id, safety_stock_cases, target_dos, int(safety_stock_cases * 1.5)))

        # Insert into MARD
        cursor.execute("""
        INSERT INTO mard_storage_stock (plant_id, sku_id, storage_location, unrestricted_stock, quality_inspection_stock, blocked_stock)
        VALUES (?, ?, '0001', ?, 0, 0)
        """, (plant_id, sku_id, unrestricted))

        # Insert into DEMAND_PROFILES
        overnight_orders = daily_demand * (1.0 + surge_pct)
        t2_share = (1.0 - t1_share) * 0.65
        t3_share = (1.0 - t1_share) * 0.35
        cursor.execute("""
        INSERT INTO demand_profiles (dc_id, sku_id, baseline_daily_demand, overnight_actual_orders, surge_variance_pct, tier_1_order_share, tier_2_order_share, tier_3_order_share)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (plant_id, sku_id, daily_demand, overnight_orders, surge_pct * 100.0, t1_share, t2_share, t3_share))

    # 3. Open Requirements (VBBE) for Key Accounts
    sample_vbbe = [
        ("REQ-WMT-101", "DC-ATL-03", "SKU-FL-101", "TIER_1", "Walmart Regional Distribution Center 6012", 450, "2026-09-02", 1),
        ("REQ-TGT-102", "DC-ATL-03", "SKU-FL-101", "TIER_1", "Target Distribution Center T-0581", 320, "2026-09-02", 1),
        ("REQ-KRG-103", "DC-ATL-03", "SKU-FL-101", "TIER_1", "Kroger Atlanta Hub", 280, "2026-09-02", 1),
        ("REQ-WMT-201", "DC-CHI-02", "SKU-FL-102", "TIER_1", "Walmart DC 7044", 520, "2026-09-02", 1),
        ("REQ-CST-202", "DC-CHI-02", "SKU-FL-102", "TIER_1", "Costco Wholesale Midwest Depot", 380, "2026-09-02", 1),
        ("REQ-KRG-301", "DC-ATL-03", "SKU-PB-201", "TIER_1", "Kroger Southeast Logistics", 480, "2026-09-02", 1),
    ]

    cursor.executemany("""
    INSERT INTO vbbe_open_requirements (requirement_id, plant_id, sku_id, customer_tier, customer_name, order_quantity_cases, requested_delivery_date, otif_priority)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_vbbe)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    populate_seed_data()
    print("Successfully populated PepsiCo supply chain database.")
