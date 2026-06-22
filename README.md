# prophet-core-ledger

Prophet core: prophet-core-ledger (open-only, auditable, provenance-first)

This repository is the **P0 ledger and evidence plane** for the SocioProphet platform. All Operation Plane lifecycle evidence is recorded here rather than in separate, per-service audit logs.

## Purpose

The Operation Plane runtime in `prophet-platform` (and other services) emits evidence records here. These records are append-only, provenance-first, and auditable without storing raw secrets or credentials.

## Evidence record types (v0.1)

| Record type | Description |
|---|---|
| `OperationEvidenceRecord` | Operation lifecycle events: create, start, progress, failure, retry, cancel, complete, compensate |
| `OperationEventLedgerEntry` | Immutable ledger wrapper for `OperationEvent` objects emitted by the runtime |
| `ArtifactAdmissionEvidence` | Artifact admission gate results and final admission state |
| `PolicyGateEvidence` | Policy gate evaluation results, overrides, and remediation paths |
| `DecisionEvidence` | Decision card resolutions with responsible actor and selected option |
| `AgentActionEvidence` | Agent actions recorded with delegated authority and scope |
| `DiagnosticExportEvidence` | Diagnostic export confirmation — redaction applied, no raw credentials stored |
| `CompensationEvidence` | Compensation actions taken against failed or canceled operations |
| `ReleaseOperationEvidence` | Release operation evidence with artifact list and source reference |

## Required properties (all record types)

- `schema_version` (always `"0.1.0"`)
- `operation_id`
- `actor` (`actor_type`, `actor_id`)
- `delegated_by` (where applicable — required for `AgentActionEvidence`)
- `command` (the operation command or event that produced this evidence)
- `result` (one of: `success`, `failure`, `partial`, `skipped`, `canceled`, `compensated`, `pending`)
- `timestamp` / `occurred_at` / `recorded_at`
- `source_service` (repo or service that emitted the record, e.g. `SocioProphet/prophet-platform`)
- `trace_id` / `span_id` (optional but recommended for distributed tracing)
- `task_id`, `artifact_id`, `policy_gate_id` where applicable

## Acceptance criteria

- Evidence records represent operation create/start/progress/failure/retry/cancel/complete/compensate. ✓
- Agent actions are recorded with delegated authority and scope. ✓
- Policy gates and override decisions are recorded with responsible actor and remediation path. ✓
- Diagnostic export evidence confirms redaction was applied without storing raw secrets. ✓
- Ledger schema aligns with `SocioProphet/prophet-core-contracts#1`. ✓

## Schema

- `schemas/operation-evidence.schema.json` — JSON Schema (draft 2020-12) for all nine record types

## Examples

- `examples/operation-evidence/operation-lifecycle.json` — `OperationEvidenceRecord` create/start/progress/complete
- `examples/operation-evidence/operation-retry.json` — `OperationEvidenceRecord` failure/retry/complete
- `examples/operation-evidence/operation-cancel.json` — `OperationEvidenceRecord` cancel + `CompensationEvidence`
- `examples/operation-evidence/operation-event-ledger.json` — `OperationEventLedgerEntry` records
- `examples/operation-evidence/artifact-admission.json` — `ArtifactAdmissionEvidence` (admitted + quarantined)
- `examples/operation-evidence/policy-gate.json` — `PolicyGateEvidence` (blocking, override, passed)
- `examples/operation-evidence/decision.json` — `DecisionEvidence` (admit and reject)
- `examples/operation-evidence/agent-action.json` — `AgentActionEvidence` (with `delegated_by`)
- `examples/operation-evidence/diagnostic-export.json` — `DiagnosticExportEvidence` (redacted)
- `examples/operation-evidence/compensation.json` — `CompensationEvidence` (rollback, reverse_artifact)
- `examples/operation-evidence/release-operation.json` — `ReleaseOperationEvidence`

## Validation

```bash
make validate
```

The validator (`tools/validate_operation_evidence_examples.py`) checks:

- `schema_version` is `"0.1.0"` for every record.
- Required identifier fields are present per record type.
- `DiagnosticExportEvidence`: `redaction_applied` is `true` and `contains_raw_credentials` is `false`.
- `AgentActionEvidence`: `delegated_by` is present.
- Blocking/requires-decision/requires-admin `PolicyGateEvidence`: `responsible_actor` and `remediation_path` are present.
- `ArtifactAdmissionEvidence`: `gate_results` is a non-empty list with required fields.
- `CompensationEvidence`: `compensated_task_ids` is a non-empty list.
- `ReleaseOperationEvidence`: `release_artifact_ids` is a non-empty list.

## Repository boundaries

This repository owns ledger schemas, evidence record definitions, and conformance examples.

It does **not** own operation runtime logic, policy execution engines, or agent execution.

Integration ownership:

- Runtime emitter: `SocioProphet/prophet-platform`
- Policy evaluation: `SocioProphet/policy-fabric`
- Agent actions: `SocioProphet/agentplane`
- Contracts vocabulary: `SocioProphet/prophet-core-contracts`
