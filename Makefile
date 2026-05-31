.PHONY: release test

release:
	python -m biophysevo.export_release \
		--input data/release/biophys_bridge_evo_cases.jsonl \
		--out-dir data/release \
		--min-quality-score 0.8
	python -m biophysevo.evaluation.run_agent_eval \
		--input data/release/biophys_bridge_evo_cases.jsonl \
		--model lexical_baseline \
		--run-dir runs/$$(date +%Y-%m-%d_%H%M%S)_agent_eval_lexical_baseline

test:
	pytest
