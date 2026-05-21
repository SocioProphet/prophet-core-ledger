.PHONY: validate validate-operation-evidence

validate: validate-operation-evidence

validate-operation-evidence:
	python3 tools/validate_operation_evidence_examples.py
