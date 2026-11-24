"""Hisn's three tools: asset lookup, runbook search, related-alert count. You write this file."""
from __future__ import annotations

from datetime import datetime, timedelta
import json
from pathlib import Path

from hisn.retrieval import search_runbooks  # re-exported: tests import it from here too

__all__ = ["lookup_asset", "related_alerts", "search_runbooks", "TOOLS", "TOOL_SCHEMAS"]

_DATA = Path(__file__).with_name("data")

def lookup_asset(host: str) -> dict:
    """Owner, criticality and environment of a host.

    Match ignoring case and surrounding spaces. Known host: the asset's fields (from
    hisn/data/assets.json) plus `"known": True`. Unknown host: `{"host": host, "known": False}`.
    """
    assets = json.loads((_DATA / "assets.json").read_text(encoding="utf-8"))
    for asset in assets:
        if asset["host"].casefold() == host.strip().casefold():
            return {**asset, "known": True}
    return {"host": host, "known": False}


def related_alerts(rule_id: str, agent: str, around: str, window_minutes: int = 60) -> dict:
    """Count alerts with the same rule on the same agent in the window before a time.

    Alerts from hisn/data/alerts.jsonl with the same `rule.id` and `agent.name` (agent compared
    ignoring case), with `around - window_minutes <= timestamp <= around` (both ends inclusive).
    Returns `{"count": int, "alert_ids": [...]}` in file order.
    `ValueError` unless `1 <= window_minutes <= 1440`.
    """
    if not 1 <= window_minutes <= 1440:
        raise ValueError("window_minutes must be between 1 and 1440")
    end = datetime.fromisoformat(around)
    start = end - timedelta(minutes=window_minutes)
    matches = []
    with (_DATA / "alerts.jsonl").open(encoding="utf-8") as source:
        for line in source:
            alert = json.loads(line)
            if (str(alert["rule"]["id"]) == str(rule_id)
                    and alert["agent"]["name"].casefold() == agent.casefold()
                    and start <= datetime.fromisoformat(alert["timestamp"]) <= end):
                matches.append(alert["id"])
    return {"count": len(matches), "alert_ids": matches}


# You write these two:
#
# TOOLS: dict mapping each tool's name to the Python function above (plus search_runbooks from
#        retrieval.py), so the agent loop can call `TOOLS[name](**arguments)`.
# TOOL_SCHEMAS: a list of three dicts {"name", "description", "input_schema"}, one per tool, in
#        the same shape `hisn/server.py` and the agent loop expect: `input_schema` is a JSON
#        Schema object with "type": "object", "properties", "required" and
#        "additionalProperties": False. Parameter types are only "string" or "integer".
TOOLS = {tool.__name__: tool for tool in (lookup_asset, search_runbooks, related_alerts)}


def _schema(name, description, required, optional_integer=None):
    properties = {argument: {"type": "string"} for argument in required}
    if optional_integer is not None:
        properties[optional_integer] = {"type": "integer"}
    return {
        "name": name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        },
    }


TOOL_SCHEMAS = [
    _schema("lookup_asset", "Look up the owner and criticality of a host.", ["host"]),
    _schema("search_runbooks", "Find runbooks that apply to an alert.", ["query"], "k"),
    _schema("related_alerts", "Count matching earlier alerts for a host and rule.",
            ["rule_id", "agent", "around"], "window_minutes"),
]
