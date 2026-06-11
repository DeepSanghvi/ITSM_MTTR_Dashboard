# 🔔 Incident MTTR Dashboard

A production-ready Streamlit dashboard that connects to the **ServiceNow Table API** to visualise incident management KPIs — MTTR, MTTA, SLA breach rates, team performance, and recurring CI analysis.

Built to demonstrate end-to-end ITSM observability skills: REST API integration, data transformation with Pandas, and interactive visualisation with Plotly.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red)
![ServiceNow](https://img.shields.io/badge/ServiceNow-Table_API-brightgreen)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## 📊 Dashboard features

| Section | What it shows |
|---|---|
| **KPI cards** | MTTR, MTTA, SLA breach rate, open incident count |
| **Trends tab** | Weekly MTTR trend line + incident volume bar chart |
| **Priorities tab** | Avg vs median MTTR per priority · volume by category (donut) |
| **Teams tab** | Assignment group MTTR ranking (fastest → slowest) |
| **SLA & CIs tab** | SLA breach rate by priority · top recurring CIs for Problem Management |
| **Raw data tab** | Searchable, filterable incident log with CSV export |

---

## 🚀 Quick start

### 1. Clone & install

```bash
git clone https://github.com/DeepSanghvi/ITSM_MTTR_Dashboard
cd MTTR_Dashboard
pip install -r requirements.txt
```

### 2. Run in demo mode (no ServiceNow needed)

```bash
streamlit run app.py
```

The app generates 300 realistic mock incidents automatically. No credentials required.

### 3. Connect to a real ServiceNow instance

```bash
cp .env.example .env
```

Edit `.env`:

```
SNOW_INSTANCE=your-instance.service-now.com
SNOW_USERNAME=your_username
SNOW_PASSWORD=your_password
DATA_MODE=live
```

Then re-run `streamlit run app.py` and switch the sidebar toggle to **Live ServiceNow**.

---

## 🏗️ Project structure

```
mttr-dashboard/
├── app.py                    # Streamlit entry point — layout, tabs, filters
├── utils/
│   ├── snow_client.py        # ServiceNow REST API client (paginated)
│   ├── metrics.py            # MTTR, MTTA, SLA, breach calculations
│   └── charts.py             # Plotly chart builders
├── data/
│   └── mock_generator.py     # Realistic synthetic incident data
├── requirements.txt
└── .env.example
```

---

## 🔌 ServiceNow API details

The dashboard uses the **[Table API](https://developer.servicenow.com/dev.do#!/reference/api/tokyo/rest/c_TableAPI)** (`/api/now/table/incident`) with:

- Basic authentication (swap `HTTPBasicAuth` for OAuth in `snow_client.py` if your instance requires it)
- Automatic pagination (`sysparm_offset` loop)
- `sysparm_display_value=all` to resolve reference fields (assignment group, CI) in one request
- Configurable look-back window (default 90 days)

**Required ServiceNow role:** `itil` (read access to the `incident` table)

---

## 📐 SLA thresholds

Default thresholds used for breach calculation (customise in `data/mock_generator.py`):

| Priority | SLA threshold |
|---|---|
| 1 - Critical | 4 hours |
| 2 - High | 8 hours |
| 3 - Moderate | 24 hours |
| 4 - Low | 72 hours |

---

## 🛠️ Extending this project

- **Add OAuth**: replace `HTTPBasicAuth` in `snow_client.py` with a Bearer token flow
- **Add Problem Management view**: query the `problem` table and join on `cmdb_ci`
- **Slack alerting**: hook `calc_sla_breach_rate()` to a cron job with `requests.post` to a Slack webhook
- **Export to Power BI**: the CSV export in the Raw Data tab drops straight into Power BI Desktop

---

## 🧑‍💻 Author

Built by [Deep Sanghvi](https://www.linkedin.com/in/sanghvideep/) — Application Support Engineer  
Demonstrating: ServiceNow API integration · ITSM metrics · Python · Streamlit · Pandas · Plotly
