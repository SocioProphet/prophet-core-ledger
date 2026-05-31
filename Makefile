.PHONY: validate validate-operation-evidence validate-wallguard-ledger

validate: validate-operation-evidence validate-wallguard-ledger

validate-operation-evidence:
	python3 tools/validate_operation_evidence_examples.py

validate-wallguard-ledger:
	python3 tools/validate_wallguard_ledger_examples.py
