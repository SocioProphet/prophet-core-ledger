# Decision-Grade World Signal Ledger v0.1

This module defines the first append-only ledger surface for GAIA decision-grade world signals.

## Purpose

The ledger records evidence and promotion decisions for world signals before those signals become operationally usable by GAIA, MLOps, agent systems, or policy-constrained actions.

Core invariant:

> Observed signal does not equal canonical truth. Every operationally usable fact must pass through contract validation, ledgering, policy evaluation, and promotion/review/rejection state.

## Entry families

### 1. Feature promotion event

Records that a feature registry entry has passed contract validation or has been blocked/review-gated.

Required semantics:

- feature ID
- source artifact hash
- contract/schema reference
- policy ID
- promotion state
- responsible actor
- replay instructions

### 2. Energy ledger event

Records candidate ambiguity and promotion barriers for extraction or entity-resolution outputs.

Required semantics:

- source artifact ID
- extraction run ID
- candidate set ID
- top candidate and score
- runner-up candidate and score
- margin delta
- perturbation flip rate
- promotion decision
- decision reason codes

### 3. Decision ledger event

Records policy-governed decisions such as match, merge, split, feature promotion, action admission, or policy block.

Required semantics:

- decision ID
- decision type
- policy ID
- input artifact hashes
- candidates
- selected ID/value
- rule trace
- confidence
- responsible actor
- replay instructions

### 4. Proof artifact event

Records a replayable proof or validation claim used by policy, security, or action admission.

Required semantics:

- claim name and version
- input hashes
- analyzer name/version
- analysis domains
- budgets
- result status
- witness or violation evidence
- replay instructions

## Append-only model

Ledger entries are immutable observations. Corrections are represented as new entries that supersede, reject, or amend prior entries. Consumers must never mutate historical ledger entries in place.

## Promotion states

- `EVIDENCE_ONLY` — may be cited as evidence but not used as canonical state.
- `REVIEW` — requires human or policy steward review.
- `REJECTED` — explicitly rejected for operational use.
- `PROMOTED` — admitted for canonical or operational use under the referenced policy.

## Replay requirement

Every entry must include enough information to replay or re-evaluate the decision path, including hashes, policy IDs, run IDs, and responsible actor identifiers.

## Related surfaces

- `SocioProphet/prophet-core-contracts#3` — JSON Schema contracts.
- `SocioProphet/prophet-domain-gaia-ontology#1` — RDF/SHACL ontology concepts.
- `SocioProphet/gaia-world-model#20` — cross-repo tracker.
