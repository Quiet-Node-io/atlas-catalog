"""Publish safety guards for atlas-catalog."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SafetyResult:
    allowed: bool
    issues: list[str]
    deduped: list[str] | None = None
    override_used: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "issues": self.issues,
            "deduped": self.deduped or [],
            "override_used": self.override_used,
        }


def _model_map(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("id")): row
        for row in catalog.get("models", [])
        if isinstance(row, dict) and row.get("id")
    }


def _has_evidence(row: dict[str, Any]) -> bool:
    evidence = row.get("discovery_evidence")
    if not isinstance(evidence, dict):
        return False
    sources = evidence.get("sources")
    return isinstance(sources, list) and bool(sources)


def _aliases(row: dict[str, Any]) -> set[str]:
    aliases = row.get("aliases")
    if not isinstance(aliases, list):
        return set()
    return {alias.strip() for alias in aliases if isinstance(alias, str) and alias.strip()}


def _same_artifact(base_row: dict[str, Any], proposed_row: dict[str, Any]) -> bool:
    fields = (
        "registry",
        "category",
        "family",
        "display_name",
        "variant_label",
        "quantization",
        "variant",
    )
    if any(base_row.get(field) != proposed_row.get(field) for field in fields):
        return False
    return bool(base_row.get("unrestricted")) == bool(proposed_row.get("unrestricted"))


def _dedupe_target(
    removed_id: str,
    removed_row: dict[str, Any],
    proposed_rows: dict[str, dict[str, Any]],
) -> str | None:
    for proposed_id, proposed_row in proposed_rows.items():
        if removed_id in _aliases(proposed_row) and _same_artifact(removed_row, proposed_row):
            return proposed_id
    return None


def evaluate_catalog_publish(
    base: dict[str, Any],
    proposed: dict[str, Any],
    *,
    allow_destructive: bool = False,
) -> SafetyResult:
    issues: list[str] = []
    deduped: list[str] = []
    base_rows = _model_map(base)
    proposed_rows = _model_map(proposed)

    for model_id, row in base_rows.items():
        if model_id not in proposed_rows:
            target_id = _dedupe_target(model_id, row, proposed_rows)
            if target_id:
                deduped.append(f"{model_id}: deduped into {target_id} alias")
                continue
            issues.append(f"{model_id}: removed catalog row")
            continue
        next_row = proposed_rows[model_id]
        if row.get("default") and not next_row.get("default"):
            issues.append(f"{model_id}: default flag removed")
        if row.get("status") == "active" and next_row.get("status") in {"hidden", "removed", "deprecated"}:
            issues.append(f"{model_id}: status changed from active to {next_row.get('status')}")
        if not row.get("superseded_by") and next_row.get("superseded_by"):
            issues.append(f"{model_id}: superseded_by added and requires review")

    for model_id, row in proposed_rows.items():
        if model_id not in base_rows and not _has_evidence(row):
            issues.append(f"{model_id}: missing discovery evidence for added row")

    if issues and not allow_destructive:
        return SafetyResult(False, issues, deduped=deduped)
    return SafetyResult(
        True,
        issues,
        deduped=deduped,
        override_used=bool(issues and allow_destructive),
    )


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check atlas-catalog publish safety.")
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--proposed", required=True, type=Path)
    parser.add_argument("--allow-destructive", action="store_true")
    args = parser.parse_args()
    result = evaluate_catalog_publish(
        _load(args.base),
        _load(args.proposed),
        allow_destructive=args.allow_destructive,
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.allowed else 1


if __name__ == "__main__":
    raise SystemExit(main())
