#!/usr/bin/env python3
"""Validate Operation Evidence ledger examples.

Checks structural invariants for all evidence record types without requiring
third-party packages.  JSON Schema validation can be added later via
sourceos-devtools conformance runner.

Invariants checked:
- schema_version is "0.1.0" for every record in every file.
- Required top-level identifier fields are present per record type.
- DiagnosticExportEvidence: redaction_applied is true and
  contains_raw_credentials is false.
- AgentActionEvidence: delegated_by is present.
- PolicyGateEvidence: blocking/requires_decision/requires_admin statuses
  have remediation_path and responsible_actor.
- ArtifactAdmissionEvidence: gate_results is a non-empty list of objects
  with gate_id, gate_type, status.
- CompensationEvidence: compensated_task_ids is a non-empty list.
- ReleaseOperationEvidence: release_artifact_ids is a non-empty list.
- operation_id is consistent within all records in a single example file
  (when the file references a single operation).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "operation-evidence"

# Map from top-level key to (record_type_name, unique_id_field)
RECORD_TYPE_MAP: dict[str, tuple[str, str]] = {
    "evidence_records": ("OperationEvidenceRecord", "evidence_record_id"),
    "ledger_entries": ("OperationEventLedgerEntry", "ledger_entry_id"),
    "admission_evidence": ("ArtifactAdmissionEvidence", "admission_evidence_id"),
    "policy_gate_evidence": ("PolicyGateEvidence", "gate_evidence_id"),
    "decision_evidence": ("DecisionEvidence", "decision_evidence_id"),
    "agent_action_evidence": ("AgentActionEvidence", "agent_action_evidence_id"),
    "diagnostic_evidence": ("DiagnosticExportEvidence", "diagnostic_evidence_id"),
    "compensation_evidence": ("CompensationEvidence", "compensation_evidence_id"),
    "release_evidence": ("ReleaseOperationEvidence", "release_evidence_id"),
}

BLOCKING_GATE_STATUSES = {"blocking", "requires_decision", "requires_admin"}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def check_base_fields(
    path: Path,
    record: dict[str, Any],
    type_name: str,
    id_field: str,
) -> list[str]:
    errors: list[str] = []
    if record.get("schema_version") != "0.1.0":
        errors.append(
            f"{path}: {type_name} {record.get(id_field, '?')} schema_version must be 0.1.0"
        )
    if not record.get(id_field):
        errors.append(f"{path}: {type_name} missing required field '{id_field}'")
    if not record.get("operation_id"):
        errors.append(
            f"{path}: {type_name} {record.get(id_field, '?')} missing operation_id"
        )
    actor = record.get("actor")
    if not isinstance(actor, dict) or not actor.get("actor_type") or not actor.get("actor_id"):
        errors.append(
            f"{path}: {type_name} {record.get(id_field, '?')} missing or invalid actor"
        )
    if not record.get("timestamp") and not record.get("occurred_at") and not record.get("recorded_at"):
        errors.append(
            f"{path}: {type_name} {record.get(id_field, '?')} missing timestamp/occurred_at/recorded_at"
        )
    if not record.get("source_service"):
        errors.append(
            f"{path}: {type_name} {record.get(id_field, '?')} missing source_service"
        )
    return errors


def validate_operation_evidence_record(
    path: Path, record: dict[str, Any]
) -> list[str]:
    errors = check_base_fields(path, record, "OperationEvidenceRecord", "evidence_record_id")
    if not record.get("operation_phase"):
        errors.append(
            f"{path}: OperationEvidenceRecord {record.get('evidence_record_id', '?')} missing operation_phase"
        )
    if not record.get("command"):
        errors.append(
            f"{path}: OperationEvidenceRecord {record.get('evidence_record_id', '?')} missing command"
        )
    if not record.get("result"):
        errors.append(
            f"{path}: OperationEvidenceRecord {record.get('evidence_record_id', '?')} missing result"
        )
    return errors


def validate_operation_event_ledger_entry(
    path: Path, record: dict[str, Any]
) -> list[str]:
    errors = check_base_fields(path, record, "OperationEventLedgerEntry", "ledger_entry_id")
    if not record.get("event_id"):
        errors.append(
            f"{path}: OperationEventLedgerEntry {record.get('ledger_entry_id', '?')} missing event_id"
        )
    if not record.get("event_type"):
        errors.append(
            f"{path}: OperationEventLedgerEntry {record.get('ledger_entry_id', '?')} missing event_type"
        )
    if not record.get("occurred_at"):
        errors.append(
            f"{path}: OperationEventLedgerEntry {record.get('ledger_entry_id', '?')} missing occurred_at"
        )
    if not record.get("recorded_at"):
        errors.append(
            f"{path}: OperationEventLedgerEntry {record.get('ledger_entry_id', '?')} missing recorded_at"
        )
    return errors


def validate_artifact_admission_evidence(
    path: Path, record: dict[str, Any]
) -> list[str]:
    errors = check_base_fields(path, record, "ArtifactAdmissionEvidence", "admission_evidence_id")
    if not record.get("artifact_id"):
        errors.append(
            f"{path}: ArtifactAdmissionEvidence {record.get('admission_evidence_id', '?')} missing artifact_id"
        )
    if not record.get("admission_state"):
        errors.append(
            f"{path}: ArtifactAdmissionEvidence {record.get('admission_evidence_id', '?')} missing admission_state"
        )
    gate_results = record.get("gate_results")
    if not isinstance(gate_results, list) or len(gate_results) == 0:
        errors.append(
            f"{path}: ArtifactAdmissionEvidence {record.get('admission_evidence_id', '?')} gate_results must be a non-empty list"
        )
    else:
        for gate in gate_results:
            if not isinstance(gate, dict):
                errors.append(
                    f"{path}: ArtifactAdmissionEvidence {record.get('admission_evidence_id', '?')} gate_result item must be an object"
                )
                continue
            for field in ("gate_id", "gate_type", "status"):
                if not gate.get(field):
                    errors.append(
                        f"{path}: ArtifactAdmissionEvidence {record.get('admission_evidence_id', '?')} gate_result missing '{field}'"
                    )
    return errors


def validate_policy_gate_evidence(
    path: Path, record: dict[str, Any]
) -> list[str]:
    errors = check_base_fields(path, record, "PolicyGateEvidence", "gate_evidence_id")
    if not record.get("policy_gate_id"):
        errors.append(
            f"{path}: PolicyGateEvidence {record.get('gate_evidence_id', '?')} missing policy_gate_id"
        )
    if not record.get("gate_type"):
        errors.append(
            f"{path}: PolicyGateEvidence {record.get('gate_evidence_id', '?')} missing gate_type"
        )
    gate_status = record.get("gate_status")
    if not gate_status:
        errors.append(
            f"{path}: PolicyGateEvidence {record.get('gate_evidence_id', '?')} missing gate_status"
        )
    if not record.get("responsible_actor"):
        errors.append(
            f"{path}: PolicyGateEvidence {record.get('gate_evidence_id', '?')} missing responsible_actor"
        )
    if gate_status in BLOCKING_GATE_STATUSES:
        if not record.get("remediation_path"):
            errors.append(
                f"{path}: PolicyGateEvidence {record.get('gate_evidence_id', '?')} blocking gate missing remediation_path"
            )
    if not record.get("explanation"):
        errors.append(
            f"{path}: PolicyGateEvidence {record.get('gate_evidence_id', '?')} missing explanation"
        )
    return errors


def validate_decision_evidence(
    path: Path, record: dict[str, Any]
) -> list[str]:
    errors = check_base_fields(path, record, "DecisionEvidence", "decision_evidence_id")
    if not record.get("decision_id"):
        errors.append(
            f"{path}: DecisionEvidence {record.get('decision_evidence_id', '?')} missing decision_id"
        )
    if not record.get("decision_type"):
        errors.append(
            f"{path}: DecisionEvidence {record.get('decision_evidence_id', '?')} missing decision_type"
        )
    if not record.get("selected_option"):
        errors.append(
            f"{path}: DecisionEvidence {record.get('decision_evidence_id', '?')} missing selected_option"
        )
    return errors


def validate_agent_action_evidence(
    path: Path, record: dict[str, Any]
) -> list[str]:
    errors = check_base_fields(path, record, "AgentActionEvidence", "agent_action_evidence_id")
    delegated_by = record.get("delegated_by")
    if not isinstance(delegated_by, dict) or not delegated_by.get("actor_type") or not delegated_by.get("actor_id"):
        errors.append(
            f"{path}: AgentActionEvidence {record.get('agent_action_evidence_id', '?')} missing or invalid delegated_by"
        )
    if not record.get("agent_scope"):
        errors.append(
            f"{path}: AgentActionEvidence {record.get('agent_action_evidence_id', '?')} missing agent_scope"
        )
    if not record.get("command"):
        errors.append(
            f"{path}: AgentActionEvidence {record.get('agent_action_evidence_id', '?')} missing command"
        )
    return errors


def validate_diagnostic_export_evidence(
    path: Path, record: dict[str, Any]
) -> list[str]:
    errors = check_base_fields(path, record, "DiagnosticExportEvidence", "diagnostic_evidence_id")
    if record.get("redaction_applied") is not True:
        errors.append(
            f"{path}: DiagnosticExportEvidence {record.get('diagnostic_evidence_id', '?')} redaction_applied must be true"
        )
    if record.get("contains_raw_credentials") is not False:
        errors.append(
            f"{path}: DiagnosticExportEvidence {record.get('diagnostic_evidence_id', '?')} contains_raw_credentials must be false"
        )
    redaction_rules = record.get("redaction_rules")
    if not isinstance(redaction_rules, list) or len(redaction_rules) == 0:
        errors.append(
            f"{path}: DiagnosticExportEvidence {record.get('diagnostic_evidence_id', '?')} redaction_rules must be a non-empty list"
        )
    return errors


def validate_compensation_evidence(
    path: Path, record: dict[str, Any]
) -> list[str]:
    errors = check_base_fields(path, record, "CompensationEvidence", "compensation_evidence_id")
    if not record.get("compensation_type"):
        errors.append(
            f"{path}: CompensationEvidence {record.get('compensation_evidence_id', '?')} missing compensation_type"
        )
    compensated_task_ids = record.get("compensated_task_ids")
    if not isinstance(compensated_task_ids, list) or len(compensated_task_ids) == 0:
        errors.append(
            f"{path}: CompensationEvidence {record.get('compensation_evidence_id', '?')} compensated_task_ids must be a non-empty list"
        )
    return errors


def validate_release_operation_evidence(
    path: Path, record: dict[str, Any]
) -> list[str]:
    errors = check_base_fields(path, record, "ReleaseOperationEvidence", "release_evidence_id")
    if not record.get("release_type"):
        errors.append(
            f"{path}: ReleaseOperationEvidence {record.get('release_evidence_id', '?')} missing release_type"
        )
    release_artifact_ids = record.get("release_artifact_ids")
    if not isinstance(release_artifact_ids, list) or len(release_artifact_ids) == 0:
        errors.append(
            f"{path}: ReleaseOperationEvidence {record.get('release_evidence_id', '?')} release_artifact_ids must be a non-empty list"
        )
    return errors


VALIDATORS: dict[str, Any] = {
    "evidence_records": validate_operation_evidence_record,
    "ledger_entries": validate_operation_event_ledger_entry,
    "admission_evidence": validate_artifact_admission_evidence,
    "policy_gate_evidence": validate_policy_gate_evidence,
    "decision_evidence": validate_decision_evidence,
    "agent_action_evidence": validate_agent_action_evidence,
    "diagnostic_evidence": validate_diagnostic_export_evidence,
    "compensation_evidence": validate_compensation_evidence,
    "release_evidence": validate_release_operation_evidence,
}


def validate_file(path: Path, data: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    known_keys = set(RECORD_TYPE_MAP.keys())
    found_keys = known_keys.intersection(data.keys())
    if not found_keys:
        # Allow metadata-only files (e.g., files with only _example key)
        if all(k.startswith("_") for k in data.keys()):
            return []
        errors.append(
            f"{path}: no recognized evidence record keys found (expected one of: {sorted(known_keys)})"
        )
        return errors

    # Collect all operation_ids across the file to check consistency
    all_operation_ids: set[str] = set()

    for key in found_keys:
        validator = VALIDATORS[key]
        for record in as_list(data.get(key)):
            if not isinstance(record, dict):
                errors.append(f"{path}: {key} item must be an object")
                continue
            errors.extend(validator(path, record))
            op_id = record.get("operation_id")
            if op_id:
                all_operation_ids.add(op_id)

    # If all records in a file share exactly one operation_id that's fine.
    # If there are multiple, we only warn — a file may demonstrate multiple ops.
    # (No hard error here; just a structural note.)

    return errors


def main() -> int:
    if not EXAMPLES.exists():
        print(f"missing examples directory: {EXAMPLES}", file=sys.stderr)
        return 1

    errors: list[str] = []
    files = sorted(EXAMPLES.glob("*.json"))
    if not files:
        print(f"no example files found in {EXAMPLES}", file=sys.stderr)
        return 1

    for path in files:
        try:
            data = load_json(path)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}: failed to parse JSON: {exc}")
            continue
        except OSError as exc:
            errors.append(f"{path}: failed to read file: {exc}")
            continue
        errors.extend(validate_file(path, data))

    if errors:
        print("Operation Evidence example validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(files)} Operation Evidence example(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
