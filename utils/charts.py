"""
Centralised chart builders using Plotly Express / Graph Objects.
Each function returns a plotly Figure ready for st.plotly_chart().
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Shared colour palette — maps to priority levels
PRIORITY_COLORS = {
    "1 - Critical":  "#E24B4A",
    "2 - High":      "#EF9F27",
    "3 - Moderate":  "#378ADD",
    "4 - Low":       "#1D9E75",
}

BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=12),
    margin=dict(l=20, r=20, t=30, b=20),
)


def _apply_base(fig: go.Figure) -> go.Figure:
    fig.update_layout(**BASE_LAYOUT)
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.1)", zeroline=False)
    return fig


# ------------------------------------------------------------------ #
# Trend charts                                                         #
# ------------------------------------------------------------------ #

def mttr_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Line chart: weekly average MTTR over time."""
    fig = px.line(
        df, x="week", y="avg_mttr_hours",
        labels={"week": "Week", "avg_mttr_hours": "Avg MTTR (hrs)"},
        markers=True,
        color_discrete_sequence=["#378ADD"],
    )
    fig.update_traces(line_width=2.5, marker_size=6)
    return _apply_base(fig)


def volume_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Bar chart: weekly incident volume."""
    fig = px.bar(
        df, x="week", y="count",
        labels={"week": "Week", "count": "Incidents"},
        color_discrete_sequence=["#534AB7"],
    )
    fig.update_traces(marker_line_width=0)
    return _apply_base(fig)


# ------------------------------------------------------------------ #
# Breakdown charts                                                     #
# ------------------------------------------------------------------ #

def mttr_by_priority_chart(df: pd.DataFrame) -> go.Figure:
    """Grouped bar: avg vs median MTTR per priority."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Avg MTTR",
        x=df["priority"], y=df["avg_hours"],
        marker_color=[PRIORITY_COLORS.get(p, "#888") for p in df["priority"]],
        marker_line_width=0,
    ))
    fig.add_trace(go.Bar(
        name="Median MTTR",
        x=df["priority"], y=df["median_hours"],
        marker_color=[PRIORITY_COLORS.get(p, "#888") for p in df["priority"]],
        marker_line_width=0,
        opacity=0.5,
    ))
    fig.update_layout(barmode="group", **BASE_LAYOUT)
    fig.update_layout(
        yaxis_title="Hours",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.1)", zeroline=False)
    return fig


def mttr_by_group_chart(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar: avg MTTR per assignment group (sorted best → worst)."""
    fig = px.bar(
        df.sort_values("avg_hours"),
        x="avg_hours", y="assignment_group",
        orientation="h",
        labels={"avg_hours": "Avg MTTR (hrs)", "assignment_group": ""},
        color="avg_hours",
        color_continuous_scale=["#1D9E75", "#EF9F27", "#E24B4A"],
    )
    fig.update_layout(coloraxis_showscale=False, **BASE_LAYOUT)
    fig.update_traces(marker_line_width=0)
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.1)", zeroline=False)
    return fig


def volume_by_category_chart(df: pd.DataFrame) -> go.Figure:
    """Donut chart: incident volume breakdown by category."""
    fig = px.pie(
        df, names="category", values="count",
        hole=0.55,
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_traces(textposition="outside", textinfo="percent+label")
    fig.update_layout(**BASE_LAYOUT)
    return fig


def sla_breach_chart(df: pd.DataFrame) -> go.Figure:
    """Stacked bar: SLA breach rate per priority."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Within SLA",
        x=df["priority"],
        y=100 - df["breach_rate"],
        marker_color="#1D9E75",
        marker_line_width=0,
    ))
    fig.add_trace(go.Bar(
        name="Breached",
        x=df["priority"],
        y=df["breach_rate"],
        marker_color="#E24B4A",
        marker_line_width=0,
    ))
    fig.update_layout(
        barmode="stack",
        yaxis_title="% of tickets",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        **BASE_LAYOUT,
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.1)", zeroline=False)
    return fig


def recurring_ci_chart(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar: top CIs by incident count (problem management view)."""
    fig = px.bar(
        df.sort_values("incident_count"),
        x="incident_count", y="cmdb_ci",
        orientation="h",
        labels={"incident_count": "Incident count", "cmdb_ci": ""},
        color_discrete_sequence=["#534AB7"],
    )
    fig.update_traces(marker_line_width=0)
    fig.update_layout(**BASE_LAYOUT)
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.1)", zeroline=False)
    return fig
