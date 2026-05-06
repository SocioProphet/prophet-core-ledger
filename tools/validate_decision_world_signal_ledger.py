#!/usr/bin/env python3
"""Validate decision-grade world signal ledger examples.

Dependency-free structural validation for the first append-only ledger examples.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "decision-world-signals"
GUIDE = ROOT / "ledger" / "decision-world-signals" / "README.md"

ENTRY_TYPES = {
    "FEATURE_PROMOTION_EVENT",
    "ENERGY_LEDGER_EVENT",
    "PROOF_ARTIFACT_EVENT",
}

PROMOTION_STATES = {"EVIDENCE_ONLY", "REVIEW", "REJECTED", "PROMOTED"}
PROMOTION_DECISIONS = {"REJECT", "REVIEW", "INSERT_EVIDENCE_ONLY", "PROMOTE_CANONICAL"}
PROOF_STATUSES = {"PROVED", "VIOLATED", "UNKNOWN", "TIMEOUT", "PRECISION_LOSS_REVIEW_REQUIRED"}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("top-level JSON value must be an object")
    return data


def require(path: Path, data: dict[str, Any], field: str, errors: list[str]) -> Any:
    value = data.get(field)
    if value in (None, "", []):
        errors.append(f"{path}: missing required field {field}")
    return value


def validate_common(path: Path, data: dict[str, Any], errors: list[str]) -> None:
    for field in ["ledger_entry_id", "entry_type", "schema_ref", "created_at", "replay_instructions"]:
        require(path, data, field, errors)
    if data.get("entry_type") not in ENTRY_TYPES:
        errors.append(f"{path}: invalid entry_type {data.get('entry_type')!r}")


def validate_feature_promotion(path: Path, data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_common(path, data, errors)
    for field in ["feature_id", "source_artifact_hash", "contract_ref", "policy_id", "promotion_state", "responsible_actor"]:
        require(path, data, field, errors)
    if data.get("promotion_state") not in PROMOTION_STATES:
        errors.append(f"{path}: invalid promotion_state {data.get('promotion_state')!r}")
    return errors


def validate_energy(path: Path, data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_common(path, data, errors)
    required = [
        "source_artifact_id",
        "extraction_run_id",
        "policy_id",
        "candidate_set_id",
        "top_entity_id",
        "top_score",
        "runnerup_entity_id",
        "runnerup_score",
        "margin_delta",
        "perturbation_flip_rate",
        "promotion_decision",
        "decision_reason_codes",
    ]
    for field in required:
        require(path, data, field, errors)
    if data.get("promotion_decision") not in PROMOTION_DECISIONS:
        errors.append(f"{path}: invalid promotion_decision {data.get('promotion_decision')!r}")
    flip_rate = data.get("perturbation_flip_rate")
    if isinstance(flip_rate, (int, float)) and not 0 <= flip_rate <= 1:
        errors.append(f"{path}: perturbation_flip_rate must be between 0 and 1")
    if isinstance(data.get("top_score"), (int, float)) and isinstance(data.get("runnerup_score"), (int, float)):
        expected = data["top_score"] - data["runnerup_score"]
        actual = data.get("margin_delta")
        if isinstance(actual, (int, float)) and abs(expected - actual) > 1e-9:
            errors.append(f"{path}: margin_delta must equal top_score - runnerup_score")
    return errors


def validate_proof(path: Path, data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_common(path, data, errors)
    for field in ["claim_name", "claim_version", "input_hashes", "analyzer", "analysis_domains", "result_status"]:
        require(path, data, field, errors)
    if data.get("result_status") not in PROOF_STATUSES:
        errors.append(f"{path}: invalid result_status {data.get('result_status')!r}")
    if data.get("result_status") == "PROVED" and not data.get("witness_ref"):
        errors.append(f"{path}: PROVED proof event requires witness_ref")
    if data.get("result_status") == "VIOLATED" and not data.get("violation_evidence_ref"):
        errors.append(f"{path}: VIOLATED proof event requires violation_evidence_ref")
    return errors


VALIDATORS = {
    "feature-promotion-event.json": validate_feature_promotion,
    "energy-ledger-event.json": validate_energy,
    "proof-artifact-event.json": validate_proof,
}


def main() -> int:
    errors: list[str] = []
    if not GUIDE.exists():
        errors.append(f"missing implementation guide: {GUIDE}")
    if not EXAMPLES.exists():
        errors.append(f"missing examples directory: {EXAMPLES}")
    else:
        for filename, validator in VALIDATORS.items():
            path = EXAMPLES / filename
            if not path.exists():
                errors.append(f"missing example: {path}")
                continue
            try:
                data = load_json(path)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{path}: failed to parse JSON: {exc}")
                continue
            errors.extend(validator(path, data))

    if errors:
        print("Decision world signal ledger validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(VALIDATORS)} decision world signal ledger example(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
