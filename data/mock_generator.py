"""
Generates realistic mock ServiceNow incident data for demo/testing.
Mirrors the exact schema returned by the ServiceNow Incident Table API.
"""

import random
import pandas as pd
from datetime import datetime, timedelta


CATEGORIES = ["network", "software", "hardware", "database", "security", "application"]
PRIORITIES = {"1 - Critical": 1, "2 - High": 2, "3 - Moderate": 3, "4 - Low": 4}
ASSIGNMENT_GROUPS = [
    "Network Ops", "App Support L2", "Database Admins",
    "Security Ops", "Cloud Infra", "Platform Engineering"
]
CMDB_CIS = [
    "prod-api-gateway", "auth-service", "db-primary", "kafka-cluster",
    "payment-service", "identity-provider", "cdn-edge", "monitoring-stack"
]
RESOLVERS = [
    "j.smith", "a.patel", "d.nguyen", "r.kumar",
    "l.chen", "m.okonkwo", "s.torres", "k.wilson"
]

# Resolution time ranges per priority (minutes)
RESOLUTION_RANGES = {
    "1 - Critical":  (15, 240),
    "2 - High":      (60, 480),
    "3 - Moderate":  (120, 1440),
    "4 - Low":       (240, 4320),
}


def _random_incident(index: int, base_date: datetime) -> dict:
    priority = random.choice(list(PRIORITIES.keys()))
    lo, hi = RESOLUTION_RANGES[priority]

    # Skew: ~10% of incidents breach expected resolution time
    breach_multiplier = random.uniform(1.8, 3.5) if random.random() < 0.10 else 1.0
    resolution_minutes = int(random.uniform(lo, hi) * breach_multiplier)

    opened_at = base_date - timedelta(
        days=random.randint(0, 89),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )
    resolved_at = opened_at + timedelta(minutes=resolution_minutes)

    # A few incidents still open (no resolved_at)
    is_open = random.random() < 0.08
    state = "1" if is_open else "6"  # 1=New/In Progress, 6=Resolved

    return {
        "number": f"INC{str(1000000 + index).zfill(7)}",
        "priority": priority,
        "category": random.choice(CATEGORIES),
        "assignment_group": {"display_value": random.choice(ASSIGNMENT_GROUPS)},
        "cmdb_ci": {"display_value": random.choice(CMDB_CIS)},
        "resolved_by": {"display_value": "" if is_open else random.choice(RESOLVERS)},
        "opened_at": opened_at.strftime("%Y-%m-%d %H:%M:%S"),
        "resolved_at": "" if is_open else resolved_at.strftime("%Y-%m-%d %H:%M:%S"),
        "state": state,
        "short_description": f"Mock incident #{index} — {random.choice(CMDB_CIS)} issue",
    }


def generate_mock_incidents(n: int = 300) -> list[dict]:
    base = datetime.now()
    return [_random_incident(i, base) for i in range(1, n + 1)]


def incidents_to_df(raw: list[dict]) -> pd.DataFrame:
    """Normalise raw ServiceNow API records (or mock dicts) into a flat DataFrame."""
    rows = []
    for r in raw:
        rows.append({
            "number":           r.get("number", ""),
            "priority":         r.get("priority", ""),
            "category":         r.get("category", ""),
            "assignment_group": r.get("assignment_group", {}).get("display_value", ""),
            "cmdb_ci":          r.get("cmdb_ci", {}).get("display_value", ""),
            "resolved_by":      r.get("resolved_by", {}).get("display_value", ""),
            "opened_at":        r.get("opened_at", ""),
            "resolved_at":      r.get("resolved_at", ""),
            "state":            r.get("state", ""),
            "short_description": r.get("short_description", ""),
        })

    df = pd.DataFrame(rows)
    df["opened_at"]   = pd.to_datetime(df["opened_at"],   errors="coerce")
    df["resolved_at"] = pd.to_datetime(df["resolved_at"], errors="coerce")

    # Resolution time in minutes
    df["resolution_minutes"] = (
        (df["resolved_at"] - df["opened_at"]).dt.total_seconds() / 60
    ).where(df["resolved_at"].notna())

    # Human-readable MTTR column (hours)
    df["mttr_hours"] = (df["resolution_minutes"] / 60).round(2)

    # Week label for trending
    df["week"] = df["opened_at"].dt.to_period("W").astype(str)

    # SLA breach flag — simple threshold per priority
    THRESHOLDS = {
        "1 - Critical": 240,
        "2 - High": 480,
        "3 - Moderate": 1440,
        "4 - Low": 4320,
    }
    df["sla_breached"] = df.apply(
        lambda row: (
            row["resolution_minutes"] > THRESHOLDS.get(row["priority"], 9999)
            if pd.notna(row["resolution_minutes"]) else False
        ),
        axis=1
    )

    return df
