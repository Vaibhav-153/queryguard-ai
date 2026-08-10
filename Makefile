.PHONY: install install-all test lint api ui demo-eval setup-data docker

install:
	python -m pip install -e ".[dev]"

install-all:
	python -m pip install -e ".[all]"

setup-data:
	python scripts/setup_chinook.py

test:
	pytest

lint:
	ruff check src tests scripts

api:
	uvicorn queryguard.api.main:app --reload --port 8000

ui:
	streamlit run app/streamlit_app.py

demo-eval:
	python -m queryguard.evaluation.runner --provider demo --max-examples 6

docker:
	docker compose up --build
