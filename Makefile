PYTHON ?= python3

.PHONY: run test test-json validate-rules smoke

run:
	@$(PYTHON) main.py

test:
	@$(PYTHON) tests/run_all.py

test-json:
	@$(PYTHON) tests/run_all.py --json --output tests/test_report.json

validate-rules:
	@$(PYTHON) tests/test_rule_validation.py

smoke:
	@echo '{"hook_event_name":"SessionStart","session_id":"local-smoke","transcript_path":"/tmp/local-smoke.jsonl","cwd":"/tmp"}' | $(PYTHON) main.py
