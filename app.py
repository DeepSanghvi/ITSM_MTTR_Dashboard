"""
Incident MTTR Dashboard
=======================
Connects to ServiceNow (or runs on mock data) and renders:
  • Top-line KPI cards
  • MTTR & volume trends over time
  • Breakdowns by priority, assignment group, category
  • SLA breach analysis
  • Top recurring CIs (problem management view)
  • Raw incident table with filters

Run:  streamlit run app.py
"""

import os
import sys

# Make project root importable
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from utils.snow_client import ServiceNowClient
from utils import metrics, charts

# ------------------------------------------------------------------ #
# Page config                                                          #
# ------------------------------------------------------------------ #

st.set_page_config(
    page_title="Incident MTTR Dashboard",
    page_icon="🔔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------ #
# Custom CSS — minimal, dark-mode-compatible                           #
# ------------------------------------------------------------------ #

st.markdown("""
<style>
  [data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 600; }
  [data-testid="stMetricDelta"] { font-size: 0.85rem; }
  .kpi-label { font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 0.06em; }
  div[data-testid="column"] > div > div > div > div { border-radius: 12px; }
  .stTabs [data-baseweb="tab-list"] { gap: 8px; }
  .stTabs [data-baseweb="tab"] { padding: 6px 16px; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------ #
# Sidebar — filters & data source                                      #
# ------------------------------------------------------------------ #

with st.sidebar:
    st.image("https://img.shields.io/badge/ServiceNow-ITSM-brightgreen", width=160)
    st.title("⚙️ Controls")

    data_mode = st.radio(
        "Data source",
        ["Mock (demo)", "Live ServiceNow"],
        index=0,
        help="Switch to Live to connect to your instance via .env credentials.",
    )
    if data_mode == "Live ServiceNow":
        os.environ["DATA_MODE"] = "live"
        st.info("Set SNOW_INSTANCE, SNOW_USERNAME, SNOW_PASSWORD in your .env file.")
    else:
        os.environ["DATA_MODE"] = "mock"

    st.divider()

    days_back = st.slider("Look-back window (days)", 7, 180, 90)
    priority_filter = st.multiselect(
        "Priority filter",
        options=["1 - Critical", "2 - High", "3 - Moderate", "4 - Low"],
        default=["1 - Critical", "2 - High", "3 - Moderate", "4 - Low"],
    )
    group_filter = st.text_input("Assignment group contains", "")

    st.divider()
    st.caption("Built for portfolio — Deep Singh")
    st.caption("[GitHub source](#)")

# ------------------------------------------------------------------ #
# Load data                                                            #
# ------------------------------------------------------------------ #

@st.cache_data(ttl=300, show_spinner="Fetching incidents...")
def load_data(mode: str, days: int):
    client = ServiceNowClient()
    return client.get_incidents(days_back=days)


df_raw = load_data(os.environ.get("DATA_MODE", "mock"), days_back)

# Apply sidebar filters
df = df_raw.copy()
if priority_filter:
    df = df[df["priority"].isin(priority_filter)]
if group_filter.strip():
    df = df[df["assignment_group"].str.contains(group_filter.strip(), case=False, na=False)]

# Slice to look-back window
import pandas as pd
cutoff = pd.Timestamp.now() - pd.Timedelta(days=days_back)
df = df[df["opened_at"] >= cutoff]

# ------------------------------------------------------------------ #
# Header                                                               #
# ------------------------------------------------------------------ #

st.title("🔔 Incident MTTR Dashboard")
mode_badge = "🟡 Mock data" if os.environ.get("DATA_MODE") == "mock" else "🟢 Live — ServiceNow"
st.caption(f"{mode_badge} · {len(df):,} incidents · last {days_back} days")
st.divider()

# ------------------------------------------------------------------ #
# KPI row                                                              #
# ------------------------------------------------------------------ #

mttr   = metrics.calc_mttr(df)
mtta   = metrics.calc_mtta(df)
breach = metrics.calc_sla_breach_rate(df)
open_  = (df["state"] == "1").sum()
total  = len(df)

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.metric("MTTR (avg hrs)", f"{mttr:.1f}",
              help="Mean time to resolve — all resolved incidents in the selected window.")
with c2:
    st.metric("MTTA (avg hrs)", f"{mtta:.1f}",
              help="Mean time to acknowledge (estimated as 15% of MTTR when ack data unavailable).")
with c3:
    st.metric("SLA breach rate", f"{breach}%",
              delta=f"{breach - 10:.1f}% vs 10% target",
              delta_color="inverse",
              help="% of tickets that exceeded SLA threshold for their priority.")
with c4:
    st.metric("Open incidents", f"{open_:,}",
              help="Tickets currently in state New or In Progress.")
with c5:
    st.metric("Total incidents", f"{total:,}")

st.divider()

# ------------------------------------------------------------------ #
# Tabs                                                                 #
# ------------------------------------------------------------------ #

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Trends", "🎯 Priorities", "👥 Teams", "🚨 SLA & CIs", "🗂️ Raw data"
])

# ── Tab 1: Trends ────────────────────────────────────────────────── #

with tab1:
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("MTTR trend by week")
        trend_df = metrics.mttr_by_week(df)
        if trend_df.empty:
            st.info("No resolved incidents in this window.")
        else:
            st.plotly_chart(charts.mttr_trend_chart(trend_df), use_container_width=True)

    with col_right:
        st.subheader("Incident volume by week")
        vol_df = metrics.volume_by_week(df)
        st.plotly_chart(charts.volume_trend_chart(vol_df), use_container_width=True)

# ── Tab 2: Priorities ────────────────────────────────────────────── #

with tab2:
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("MTTR by priority")
        prio_df = metrics.mttr_by_priority(df)
        if prio_df.empty:
            st.info("No data.")
        else:
            st.plotly_chart(charts.mttr_by_priority_chart(prio_df), use_container_width=True)
            st.dataframe(
                prio_df.rename(columns={
                    "avg_hours": "Avg hrs", "median_hours": "Median hrs", "tickets": "Tickets"
                }),
                use_container_width=True, hide_index=True,
            )

    with col_r:
        st.subheader("Incidents by category")
        cat_df = metrics.volume_by_category(df)
        st.plotly_chart(charts.volume_by_category_chart(cat_df), use_container_width=True)

# ── Tab 3: Teams ─────────────────────────────────────────────────── #

with tab3:
    st.subheader("Avg MTTR by assignment group")
    group_df = metrics.mttr_by_group(df)
    if group_df.empty:
        st.info("No resolved incidents for group breakdown.")
    else:
        st.plotly_chart(charts.mttr_by_group_chart(group_df), use_container_width=True)
        st.caption("Lower is better. Sorted by fastest → slowest average resolution time.")

# ── Tab 4: SLA & CIs ─────────────────────────────────────────────── #

with tab4:
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("SLA breach rate by priority")
        sla_df = metrics.sla_breach_by_priority(df)
        if sla_df.empty:
            st.info("No data.")
        else:
            st.plotly_chart(charts.sla_breach_chart(sla_df), use_container_width=True)

    with col_r:
        st.subheader("Top recurring CIs (problem mgmt)")
        ci_df = metrics.top_recurring_cis(df)
        st.plotly_chart(charts.recurring_ci_chart(ci_df), use_container_width=True)
        st.caption(
            "CIs with the highest incident count — candidates for Problem records or change requests."
        )

# ── Tab 5: Raw data ──────────────────────────────────────────────── #

with tab5:
    st.subheader("Incident log")

    search = st.text_input("Search by ticket number or description", "")
    display_df = df.copy()
    if search.strip():
        mask = (
            display_df["number"].str.contains(search, case=False, na=False) |
            display_df["short_description"].str.contains(search, case=False, na=False)
        )
        display_df = display_df[mask]

    cols = ["number", "priority", "category", "assignment_group",
            "cmdb_ci", "opened_at", "resolved_at", "mttr_hours", "sla_breached"]
    st.dataframe(
        display_df[cols].rename(columns={
            "number": "Ticket", "priority": "Priority", "category": "Category",
            "assignment_group": "Group", "cmdb_ci": "CI",
            "opened_at": "Opened", "resolved_at": "Resolved",
            "mttr_hours": "MTTR (hrs)", "sla_breached": "SLA Breach",
        }),
        use_container_width=True,
        hide_index=True,
    )

    csv = display_df[cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Export to CSV",
        data=csv,
        file_name="incidents_export.csv",
        mime="text/csv",
    )
