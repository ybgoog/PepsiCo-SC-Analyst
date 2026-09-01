"""
A2UI (Agent-to-User-Interface) Component Renderer for Gemini Enterprise (GEAP)
Generates rich, high-contrast, responsive visual card blocks rendered directly
inside Gemini Enterprise / Google Agentspace chat interfaces.
"""

from typing import List, Dict, Any


def render_triage_scorecard_a2ui(
    alerts: List[Dict[str, Any]],
    critical_count: int,
    warning_count: int,
    total_rev_at_risk: float,
    total_cases_needed: int
) -> str:
    """Renders the A2UI.TriageScorecard visual widget for morning health checks."""
    rows_html = []
    for idx, a in enumerate(alerts[:5], 1):
        sev_color = "#f87171" if a["severity"] == "CRITICAL" else "#fbbf24"
        sev_badge = f'<span style="background:rgba(239,68,68,0.2); color:{sev_color}; padding:2px 8px; border-radius:4px; font-weight:700; font-size:10px;">{a["severity"]}</span>'
        bar_pct = min(100, int((a["current_dos"] / a["safety_stock_dos_threshold"]) * 100))
        
        rows_html.append(f"""
        <tr style="border-bottom:1px solid #24324d;">
            <td style="padding:10px 12px; font-family:monospace; font-weight:bold;">{idx}</td>
            <td style="padding:10px 12px;">{sev_badge}</td>
            <td style="padding:10px 12px; font-weight:600; color:#ffffff;">{a['sku_name']}<br><span style="font-size:11px; color:#94a3b8; font-family:monospace;">{a['sku_id']} • {a['dc_name']}</span></td>
            <td style="padding:10px 12px;">
                <span style="font-family:monospace; font-weight:bold; color:#ffffff;">{a['current_dos']:.1f}d / {a['safety_stock_dos_threshold']:.1f}d</span>
                <div style="width:80px; height:5px; background:#1e293b; border-radius:3px; margin-top:4px; overflow:hidden;">
                    <div style="width:{bar_pct}%; height:100%; background:{sev_color};"></div>
                </div>
            </td>
            <td style="padding:10px 12px; font-family:monospace; color:#38bdf8; font-weight:700;">${a['daily_revenue_at_risk']:,.2f}</td>
        </tr>
        """)

    rows_joined = "".join(rows_html)

    return f"""
<div class="a2ui-card" style="background:#0d1527; border:1px solid #1f3154; border-radius:12px; padding:20px; font-family:'Inter',system-ui,sans-serif; color:#f8fafc; max-width:760px; box-shadow:0 10px 30px rgba(0,0,0,0.5);">
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1f3154; padding-bottom:12px; margin-bottom:16px;">
        <div style="display:flex; align-items:center; gap:10px;">
            <div style="width:28px; height:28px; border-radius:50%; background:linear-gradient(135deg, #005cb9 45%, #ffffff 45%, #ffffff 55%, #e32219 55%);"></div>
            <div>
                <div style="font-size:15px; font-weight:800; color:#ffffff;">PepsiCo Morning Exception Triage</div>
                <div style="font-size:11px; color:#94a3b8;">SOP-SC-042 • Automated Health Check</div>
            </div>
        </div>
        <span style="background:rgba(56,189,248,0.15); color:#38bdf8; border:1px solid rgba(56,189,248,0.3); padding:3px 10px; border-radius:6px; font-size:11px; font-weight:700; font-family:monospace;">06:30 RUN</span>
    </div>

    <!-- KPI Metric Summary -->
    <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:12px; margin-bottom:16px;">
        <div style="background:#131f38; border:1px solid #1f3154; border-radius:8px; padding:12px;">
            <div style="font-size:10px; font-weight:700; color:#94a3b8; text-transform:uppercase;">Exceptions</div>
            <div style="font-size:22px; font-weight:800; font-family:monospace; color:#f87171;">{len(alerts)} SKUs</div>
            <div style="font-size:10px; color:#fca5a5;">{critical_count} Critical / {warning_count} Warning</div>
        </div>
        <div style="background:#131f38; border:1px solid #1f3154; border-radius:8px; padding:12px;">
            <div style="font-size:10px; font-weight:700; color:#94a3b8; text-transform:uppercase;">Daily Revenue Risk</div>
            <div style="font-size:22px; font-weight:800; font-family:monospace; color:#fbbf24;">${total_rev_at_risk:,.0f}</div>
            <div style="font-size:10px; color:#fde68a;">Wholesale Exposure</div>
        </div>
        <div style="background:#131f38; border:1px solid #1f3154; border-radius:8px; padding:12px;">
            <div style="font-size:10px; font-weight:700; color:#94a3b8; text-transform:uppercase;">Rebalance Units</div>
            <div style="font-size:22px; font-weight:800; font-family:monospace; color:#38bdf8;">{total_cases_needed:,}</div>
            <div style="font-size:10px; color:#bae6fd;">Cases to 7.0 DOS</div>
        </div>
    </div>

    <!-- Triage Table -->
    <table style="width:100%; border-collapse:collapse; font-size:12px; text-align:left;">
        <thead>
            <tr style="background:#0a0f1d; color:#94a3b8; font-size:10px; text-transform:uppercase;">
                <th style="padding:8px 12px;">#</th>
                <th style="padding:8px 12px;">Status</th>
                <th style="padding:8px 12px;">Product / Location</th>
                <th style="padding:8px 12px;">DOS (Days)</th>
                <th style="padding:8px 12px;">Daily Exposure</th>
            </tr>
        </thead>
        <tbody>
            {rows_joined}
        </tbody>
    </table>
</div>
"""


