"""
Pure calculation helpers — no Streamlit imports here.
All functions receive a DataFrame and return scalars, Series, or DataFrames.
"""

import pandas as pd


def filter_resolved(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only resolved incidents with a valid resolution time."""
    return df[df["resolved_at"].notna() & df["resolution_minutes"].notna()].copy()


# ------------------------------------------------------------------ #
# Top-line KPIs                                                        #
# ------------------------------------------------------------------ #

def calc_mttr(df: pd.DataFrame) -> float:
    """Mean time to resolve in hours (resolved tickets only)."""
    resolved = filter_resolved(df)
    if resolved.empty:
        return 0.0
    return round(resolved["resolution_minutes"].mean() / 60, 2)


def calc_mtta(df: pd.DataFrame) -> float:
    """
    Mean time to acknowledge — approximated as time from opened_at to
    first state change. We use a simplified model: MTTA ~ 15% of MTTR
    when real ack data isn't available, unless the column exists.
    """
    if "acknowledged_at" in df.columns and df["acknowledged_at"].notna().any():
        df = df.copy()
        df["ack_minutes"] = (
            (df["acknowledged_at"] - df["opened_at"]).dt.total_seconds() / 60
        )
        return round(df["ack_minutes"].mean() / 60, 2)
    # Fallback estimate
    return round(calc_mttr(df) * 0.15, 2)


def calc_sla_breach_rate(df: pd.DataFrame) -> float:
    """Percentage of resolved tickets that breached SLA."""
    resolved = filter_resolved(df)
    if resolved.empty:
        return 0.0
    rate = resolved["sla_breached"].sum() / len(resolved) * 100
    return round(rate, 1)


def calc_reopen_rate(df: pd.DataFrame) -> float:
    """Placeholder — requires 'reopen_count' field from ServiceNow."""
    if "reopen_count" in df.columns:
        reopened = (df["reopen_count"].astype(int) > 0).sum()
        return round(reopened / len(df) * 100, 1) if len(df) else 0.0
    return 0.0


# ------------------------------------------------------------------ #
# Trend series                                                         #
# ------------------------------------------------------------------ #

def mttr_by_week(df: pd.DataFrame) -> pd.DataFrame:
    """Weekly average MTTR (hours) over time."""
    resolved = filter_resolved(df)
    if resolved.empty:
        return pd.DataFrame(columns=["week", "mttr_hours"])
    agg = (
        resolved.groupby("week")["mttr_hours"]
        .mean()
        .round(2)
        .reset_index()
        .rename(columns={"mttr_hours": "avg_mttr_hours"})
    )
    return agg


def volume_by_week(df: pd.DataFrame) -> pd.DataFrame:
    """Weekly incident count."""
    agg = df.groupby("week").size().reset_index(name="count")
    return agg


# ------------------------------------------------------------------ #
# Breakdowns                                                           #
# ------------------------------------------------------------------ #

def mttr_by_priority(df: pd.DataFrame) -> pd.DataFrame:
    resolved = filter_resolved(df)
    agg = (
        resolved.groupby("priority")["mttr_hours"]
        .agg(["mean", "median", "count"])
        .round(2)
        .reset_index()
        .rename(columns={"mean": "avg_hours", "median": "median_hours", "count": "tickets"})
    )
    priority_order = ["1 - Critical", "2 - High", "3 - Moderate", "4 - Low"]
    agg["priority"] = pd.Categorical(agg["priority"], categories=priority_order, ordered=True)
    return agg.sort_values("priority")


def mttr_by_group(df: pd.DataFrame, top_n: int = 8) -> pd.DataFrame:
    resolved = filter_resolved(df)
    agg = (
        resolved.groupby("assignment_group")["mttr_hours"]
        .mean()
        .round(2)
        .reset_index()
        .rename(columns={"mttr_hours": "avg_hours"})
        .sort_values("avg_hours", ascending=True)
        .head(top_n)
    )
    return agg


def volume_by_category(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("category").size().reset_index(name="count").sort_values("count", ascending=False)


def sla_breach_by_priority(df: pd.DataFrame) -> pd.DataFrame:
    resolved = filter_resolved(df)
    agg = resolved.groupby("priority")["sla_breached"].agg(["sum", "count"]).reset_index()
    agg["breach_rate"] = (agg["sum"] / agg["count"] * 100).round(1)
    agg.rename(columns={"sum": "breached", "count": "total"}, inplace=True)
    return agg


def top_recurring_cis(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    return (
        df.groupby("cmdb_ci")
        .size()
        .reset_index(name="incident_count")
        .sort_values("incident_count", ascending=False)
        .head(top_n)
    )
