"""Repo-state helpers for discovery review suppression."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SUPPRESS_STATES = {"ignored", "reviewed", "open_pr", "superseded"}


def load_review_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"discoveries": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def filter_previously_reviewed(
    discoveries: list[dict[str, Any]],
    state: dict[str, Any],
) -> list[dict[str, Any]]:
    state_rows = state.get("discoveries", {})
    visible: list[dict[str, Any]] = []
    for discovery in discoveries:
        saved = state_rows.get(discovery.get("id"))
        if (
            isinstance(saved, dict)
            and saved.get("state") in SUPPRESS_STATES
            and saved.get("source_hash") == discovery.get("source_hash")
        ):
            continue
        visible.append(discovery)
    return visible


def update_open_pr_state(state: dict[str, Any], discoveries: list[dict[str, Any]]) -> dict[str, Any]:
    next_state = dict(state)
    rows = dict(next_state.get("discoveries", {}))
    for discovery in discoveries:
        rows[discovery["id"]] = {
            "state": "open_pr",
            "source_hash": discovery.get("source_hash"),
            "provider": discovery.get("provider"),
        }
    next_state["discoveries"] = rows
    return next_state
