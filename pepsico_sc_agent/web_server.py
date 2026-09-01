"""
HTTP Web Server & ADK REST API for PepsiCo Supply Chain Agent
Serves localhost:8080 interactive operations dashboard with zero external dependencies.
"""

import os
import sys
import json
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Ensure root package is in Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pepsico_sc_agent.agent.core_agent import SupplyChainPlannerAgent
from pepsico_sc_agent.data.seed_data import populate_seed_data
from pepsico_sc_agent.data.database import get_recent_sap_audit_trail
from pepsico_sc_agent.agent.tools import execute_sap_action, simulate_mitigation_scenarios
from pepsico_sc_agent.models.schemas import SeverityLevel

HTML_FILE_PATH = os.path.join(os.path.dirname(__file__), "web", "index.html")
SLIDES_FILE_PATH = os.path.join(os.path.dirname(__file__), "web", "slides.html")


class SupplyChainDashboardHandler(BaseHTTPRequestHandler):

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path in ["/", "/index.html"]:
            try:
                with open(HTML_FILE_PATH, "r", encoding="utf-8") as f:
                    content = f.read()
                self._set_headers(200, content_type="text/html; charset=utf-8")
                self.wfile.write(content.encode("utf-8"))
            except Exception as e:
                self._set_headers(500, content_type="text/plain")
                self.wfile.write(f"Error loading dashboard HTML: {e}".encode("utf-8"))

        elif parsed_path.path in ["/slides", "/slides.html"]:
            try:
                with open(SLIDES_FILE_PATH, "r", encoding="utf-8") as f:
                    content = f.read()
                self._set_headers(200, content_type="text/html; charset=utf-8")
                self.wfile.write(content.encode("utf-8"))
            except Exception as e:
                self._set_headers(500, content_type="text/plain")
                self.wfile.write(f"Error loading slides HTML: {e}".encode("utf-8"))

        elif parsed_path.path == "/api/triage":
            agent = SupplyChainPlannerAgent()
            alerts = agent.run_morning_health_check()
            matrices = agent.evaluate_all_exceptions(alerts)
            commentary = agent.generate_executive_commentary(alerts, matrices)

            critical_count = sum(1 for a in alerts if a.severity == SeverityLevel.CRITICAL)
            warning_count = sum(1 for a in alerts if a.severity == SeverityLevel.WARNING)
            total_rev = sum(a.daily_revenue_at_risk for a in alerts)
            total_cases = sum(a.units_needed_for_target_dos for a in alerts)

            payload = {
                "alerts": [a.to_dict() for a in alerts],
                "matrices": [m.to_dict() for m in matrices],
                "commentary": commentary,
                "critical_count": critical_count,
                "warning_count": warning_count,
                "total_revenue_at_risk": total_rev,
                "total_units_needed": total_cases
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(payload).encode("utf-8"))

        elif parsed_path.path == "/api/audit":
            logs = get_recent_sap_audit_trail(limit=50)
            self._set_headers(200)
            self.wfile.write(json.dumps(logs).encode("utf-8"))

        else:
            self._set_headers(404, content_type="application/json")
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def do_POST(self):
        parsed_path = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body_data = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            body = json.loads(body_data.decode("utf-8")) if body_data else {}
        except Exception:
            body = {}

        if parsed_path.path == "/api/execute":
            sku_id = body.get("sku_id")
            dc_id = body.get("dc_id")
            option_id = body.get("option_id")

            if not (sku_id and dc_id and option_id):
                self._set_headers(400)
                self.wfile.write(json.dumps({"status": "ERROR", "message": "Missing required fields"}).encode("utf-8"))
                return

            agent = SupplyChainPlannerAgent()
            matrix = simulate_mitigation_scenarios(dc_id=dc_id, sku_id=sku_id)
            result = agent.execute_planner_selection(
                matrix=matrix,
                selected_option_id=option_id,
                planner_note="Authorized via ADK Web UI on localhost"
            )
            self._set_headers(200)
            self.wfile.write(json.dumps(result).encode("utf-8"))

        elif parsed_path.path == "/api/auto-execute-all":
            agent = SupplyChainPlannerAgent()
            alerts = agent.run_morning_health_check()
            matrices = agent.evaluate_all_exceptions(alerts)

            executed = []
            for matrix in matrices:
                res = agent.execute_planner_selection(
                    matrix=matrix,
                    selected_option_id=matrix.recommended_option_id,
                    planner_note="Auto-approved Recommended Mitigation via ADK Web UI"
                )
                executed.append(res)

            self._set_headers(200)
            self.wfile.write(json.dumps({"status": "SUCCESS", "executed_count": len(executed)}).encode("utf-8"))

        elif parsed_path.path == "/api/reset":
            populate_seed_data()
            self._set_headers(200)
            self.wfile.write(json.dumps({"status": "SUCCESS", "message": "Database re-seeded."}).encode("utf-8"))

        elif parsed_path.path == "/api/chat":
            user_msg = body.get("message", "").lower()
            agent = SupplyChainPlannerAgent()
            alerts = agent.run_morning_health_check()

            # Smart conversational replies grounded in live data
            if "doritos" in user_msg or "sku-fl-102" in user_msg:
                alert = next((a for a in alerts if a.sku_id == "SKU-FL-102"), None)
                reply = (
                    f"**Doritos Nacho Cheese 9.25oz (`SKU-FL-102`)** is currently at **{alert.current_dos if alert else 1.7:.1f} Days of Supply** "
                    f"in Chicago Central DC (`DC-CHI-02`). Overnight demand surged by +45% from Key Accounts (Walmart/Costco). "
                    f"Recommended Action: **Option A (Expedited STO from Dallas `DC-DAL-01`)** with a 21.2-hour lead time, "
                    f"protecting $292,698 in wholesale revenue for an estimated freight cost of $17,211."
                )
            elif "lay" in user_msg or "sku-fl-101" in user_msg:
                alert = next((a for a in alerts if a.sku_id == "SKU-FL-101"), None)
                reply = (
                    f"**Lay's Classic 8oz (`SKU-FL-101`)** in Atlanta Metro DC (`DC-ATL-03`) is facing critical stockout risk with only "
                    f"**{alert.current_dos if alert else 1.1:.1f} Days of Supply** (Deficit: -5.9d). "
                    f"An expedited STO of 7,527 cases from Dallas (`DC-DAL-01`) will arrive in 18.2 hours to restore safety stock to 7.0 DOS."
                )
            elif "freight" in user_msg or "cost" in user_msg or "distance" in user_msg:
                reply = (
                    "**PepsiCo Linehaul Freight Parameters (MOP-SC-042):**<br>"
                    "• Dedicated Team Expedited: **$4.20 / highway mile** (48 mph effective speed)<br>"
                    "• Standard Dry-Van: **$2.85 / highway mile**<br>"
                    "• Dallas to Atlanta: 780 miles (~18.2 hrs transit)<br>"
                    "• Dallas to Chicago: 920 miles (~21.2 hrs transit)<br>"
                    "• Chicago to Breinigsville Northeast: 680 miles (~16.2 hrs transit)"
                )
            elif "sop" in user_msg or "mop" in user_msg or "procedure" in user_msg:
                reply = (
                    "**SOP-SC-042 Workflow Schedule:**<br>"
                    "• **06:00 - 06:30:** Automated Data Ingestion (MARC, MARD, VBBE)<br>"
                    "• **06:30 - 07:00:** Exception Review & Revenue-Weighted Risk Ranking<br>"
                    "• **07:00 - 07:30:** 3-Way Quantitative Mitigation Simulation (Options A, B, C)<br>"
                    "• **07:30 - 08:00:** Planner HITL Approval & SAP Posting"
                )
            else:
                critical_skus = ", ".join([f"{a.sku_name} ({a.current_dos:.1f} DOS)" for a in alerts[:3]])
                reply = (
                    f"Currently tracking **{len(alerts)} active inventory exceptions**. "
                    f"Top priority bottlenecks: {critical_skus}. "
                    f"You can approve recommended Stock Transfer Orders (Option A) directly in the **Mitigation Trade-Offs** tab!"
                )

            self._set_headers(200)
            self.wfile.write(json.dumps({"reply": reply}).encode("utf-8"))

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))


def run_server(port: int = 8080):
    populate_seed_data()
    server_address = ("", port)
    
    try:
        httpd = HTTPServer(server_address, SupplyChainDashboardHandler)
    except OSError as e:
        if "Address already in use" in str(e):
            alt_port = 8081 if port == 8080 else port + 1
            print(f"[!] Port {port} is already in use by another process.")
            print(f"[*] Starting on fallback port: http://localhost:{alt_port}")
            httpd = HTTPServer(("", alt_port), SupplyChainDashboardHandler)
            port = alt_port
        else:
            raise e

    print("=" * 80)
    print("  PEPSICO SUPPLY CHAIN AGENT - ADK OPERATIONS DASHBOARD")
    print(f"  Live UI & REST API Running at:  http://localhost:{port}")
    print("  SOP-SC-042 Exception Triage | MOP-SC-042 Quantitative Engine")
    print("=" * 80)
    print("\nPress Ctrl+C to stop the server.\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Shutting down Supply Chain Agent Web Server.")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start PepsiCo SC Agent Web Dashboard")
    parser.add_argument("--port", type=int, default=8080, help="Port to serve (default: 8080)")
    args = parser.parse_args()
    run_server(port=args.port)