def render_mitigation_matrix_a2ui(matrix: Dict[str, Any], alert: Dict[str, Any]) -> str:
    """Renders the A2UI.MitigationMatrix visual widget for a specific exception."""
    opt_cards = []
    for opt in matrix["options"]:
        is_rec = opt["option_id"] == matrix["recommended_option_id"]
        rec_border = "border:2px solid #38bdf8; box-shadow:0 0 15px rgba(56,189,248,0.2);" if is_rec else "border:1px solid #1f3154;"
        rec_tag = '<span style="background:linear-gradient(135deg, #005cb9, #38bdf8); color:#ffffff; font-size:9px; font-weight:800; padding:2px 8px; border-radius:10px; text-transform:uppercase; margin-left:6px;">★ RECOMMENDED</span>' if is_rec else ""
        btn_style = "background:#00875a; color:#ffffff;" if is_rec else "background:#1e293b; color:#94a3b8;"

        cost_str = f"${opt['execution_cost_usd']:,.2f}" if opt['execution_cost_usd'] > 0 else "$0.00 (Zero Freight)"

        opt_cards.append(f"""
        <div style="background:#0e1424; {rec_border} border-radius:10px; padding:14px; display:flex; flex-direction:column; justify-content:space-between;">
            <div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="background:#1e293b; color:#94a3b8; font-family:monospace; font-size:11px; font-weight:700; padding:2px 6px; border-radius:4px;">{opt['option_type']}</span>
                    {rec_tag}
                </div>
                <div style="font-size:13px; font-weight:700; color:#ffffff; margin-bottom:6px;">{opt['title']}</div>
                <div style="font-size:11px; color:#94a3b8; line-height:1.4; margin-bottom:12px;">{opt['description']}</div>
                
                <div style="font-size:11px; border-top:1px solid #1f3154; padding-top:8px; line-height:1.6;">
                    <div style="display:flex; justify-content:space-between;"><span style="color:#94a3b8;">Freight Cost:</span> <strong style="font-family:monospace; color:{'#fbbf24' if opt['execution_cost_usd'] > 0 else '#34d399'};">{cost_str}</strong></div>
                    <div style="display:flex; justify-content:space-between;"><span style="color:#94a3b8;">Lead Time:</span> <strong style="font-family:monospace; color:#ffffff;">{opt['recovery_lead_time_hours']:.1f} hrs</strong></div>
                    <div style="display:flex; justify-content:space-between;"><span style="color:#94a3b8;">Restored DOS:</span> <strong style="font-family:monospace; color:#38bdf8;">{opt['post_mitigation_dos']:.1f} Days</strong></div>
                    <div style="display:flex; justify-content:space-between;"><span style="color:#94a3b8;">Protected Rev:</span> <strong style="font-family:monospace; color:#34d399;">${opt['protected_revenue_usd']:,.2f}</strong></div>
                    <div style="display:flex; justify-content:space-between;"><span style="color:#94a3b8;">Fill Rate:</span> <strong style="font-family:monospace; color:#ffffff;">{opt['fill_rate_projection_pct']:.1f}%</strong></div>
                </div>
            </div>
            
            <div style="margin-top:14px;">
                <div style="background:#131f38; border:1px solid #1f3154; border-radius:6px; padding:6px; text-align:center; font-size:11px; font-family:monospace; color:#38bdf8; font-weight:bold;">
                    SAP Action: {opt['sap_transaction_code']}
                </div>
            </div>
        </div>
        """)

    cards_joined = "".join(opt_cards)

    return f"""
<div class="a2ui-card" style="background:#0d1527; border:1px solid #1f3154; border-radius:12px; padding:20px; font-family:'Inter',system-ui,sans-serif; color:#f8fafc; max-width:820px; box-shadow:0 10px 30px rgba(0,0,0,0.5);">
    <div style="border-bottom:1px solid #1f3154; padding-bottom:12px; margin-bottom:14px;">
        <div style="font-size:15px; font-weight:800; color:#ffffff;">Mitigation Trade-Off Matrix: {alert.get('sku_name', matrix['sku_id'])}</div>
        <div style="font-size:11px; color:#94a3b8; margin-top:2px;">
            Facility: <strong>{alert.get('dc_name', matrix['dc_id'])}</strong> | Current DOS: <strong style="color:#f87171;">{alert.get('current_dos', 0):.1f}d</strong> (Target: 7.0d) | Daily Exposure: <strong>${alert.get('daily_revenue_at_risk', 0):,.2f}</strong>
        </div>
    </div>

    <div style="background:#131f38; border-left:3px solid #38bdf8; padding:10px 14px; border-radius:6px; font-size:11px; line-height:1.5; color:#cbd5e1; margin-bottom:16px;">
        <strong>AI Agent Recommendation Rationale:</strong> {matrix['recommendation_rationale']}
    </div>

    <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:12px;">
        {cards_joined}
    </div>
</div>
"""


