"""
BigQuery / SAP Semantic Data Layer for PepsiCo Supply Chain Agent
Provides SQLite persistence engine mimicking BigQuery enterprise views
over SAP tables (MARC, MARD, VBBE) and transaction execution logs.
"""

import sqlite3
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

DB_FILE_PATH = os.path.join(os.path.dirname(__file__), "pepsico_sc_inventory.db")


def get_db_connection(db_path: str = DB_FILE_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_FILE_PATH):
    """Initializes the database schema."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # 1. SKU Master Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sku_master (
        sku_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        brand TEXT NOT NULL,
        category TEXT NOT NULL,
        unit_wholesale_price REAL NOT NULL,
        case_pack INTEGER NOT NULL DEFAULT 12,
        pallet_cases INTEGER NOT NULL DEFAULT 60,
        weight_lbs_per_case REAL NOT NULL DEFAULT 15.0
    )
    """)

    # 2. SAP MARC Table: Plant / DC Material Master
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS marc_plant_data (
        plant_id TEXT NOT NULL,
        sku_id TEXT NOT NULL,
        safety_stock_units INTEGER NOT NULL,
        safety_stock_dos_target REAL NOT NULL DEFAULT 7.0,
        reorder_point_cases INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (plant_id, sku_id),
        FOREIGN KEY (sku_id) REFERENCES sku_master(sku_id)
    )
    """)

    # 3. SAP MARD Table: Storage Location Inventory Balances
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mard_storage_stock (
        plant_id TEXT NOT NULL,
        sku_id TEXT NOT NULL,
        storage_location TEXT NOT NULL DEFAULT '0001',
        unrestricted_stock INTEGER NOT NULL,
        quality_inspection_stock INTEGER NOT NULL DEFAULT 0,
        blocked_stock INTEGER NOT NULL DEFAULT 0,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (plant_id, sku_id, storage_location),
        FOREIGN KEY (sku_id) REFERENCES sku_master(sku_id)
    )
    """)

    # 4. SAP VBBE Table: Open Requirements & Sales Orders
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vbbe_open_requirements (
        requirement_id TEXT PRIMARY KEY,
        plant_id TEXT NOT NULL,
        sku_id TEXT NOT NULL,
        customer_tier TEXT NOT NULL,
        customer_name TEXT NOT NULL,
        order_quantity_cases INTEGER NOT NULL,
        requested_delivery_date DATE NOT NULL,
        otif_priority INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (sku_id) REFERENCES sku_master(sku_id)
    )
    """)

    # 5. Demand Profiles (30-day baseline vs overnight actuals)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS demand_profiles (
        dc_id TEXT NOT NULL,
        sku_id TEXT NOT NULL,
        baseline_daily_demand REAL NOT NULL,
        overnight_actual_orders REAL NOT NULL,
        surge_variance_pct REAL NOT NULL DEFAULT 0.0,
        tier_1_order_share REAL NOT NULL DEFAULT 0.60,
        tier_2_order_share REAL NOT NULL DEFAULT 0.25,
        tier_3_order_share REAL NOT NULL DEFAULT 0.15,
        PRIMARY KEY (dc_id, sku_id),
        FOREIGN KEY (sku_id) REFERENCES sku_master(sku_id)
    )
    """)

    # 6. SAP Execution Audit Trail Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sap_execution_audit (
        order_id TEXT PRIMARY KEY,
        sap_doc_number TEXT NOT NULL,
        transaction_code TEXT NOT NULL,
        sku_id TEXT NOT NULL,
        source_plant TEXT,
        destination_plant TEXT NOT NULL,
        quantity_cases INTEGER NOT NULL,
        execution_status TEXT NOT NULL,
        executed_by TEXT NOT NULL DEFAULT 'HITL_PLANNER',
        audit_message TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def query_inventory_semantic_view(plant_id: Optional[str] = None, sku_id: Optional[str] = None, db_path: str = DB_FILE_PATH) -> List[Dict[str, Any]]:
    """
    Simulates BigQuery semantic view: v_daily_inventory_health
    Joins SKU_MASTER, MARC, MARD, and DEMAND_PROFILES.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    query = """
    SELECT 
        s.sku_id,
        s.name AS sku_name,
        s.brand,
        s.category,
        s.unit_wholesale_price,
        s.pallet_cases,
        m.plant_id,
        m.safety_stock_units,
        m.safety_stock_dos_target,
        d.unrestricted_stock,
        d.quality_inspection_stock,
        d.blocked_stock,
        p.baseline_daily_demand,
        p.overnight_actual_orders,
        p.surge_variance_pct,
        p.tier_1_order_share,
        p.tier_2_order_share,
        p.tier_3_order_share
    FROM sku_master s
    JOIN marc_plant_data m ON s.sku_id = m.sku_id
    JOIN mard_storage_stock d ON m.plant_id = d.plant_id AND s.sku_id = d.sku_id
    JOIN demand_profiles p ON m.plant_id = p.dc_id AND s.sku_id = p.sku_id
    WHERE 1=1
    """
    params = []
    if plant_id:
        query += " AND m.plant_id = ?"
        params.append(plant_id)
    if sku_id:
        query += " AND s.sku_id = ?"
        params.append(sku_id)

    query += " ORDER BY m.plant_id, s.sku_id"

    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_all_dc_inventory_for_sku(sku_id: str, db_path: str = DB_FILE_PATH) -> Dict[str, Dict[str, Any]]:
    """Fetches stock and demand rates across all DCs for a single SKU."""
    rows = query_inventory_semantic_view(sku_id=sku_id, db_path=db_path)
    result = {}
    for r in rows:
        result[r["plant_id"]] = {
            "on_hand": r["unrestricted_stock"],
            "daily_demand": r["baseline_daily_demand"],
            "safety_stock_dos": r["safety_stock_dos_target"]
        }
    return result


def record_sap_execution(
    transaction_code: str,
    sku_id: str,
    source_plant: Optional[str],
    destination_plant: str,
    quantity_cases: int,
    executed_by: str = "HITL_PLANNER",
    audit_message: str = "",
    db_path: str = DB_FILE_PATH
) -> str:
    """
    Simulates posting an execution document back to SAP ERP / IBP.
    Updates MARD inventory stock if it is a Stock Transfer Order.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    order_id = f"ORD-{int(datetime.now().timestamp() * 1000)}"
    doc_prefix = "4500" if "STO" in transaction_code else "1000"
    sap_doc_number = f"{doc_prefix}{int(datetime.now().timestamp()) % 1000000:06d}"

    cursor.execute("""
    INSERT INTO sap_execution_audit (
        order_id, sap_doc_number, transaction_code, sku_id,
        source_plant, destination_plant, quantity_cases,
        execution_status, executed_by, audit_message
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order_id, sap_doc_number, transaction_code, sku_id,
        source_plant, destination_plant, quantity_cases,
        "POSTED", executed_by, audit_message
    ))

    # If STO, adjust simulated balances
    if source_plant and "STO" in transaction_code:
        # Deduct from source
        cursor.execute("""
        UPDATE mard_storage_stock
        SET unrestricted_stock = MAX(0, unrestricted_stock - ?)
        WHERE plant_id = ? AND sku_id = ?
        """, (quantity_cases, source_plant, sku_id))

        # Add to destination
        cursor.execute("""
        UPDATE mard_storage_stock
        SET unrestricted_stock = unrestricted_stock + ?
        WHERE plant_id = ? AND sku_id = ?
        """, (quantity_cases, destination_plant, sku_id))

    conn.commit()
    conn.close()
    return sap_doc_number


def get_recent_sap_audit_trail(limit: int = 10, db_path: str = DB_FILE_PATH) -> List[Dict[str, Any]]:
    """Fetches recent SAP transaction execution audit entries."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM sap_execution_audit ORDER BY timestamp DESC LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows
