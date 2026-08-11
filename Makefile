.PHONY: install test lint format format-check verify api ui demo-eval retrieval-eval

install:
	python -m pip install -e ".[ui,dev]"

test:
	pytest -v

lint:
	ruff check app src tests scripts

format-check:
	ruff format --check app src tests scripts

format:
	ruff check app src tests scripts --fix
	ruff format app src tests scripts

verify:
	python scripts/setup_chinook.py
	queryguard-verify

api:
	uvicorn queryguard.api.main:app --reload

ui:
	streamlit run app/streamlit_app.py

demo-eval:
	python scripts/run_demo_evaluation.py

retrieval-eval:
	python scripts/evaluate_retrieval.py
