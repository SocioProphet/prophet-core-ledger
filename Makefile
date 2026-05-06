.PHONY: validate validate-decision-world-signals

validate: validate-decision-world-signals

validate-decision-world-signals:
	python3 tools/validate_decision_world_signal_ledger.py
