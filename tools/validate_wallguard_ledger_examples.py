#!/usr/bin/env python3
"""Validate WallGuard ledger event examples."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "wallguard-ledger-event.schema.json"
EXAMPLE_DIR = ROOT / "examples" / "wallguard-ledger"
NEGATIVE_OUTCOMES = {"deny", "redact", "quarantine", "escalate", "clean_room_release_denied"}
RESTRICTED_CLASSES = {"client_confidential", "matter_restricted", "wall_restricted"}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_schema(instance: dict, schema: dict, *, source_label: str) -> None:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        lines = [f"{source_label} failed schema validation:"]
        for error in errors:
            location = ".".join(str(part) for part in error.path) or "<root>"
            lines.append(f" - {location}: {error.message}")
        raise ValueError("\n".join(lines))


def semantic_diagnostics(record: dict) -> list[str]:
    diagnostics: list[str] = []
    outcome = record["wall_decision_outcome"]
    reason = record["reason_code"]
    labels = record["resource_label_summary"]
    classification = labels["classification"]
    visibility = record["receipt_visibility_class"]

    if record["contains_restricted_payload"]:
        diagnostics.append("ledger events must not store restricted payload content")

    if classification in RESTRICTED_CLASSES:
        if not record.get("redaction_summary"):
            diagnostics.append("restricted ledger events require redaction_summary")
        if not record.get("residual_restrictions"):
            diagnostics.append("restricted ledger events require residual_restrictions")
        if visibility == "public" and outcome != "clean_room_release_allowed":
            diagnostics.append("restricted events must not be public unless clean-room release allowed")

    if outcome in NEGATIVE_OUTCOMES:
        if reason == "same_wall_allowed":
            diagnostics.append("negative outcomes must not use same_wall_allowed")
        if visibility == "public":
            diagnostics.append("negative restricted events must not be public")

    if outcome == "allow" and reason != "same_wall_allowed":
        diagnostics.append("plain allow outcome requires same_wall_allowed reason")

    if record["event_type"] == "wall_clean_room_release":
        if outcome not in {"clean_room_release_requested", "clean_room_release_allowed", "clean_room_release_denied"}:
            diagnostics.append("clean-room release events require clean-room WallGuard outcome")
        if outcome == "clean_room_release_allowed" and classification in RESTRICTED_CLASSES and not record.get("residual_restrictions"):
            diagnostics.append("clean-room release from restricted source requires residual restrictions")

    return diagnostics


def expected_semantic_result(path: Path) -> str:
    return "fail" if ".rejected." in path.name else "pass"


def main() -> int:
    schema = load_json(SCHEMA)
    Draft202012Validator.check_schema(schema)
    examples = sorted(EXAMPLE_DIR.glob("*.json"))
    if not examples:
        raise SystemExit("No WallGuard ledger examples found")

    results = []
    for path in examples:
        record = load_json(path)
        validate_schema(record, schema, source_label=str(path.relative_to(ROOT)))
        diagnostics = semantic_diagnostics(record)
        actual = "fail" if diagnostics else "pass"
        expected = expected_semantic_result(path)
        result = {"example": path.name, "expected": expected, "actual": actual, "diagnostics": diagnostics}
        results.append(result)
        if actual != expected:
            raise ValueError(json.dumps(result, indent=2))

    print(json.dumps({"ok": True, "checked": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
