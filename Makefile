.PHONY: validate validate-decision-world-signals validate-operation-evidence validate-wallguard-ledger

validate: validate-decision-world-signals validate-operation-evidence validate-wallguard-ledger

validate-decision-world-signals:
	python3 tools/validate_decision_world_signal_ledger.py

validate-operation-evidence:
	python3 tools/validate_operation_evidence_examples.py

validate-wallguard-ledger:
	python3 tools/validate_wallguard_ledger_examples.py
