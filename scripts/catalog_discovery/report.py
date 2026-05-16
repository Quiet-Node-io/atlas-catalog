"""Markdown and manifest output for discovery runs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def render_report(
    *,
    run_id: str,
    diff_result: dict[str, list[dict[str, Any]]],
    provider_errors: list[dict[str, Any]],
    safety: dict[str, Any],
) -> str:
    lines = [
        f"# {run_id} Catalog Discovery Review",
        "",
        f"- Added discoveries: {len(diff_result.get('added', []))}",
        f"- Removed/superseded review candidates: {len(diff_result.get('removed', []))}",
        f"- Changed discoveries: {len(diff_result.get('changed', []))}",
        f"- Provider errors: {len(provider_errors)}",
        f"- Safety allowed: {safety.get('allowed')}",
        "",
        "## Added Discoveries",
        "",
    ]
    if diff_result.get("added"):
        for entry in diff_result["added"]:
            lines.append(f"- `{entry.get('id')}` from `{entry.get('provider')}` ({entry.get('source_url')})")
    else:
        lines.append("- None")
    lines.extend(["", "## Removed / Superseded Review", ""])
    if diff_result.get("removed"):
        for entry in diff_result["removed"]:
            lines.append(f"- `{entry.get('id')}`: {entry.get('reason')}")
    else:
        lines.append("- None")
    lines.extend(["", "## Safety", ""])
    issues = safety.get("issues") or []
    if issues:
        for issue in issues:
            lines.append(f"- {issue}")
    else:
        lines.append("- No blocking safety issues.")
    if provider_errors:
        lines.extend(["", "## Provider Errors", ""])
        for error in provider_errors:
            lines.append(f"- `{error.get('provider')}`: {error.get('error')}")
    lines.append("")
    return "\n".join(lines)
