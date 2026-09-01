"""
Google Enterprise Agent Platform (GEAP) ADK Microservice
Serves OpenAPI-compliant tool endpoints with rich A2UI visual card payloads
for registration in Gemini Enterprise / Google Agentspace.
"""

import os
import sys
import json
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pepsico_sc_agent.agent.core_agent import SupplyChainPlannerAgent
from pepsico_sc_agent.agent.tools import simulate_mitigation_scenarios
from pepsico_sc_agent.data.seed_data import populate_seed_data
from pepsico_sc_agent.models.schemas import SeverityLevel
from geap_agent.a2ui_components import (
    render_triage_scorecard_a2ui,
    render_mitigation_matrix_a2ui,
    render_sap_confirmation_a2ui
)

# Initialize seed database on startup
populate_seed_data()


# ----------------------------------------------------------------------
# Core GEAP Tool Handlers (Portable across FastAPI and Standard HTTP)
# ----------------------------------------------------------------------

def handle_morning_triage() -> Dict[str, Any]:
    """
    GEAP Tool: Executes 06:00 Automated Morning Health Check.
    Queries MARC, MARD, and VBBE tables to detect and rank inventory exceptions.
    Returns structured data + A2UI.TriageScorecard visual card.
    """
    agent = SupplyChainPlannerAgent()
    alerts = agent.run_morning_health_check()
    matrices = agent.evaluate_all_exceptions(alerts)
    commentary = agent.generate_executive_commentary(alerts, matrices)

    critical_count = sum(1 for a in alerts if a.severity == SeverityLevel.CRITICAL)
    warning_count = sum(1 for a in alerts if a.severity == SeverityLevel.WARNING)
    total_rev = sum(a.daily_revenue_at_risk for a in alerts)
    total_cases = sum(a.units_needed_for_target_dos for a in alerts)

    alerts_dict = [a.to_dict() for a in alerts]
    
    # Generate A2UI visual card block
    a2ui_html = render_triage_scorecard_a2ui(
        alerts=alerts_dict,
        critical_count=critical_count,
        warning_count=warning_count,
        total_rev_at_risk=total_rev,
        total_cases_needed=total_cases
    )

    return {
        "tool_name": "morning_triage_health_check",
        "status": "SUCCESS",
        "summary": f"Identified {len(alerts)} SKU exceptions with ${total_rev:,.2f}/day revenue exposure.",
        "executive_commentary": commentary,
        "kpis": {
            "total_exceptions": len(alerts),
            "critical_exceptions": critical_count,
            "warning_exceptions": warning_count,
            "daily_revenue_at_risk_usd": total_rev,
            "cases_needed_for_target_dos": total_cases
        },
        "alerts": alerts_dict,
        "a2ui_card_html": a2ui_html
    }


def handle_evaluate_mitigations(sku_id: str, dc_id: str) -> Dict[str, Any]:
    """
    GEAP Tool: Runs 3-Way Quantitative Mitigation Simulation (Options A, B, C).
    Models freight costs, lead times, protected revenue, and fill rates.
    Returns structured data + A2UI.MitigationMatrix visual card.
    """
    agent = SupplyChainPlannerAgent()
    matrix = simulate_mitigation_scenarios(dc_id=dc_id, sku_id=sku_id)
    alerts = agent.run_morning_health_check()
    alert = next((a.to_dict() for a in alerts if a.sku_id == sku_id and a.dc_id == dc_id), {})

    matrix_dict = matrix.to_dict()
    a2ui_html = render_mitigation_matrix_a2ui(matrix=matrix_dict, alert=alert)

    return {
        "tool_name": "evaluate_mitigation_options",
        "status": "SUCCESS",
        "sku_id": sku_id,
        "dc_id": dc_id,
        "recommended_option_id": matrix.recommended_option_id,
        "recommendation_rationale": matrix.recommendation_rationale,
        "options": matrix_dict["options"],
        "a2ui_card_html": a2ui_html
    }


