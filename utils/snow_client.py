"""
ServiceNow Incident Table API client.
Supports basic auth; swap for OAuth token if your instance requires it.

Docs: https://developer.servicenow.com/dev.do#!/reference/api/tokyo/rest/c_TableAPI
"""

import os
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
from data.mock_generator import generate_mock_incidents, incidents_to_df
import pandas as pd


class ServiceNowClient:
    """
    Fetches incidents from the ServiceNow Table API.
    Falls back to mock data automatically when DATA_MODE=mock (default).
    """

    TABLE = "incident"
    FIELDS = (
        "number,priority,category,assignment_group,cmdb_ci,"
        "resolved_by,opened_at,resolved_at,state,short_description"
    )

    def __init__(self):
        self.instance = os.getenv("SNOW_INSTANCE", "")
        self.username = os.getenv("SNOW_USERNAME", "")
        self.password = os.getenv("SNOW_PASSWORD", "")
        self.mode = os.getenv("DATA_MODE", "mock").lower()
        self.base_url = f"https://{self.instance}/api/now/table/{self.TABLE}"

    # ------------------------------------------------------------------ #
    # Public                                                               #
    # ------------------------------------------------------------------ #

    def get_incidents(self, days_back: int = 90, limit: int = 500) -> pd.DataFrame:
        """Return a normalised DataFrame of incidents for the past N days."""
        if self.mode == "mock":
            raw = generate_mock_incidents(n=300)
            return incidents_to_df(raw)
        return self._fetch_live(days_back=days_back, limit=limit)

    # ------------------------------------------------------------------ #
    # Internal                                                             #
    # ------------------------------------------------------------------ #

    def _fetch_live(self, days_back: int, limit: int) -> pd.DataFrame:
        since = (datetime.utcnow() - timedelta(days=days_back)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        params = {
            "sysparm_query":  f"opened_at>={since}^ORDERBYDESCopened_at",
            "sysparm_fields": self.FIELDS,
            "sysparm_limit":  limit,
            "sysparm_display_value": "all",   # returns both value + display_value
            "sysparm_exclude_reference_link": "true",
        }
        all_records: list[dict] = []
        offset = 0

        while True:
            params["sysparm_offset"] = offset
            resp = requests.get(
                self.base_url,
                params=params,
                auth=HTTPBasicAuth(self.username, self.password),
                timeout=30,
            )
            resp.raise_for_status()
            batch = resp.json().get("result", [])
            if not batch:
                break
            all_records.extend(batch)
            if len(batch) < limit:
                break
            offset += limit

        return incidents_to_df(all_records)