def render_sap_confirmation_a2ui(result: Dict[str, Any]) -> str:
    """Renders the A2UI.SAPConfirmationToast badge for executed ERP transactions."""
    return f"""
<div class="a2ui-card" style="background:#0b1912; border:1px solid #00875a; border-left:5px solid #34d399; border-radius:10px; padding:16px 20px; font-family:'Inter',system-ui,sans-serif; color:#f8fafc; max-width:650px; box-shadow:0 8px 24px rgba(0,135,90,0.25);">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size:18px;">✅</span>
            <span style="font-size:14px; font-weight:800; color:#ffffff;">SAP ERP / IBP Transaction Posted</span>
        </div>
        <span style="background:rgba(52,211,153,0.2); color:#34d399; border:1px solid rgba(52,211,153,0.4); padding:2px 8px; border-radius:4px; font-size:11px; font-family:monospace; font-weight:700;">STATUS: POSTED</span>
    </div>

    <div style="background:#06110b; border:1px solid #163824; border-radius:6px; padding:10px 14px; font-family:monospace; font-size:12px; margin-bottom:10px; line-height:1.6;">
        <div><strong style="color:#94a3b8;">SAP Document Number:</strong> <span style="color:#38bdf8; font-weight:700;">#{result.get('sap_document_number', 'N/A')}</span></div>
        <div><strong style="color:#94a3b8;">Transaction Code:</strong> <span>{result.get('transaction_code', 'STO-UB-01')}</span></div>
        <div><strong style="color:#94a3b8;">Material (SKU):</strong> <span>{result.get('sku_id', 'N/A')}</span></div>
        <div><strong style="color:#94a3b8;">Quantity Rebalanced:</strong> <span style="color:#34d399; font-weight:700;">{result.get('quantity_cases', 0):,} Cases</span></div>
        <div><strong style="color:#94a3b8;">Origin ➔ Destination:</strong> <span>{result.get('source_plant', 'N/A')} ➔ {result.get('destination_plant', 'N/A')}</span></div>
    </div>

    <div style="font-size:11px; color:#94a3b8;">
        <strong>Audit Trail:</strong> {result.get('audit_message', 'Authorized by Senior Supply Chain Planner via HITL session.')}
    </div>
</div>
"""
