# PepsiCo Autonomous Supply Chain Exception Triage & Replenishment Agent (ADK Suite)

An enterprise-grade autonomous supply chain planning agent designed for **PepsiCo Consumer Packaged Goods (CPG) Operations & Logistics**. 

The agent operates in accordance with **SOP-SC-042** (Daily Supply Chain Exception Triage & Replenishment Execution) and technical specification **MOP-SC-042** (Technical Architecture for Supply Chain Agentic Exception Triage).

---

## 📋 Executive Overview & SOP Alignment

The agent automates the daily morning operational cycle across regional distribution hubs:

```
+-----------------------------------------------------------------------------------------------+
|                                    SOP-SC-042 DAILY WORKFLOW                                  |
+-----------------------------------------------------------------------------------------------+
|  06:00 - 06:30          06:30 - 07:00              07:00 - 07:30           07:30 - 08:00      |
|  Step 1: Ingestion  ->  Step 2: Risk Ranking   ->  Step 3: Simulation  ->  Step 4: Execution  |
|  Query MARC/MARD/VBBE   Compute DOS & Deficits     Model Options A, B, C   HITL Approval & SAP|
+-----------------------------------------------------------------------------------------------+
```

### 1. Daily Operational Schedule
- **Step 1: Automated Morning Health Check (06:00 - 06:30):** Queries BigQuery/SAP ERP semantic data layers (`MARC` plant data, `MARD` stock balances, `VBBE` sales requirements) across regional hubs.
- **Step 2: Exception Review & Risk Ranking (06:30 - 07:00):** Calculates Days of Supply ($\text{DOS}$) and prioritizes critical exceptions weighted by **Daily Revenue at Risk $\times$ Tier-1 Key Account SLA Severity (Walmart, Target, Kroger OTIF)**.
- **Step 3: Mitigation Option Modeling (07:00 - 07:30):** Simulates quantitative trade-off matrices for 3 mitigation paths:
  - **Option A:** Expedite Stock Transfer Order (STO) from an adjacent regional DC with surplus stock ($\text{DOS} \ge 14.0$).
  - **Option B:** Dynamic Safety Stock Buffer Reallocation based on 14-day rolling demand trends.
  - **Option C:** Defer Non-Critical Retail Replenishment (Order Throttling for Tier-2/3) to protect Tier-1 fill rates pending plant production.
- **Step 4: HITL Approval & SAP Execution (07:30 - 08:00):** Human planner validates recommendations, authorizes transactions, and posts live document updates back to SAP ERP/IBP.

---

## 🏗️ Architecture & Technical Specifications (MOP-SC-042)

```
pepsico_sc_agent/
├── config/
│   └── settings.py          # DC network topology, distance matrix, freight rates, SLA tiers
├── data/
│   ├── database.py          # SQLite / BigQuery semantic views (MARC, MARD, VBBE, Audit log)
│   └── seed_data.py         # Realistic PepsiCo portfolio (Frito-Lay, Pepsi, Gatorade, Quaker)
├── models/
│   ├── schemas.py           # Typed Pydantic/Dataclass schemas for SKUs, Alerts, Mitigations
│   └── calculations.py      # Algorithmic DOS, Risk Index, and linehaul transit formulas
├── agent/
│   ├── prompts.py           # System instructions and executive synthesis prompt templates
│   ├── tools.py             # ADK Agent Tools (query, rank, simulate, post_sap)
│   └── core_agent.py        # Hybrid autonomous agent (Gemini GenAI SDK + deterministic fallback)
├── cli/
│   ├── interactive_runner.py# Human-in-the-Loop CLI with rich terminal prompts
│   └── generate_brief.py    # Automated Markdown Daily Brief generator
├── tests/
│   ├── test_calculations.py # Math and algorithmic test suite
│   ├── test_tools.py        # ADK tools test suite
│   └── test_workflow.py     # End-to-end SOP-SC-042 integration test
└── main.py                  # Unified CLI entrypoint
```

---

## 🧮 Algorithmic Formulas

### Days of Supply (DOS)
$$\text{DOS} = \frac{\text{Current On-Hand Inventory (Cases)}}{\text{Average Daily Sales Run Rate (Cases/Day)}}$$

### SLA-Weighted Risk Score
$$\text{Risk Score} = \text{DOS Deficit Days} \times \left(\sum_{i \in \text{Tiers}} \text{Share}_i \times \text{Weight}_i\right) \times \left(\frac{\text{Daily Revenue}}{1000}\right)$$
* Where Tier-1 Key Accounts (Walmart, Target, Kroger) carry a $2.5\times$ multiplier for OTIF penalty protection.

### Freight Linehaul Cost Model
$$\text{Linehaul Cost} = (\text{Distance (Miles)} \times \text{Expedited Rate (\$4.20/mile)} \times \text{Truckloads}) + (\text{Pallets} \times \text{Handling Fee (\$15.00)})$$

---

## 🚀 Quickstart & Usage

### 1. Launch Interactive ADK Web Dashboard (localhost:8080)
```bash
python3 pepsico_sc_agent/web_server.py --port 8080
```
*Opens the rich interactive PepsiCo Supply Chain Planning Operations Hub in your browser.*

### 2. Run Autonomous Morning Health Check & Generate Executive Brief
```bash
python3 pepsico_sc_agent/main.py --generate-brief
```
*Outputs a publication-ready report `Daily_Supply_Chain_Exception_Brief_YYYYMMDD.md`.*

### 3. Launch Interactive Human-in-the-Loop (HITL) Planner CLI
```bash
python3 pepsico_sc_agent/main.py --interactive
```

### 4. Run Autonomous Auto-Triage with Automatic Recommended Execution
```bash
python3 pepsico_sc_agent/main.py --auto-triage
```

### 5. Inspect SAP ERP / IBP Transaction Audit Trail
```bash
python3 pepsico_sc_agent/main.py --show-audit
```

### 6. Run Automated Test Suite
```bash
python3 -m unittest discover -s pepsico_sc_agent/tests -p "test_*.py" -v
```

---

## 🏢 Synthetic Portfolio & DC Network

### Products
- **Frito-Lay**: Lay's Classic 8oz Party Size (`SKU-FL-101`), Doritos Nacho Cheese 9.25oz (`SKU-FL-102`), Cheetos Crunchy 8.5oz (`SKU-FL-103`)
- **Pepsi Carbonated Beverages**: Pepsi Cola 12-Pack Cans (`SKU-PB-201`), bubly Sparkling Water 8-Pack (`SKU-PB-202`), Mountain Dew 20oz (`SKU-PB-203`)
- **Gatorade Sports Hydration**: Gatorade Cool Blue 28oz (`SKU-GT-301`), Gatorade Zero 20oz (`SKU-GT-302`)
- **Quaker Foods**: Quaker Quick Oats 42oz (`SKU-QK-401`), Quaker Chewy Bars (`SKU-QK-402`)

### Regional Hubs
- `DC-DAL-01`: Dallas Regional Distribution Hub (TX) - Primary Manufacturing Plant & Surplus Buffer
- `DC-CHI-02`: Chicago Central Distribution Center (IL)
- `DC-ATL-03`: Atlanta Metro Distribution Center (GA) - High Retail Velocity Corridors
- `DC-NE-04`: Northeast Regional Hub / Breinigsville (PA)
