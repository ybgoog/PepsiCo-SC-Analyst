"""
Daily Supply Chain Exception & Action Brief Generator
Formats executive-ready Markdown reports adhering to SOP-SC-042 & MOP-SC-042.
"""

import os
from datetime import datetime
from typing import List, Optional
from pepsico_sc_agent.agent.core_agent import SupplyChainPlannerAgent
from pepsico_sc_agent.models.schemas import ExceptionAlert, MitigationComparisonMatrix, SeverityLevel
from pepsico_sc_agent.data.database import get_recent_sap_audit_trail


def generate_morning_brief_markdown(
    alerts: List[ExceptionAlert],
    matrices: List[MitigationComparisonMatrix],
    executive_commentary: str,
    output_filepath: Optional[str] = None
) -> str:
    """Generates the structured Daily Exception Brief in GitHub Flavored Markdown."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")

    critical_count = sum(1 for a in alerts if a.severity == SeverityLevel.CRITICAL)
    warning_count = sum(1 for a in alerts if a.severity == SeverityLevel.WARNING)
    total_rev_at_risk = sum(a.daily_revenue_at_risk for a in alerts)
    total_units_needed = sum(a.units_needed_for_target_dos for a in alerts)

    md = []
    md.append(f"# PepsiCo Daily Supply Chain Exception & Action Brief")
    md.append(f"**Date:** `{date_str}` | **Triage Run Time:** `{timestamp_str}`  ")
    md.append(f"**Standard Operating Procedure:** `SOP-SC-042` | **Architecture:** `MOP-SC-042`  ")
    md.append(f"**Author / Agent:** `PepsiCo Senior Supply Chain Demand & Inventory Planner Agent`\n")
    md.append("---\n")

    # Key Operational Metrics Bar
    md.append("## 1. Executive KPIs & Morning Risk Snapshot")
    md.append(f"| Metric | Value | Operational Status |")
    md.append(f"| :--- | :--- | :--- |")
    md.append(f"| **Active Portfolio Exceptions** | **{len(alerts)} SKUs** | {critical_count} Critical / {warning_count} Warning |")
    md.append(f"| **Cumulative Daily Revenue Exposure** | **${total_rev_at_risk:,.2f} / day** | High Value Focus |")
    md.append(f"| **Total Cases Required to Restore DOS** | **{total_units_needed:,} Cases** | Inter-DC Rebalance Required |")
    md.append(f"| **Network Baseline Target DOS** | **7.0 Days** | MOP-SC-042 Standard |\n")

    # Executive Commentary
    md.append("## 2. Executive Assessment & Root Cause Analysis")
    md.append(f"{executive_commentary}\n")

    # Exception Ranking Table
    md.append("## 3. Prioritized Exception Ranking (SOP-SC-042 Step 2)")
    md.append("Ranked by **Daily Revenue at Risk $\\times$ Customer Tier SLA Severity Multiplier**.\n")
    md.append("| Rank | Severity | SKU ID | Product Description | Distribution Center | On-Hand (Cases) | Daily Demand | Current DOS | Target DOS | Deficit | Daily Rev at Risk | Risk Score |")
    md.append("| :---: | :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    for idx, a in enumerate(alerts, 1):
        sev_badge = "🚨 CRITICAL" if a.severity == SeverityLevel.CRITICAL else "⚠️ WARNING"
        md.append(
            f"| **{idx}** | {sev_badge} | `{a.sku_id}` | **{a.sku_name}** | {a.dc_name} (`{a.dc_id}`) | "
            f"{a.current_on_hand:,} | {a.daily_demand_rate:,.0f}/day | **{a.current_dos:.1f}d** | "
            f"{a.safety_stock_dos_threshold:.1f}d | -{a.dos_deficit_days:.1f}d | "
            f"**${a.daily_revenue_at_risk:,.2f}** | `{a.sla_weighted_risk_score:.1f}` |"
        )
    md.append("\n")

    # Quantitative Mitigation Trade-Off Matrices
    md.append("## 4. Quantitative Mitigation Trade-Off Matrices (SOP-SC-042 Step 3)")
    md.append("For each critical exception, the agent simulated 3 distinct mitigation choices:\n")

    for idx, m in enumerate(matrices, 1):
        alert_item = next((a for a in alerts if a.sku_id == m.sku_id and a.dc_id == m.dc_id), None)
        item_title = f"{alert_item.sku_name} ({m.sku_id}) at {alert_item.dc_name}" if alert_item else f"{m.sku_id} at {m.dc_id}"
        
        md.append(f"### Exception {idx}: {item_title}")
        md.append(f"> **Agent Recommendation:** {m.recommendation_rationale}\n")
        
        md.append("| Option | Mitigation Strategy | Freight Cost | Recovery Lead Time | Post-Mitigation DOS | Protected Revenue | Projected Fill Rate | Confidence | SAP Action Code |")
        md.append("| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

        for opt in m.options:
            is_rec = " ⭐ **(Recommended)**" if opt.option_id == m.recommended_option_id else ""
            cost_str = f"${opt.execution_cost_usd:,.2f}" if opt.execution_cost_usd > 0 else "$0.00"
            md.append(
                f"| **{opt.option_type.value}** | **{opt.title}**{is_rec} | {cost_str} | "
                f"{opt.recovery_lead_time_hours:.1f} hrs | **{opt.post_mitigation_dos:.1f} DOS** | "
                f"${opt.protected_revenue_usd:,.2f} | {opt.fill_rate_projection_pct:.1f}% | "
                f"`{int(opt.risk_confidence_score * 100)}%` | `{opt.sap_transaction_code}` |"
            )
        md.append("\n")

    # SAP Audit Trail
    md.append("## 5. SAP ERP / IBP Execution Audit Trail (SOP-SC-042 Step 4)")
    recent_audits = get_recent_sap_audit_trail(limit=5)
    if recent_audits:
        md.append("| SAP Document # | Transaction Code | SKU ID | Source Plant | Destination Plant | Cases | Status | Timestamp | Audit Note |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :--- | :--- |")
        for audit in recent_audits:
            source = audit['source_plant'] if audit['source_plant'] else "N/A"
            md.append(
                f"| `{audit['sap_doc_number']}` | `{audit['transaction_code']}` | `{audit['sku_id']}` | "
                f"`{source}` | `{audit['destination_plant']}` | {audit['quantity_cases']:,} | "
                f"**{audit['execution_status']}** | {audit['timestamp']} | {audit['audit_message']} |"
            )
    else:
        md.append("*No SAP transactions executed yet for this session. Awaiting Planner HITL authorization.*")

    md.append("\n---\n*Report generated autonomously by PepsiCo Supply Chain Agent (ADK Suite) under SOP-SC-042.*")

    content = "\n".join(md)

    if output_filepath:
        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(content)

    return content


def run_generate_daily_brief(output_dir: Optional[str] = None) -> str:
    """Runs full pipeline and saves brief to disk."""
    agent = SupplyChainPlannerAgent()
    alerts = agent.run_morning_health_check()
    matrices = agent.evaluate_all_exceptions(alerts)
    commentary = agent.generate_executive_commentary(alerts, matrices)

    date_str = datetime.now().strftime("%Y%m%d")
    if not output_dir:
        output_dir = os.path.dirname(os.path.dirname(__file__))
    
    filename = f"Daily_Supply_Chain_Exception_Brief_{date_str}.md"
    filepath = os.path.join(output_dir, filename)

    generate_morning_brief_markdown(alerts, matrices, commentary, output_filepath=filepath)
    return filepath