def handle_execute_sap(sku_id: str, dc_id: str, option_id: str, planner_note: str = "Authorized via Gemini Enterprise HITL Session") -> Dict[str, Any]:
    """
    GEAP Tool: Executes approved mitigation option back to SAP ERP/IBP.
    Posts Stock Transfer Orders (STOs) and updates inventory balances with full audit logging.
    Returns structured data + A2UI.SAPConfirmationToast badge.
    """
    agent = SupplyChainPlannerAgent()
    matrix = simulate_mitigation_scenarios(dc_id=dc_id, sku_id=sku_id)
    result = agent.execute_planner_selection(
        matrix=matrix,
        selected_option_id=option_id,
        planner_note=planner_note
    )

    a2ui_html = render_sap_confirmation_a2ui(result)

    return {
        "tool_name": "execute_sap_replenishment",
        "status": "SUCCESS",
        "sap_document_number": result["sap_document_number"],
        "transaction_code": result["transaction_code"],
        "sku_id": result["sku_id"],
        "quantity_cases": result["quantity_cases"],
        "source_plant": result["source_plant"],
        "destination_plant": result["destination_plant"],
        "audit_message": result["audit_message"],
        "a2ui_card_html": a2ui_html
    }


# ----------------------------------------------------------------------
# Optional FastAPI Integration (Used when FastAPI is installed in Container)
# ----------------------------------------------------------------------
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field

    class MitigationRequest(BaseModel):
        sku_id: str = Field(..., description="Target Material ID (e.g. SKU-FL-101)")
        dc_id: str = Field(..., description="Target Plant ID (e.g. DC-ATL-03)")

    class ExecutionRequest(BaseModel):
        sku_id: str = Field(..., description="Material ID")
        dc_id: str = Field(..., description="Destination Plant ID")
        option_id: str = Field(..., description="Approved Option ID")
        planner_note: Optional[str] = Field(default="Authorized via Gemini Enterprise HITL Session")

    app = FastAPI(
        title="PepsiCo Supply Chain Planner GEAP Agent",
        description="Google Enterprise Agent Platform (GEAP) Tool Service with A2UI elements (SOP-SC-042).",
        version="1.0.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health_check():
        return {"status": "HEALTHY", "service": "pepsico-sc-geap-agent"}

    @app.post("/tools/morning-triage")
    def tool_morning_triage():
        return handle_morning_triage()

    @app.post("/tools/evaluate-mitigations")
    def tool_evaluate_mitigations(req: MitigationRequest):
        return handle_evaluate_mitigations(req.sku_id, req.dc_id)

    @app.post("/tools/execute-sap")
    def tool_execute_sap(req: ExecutionRequest):
        return handle_execute_sap(req.sku_id, req.dc_id, req.option_id, req.planner_note)

except ImportError:
    app = None


# ----------------------------------------------------------------------
# Standard Library HTTP Server Fallback (Runs without external packages)
# ----------------------------------------------------------------------
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

class StandaloneGEAPHandler(BaseHTTPRequestHandler):

    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._set_headers(200)
            self.wfile.write(json.dumps({"status": "HEALTHY", "service": "pepsico-sc-geap-agent"}).encode("utf-8"))
        else:
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "service": "PepsiCo GEAP Agent Service",
                "status": "ONLINE",
                "endpoints": ["/tools/morning-triage", "/tools/evaluate-mitigations", "/tools/execute-sap"]
            }).encode("utf-8"))

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            body = json.loads(body_data.decode("utf-8"))
        except Exception:
            body = {}

        if parsed.path == "/tools/morning-triage":
            res = handle_morning_triage()
            self._set_headers(200)
            self.wfile.write(json.dumps(res).encode("utf-8"))

        elif parsed.path == "/tools/evaluate-mitigations":
            sku_id = body.get("sku_id", "SKU-FL-101")
            dc_id = body.get("dc_id", "DC-ATL-03")
            res = handle_evaluate_mitigations(sku_id, dc_id)
            self._set_headers(200)
            self.wfile.write(json.dumps(res).encode("utf-8"))

        elif parsed.path == "/tools/execute-sap":
            sku_id = body.get("sku_id", "SKU-FL-101")
            dc_id = body.get("dc_id", "DC-ATL-03")
            option_id = body.get("option_id", "OPT-A-STO")
            note = body.get("planner_note", "Authorized via GEAP")
            res = handle_execute_sap(sku_id, dc_id, option_id, note)
            self._set_headers(200)
            self.wfile.write(json.dumps(res).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))


def run_standalone(port: int = 8090):
    server = HTTPServer(("", port), StandaloneGEAPHandler)
    print(f"GEAP Agent Standalone Service running on http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8090))
    if app:
        import uvicorn
        uvicorn.run("geap_agent.agent_service:app", host="0.0.0.0", port=port)
    else:
        run_standalone(port=port)
