# PepsiCo Supply Chain Planner — Google Enterprise Agent Platform (GEAP) Package

This package allows publishing the **PepsiCo Autonomous Supply Chain Agent** directly to **Gemini Enterprise / Google Enterprise Agent Platform (GEAP)** with rich **A2UI (Agent-to-User-Interface)** visual components.

---

## 📦 Package Contents

```
geap_agent/
├── a2ui_components.py      # A2UI Visual Card renderers (Triage Scorecard, 3-Way Matrix, SAP Confirmation)
├── agent_service.py        # FastAPI / ADK Tool Microservice
├── openapi.yaml            # OpenAPI 3.0 Tool specification for Gemini Enterprise import
├── geap_manifest.yaml      # Agent Builder configuration manifest
├── Dockerfile              # Container definition for Cloud Run deployment
├── requirements.txt        # Isolated service dependencies
├── deploy_to_cloud_run.sh  # 1-command deployment script to Google Cloud Run
└── test_geap_local.py      # Local verification and A2UI card test runner
```

---

## 🎨 A2UI (Agent-to-UI) Visual Elements

When Gemini Enterprise executes the agent's tools, the backend returns both machine-readable JSON (for LLM reasoning) and styled **A2UI Visual Cards** rendered in the chat stream:

1. **`A2UI.TriageScorecard`:** Visual KPI counters, color-coded Days of Supply ($\text{DOS}$) progress bars, and prioritized exception table.
2. **`A2UI.MitigationMatrix`:** Side-by-side cards comparing **Option A (Inter-DC STO)**, **Option B (Safety Rebalance)**, and **Option C (Order Deferral)** with freight costs, recovery hours, and SAP action tags.
3. **`A2UI.SAPConfirmationToast`:** Live confirmation badge displaying confirmed purchase order numbers (`#4500xxxxxx`) and audit timestamps.

---

## 🚀 How to Publish to Gemini Enterprise (GEAP)

### Step 1: Deploy the Tool Service to Google Cloud Run
Run the deployment script:
```bash
./geap_agent/deploy_to_cloud_run.sh
```
*Outputs your live Cloud Run Service URL: `https://pepsico-sc-agent-uc.a.run.app`*

### Step 2: Register Tools in Gemini Enterprise
1. In the Google Cloud Console, navigate to **Gemini Enterprise > Agent Builder > Tools**.
2. Click **Create Tool** > Select **OpenAPI**.
3. Provide tool name: `PepsiCo_Supply_Chain_Tools`.
4. Paste the URL of your OpenAPI spec: `https://<YOUR_CLOUD_RUN_URL>/openapi.json` (or upload `geap_agent/openapi.yaml`).

### Step 3: Create & Publish the Agent in Gemini Enterprise
1. In **Agent Builder > Agents**, click **Create Agent**.
2. Set Display Name: `PepsiCo Supply Chain Planner`.
3. Paste System Instructions from `geap_agent/geap_manifest.yaml`.
4. Link the `PepsiCo_Supply_Chain_Tools` toolset.
5. Click **Publish** to make it available to users in Google Agentspace / Gemini Enterprise!

---

## 🧪 Local Testing & Verification

To verify tool execution and A2UI card rendering locally before publishing:
```bash
python3 geap_agent/test_geap_local.py
```
