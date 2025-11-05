.PHONY: run test lint watch

run:
	python main_minimal.py

test:
	python -m pytest -v

lint:
	ruff check .
	ruff format --check .

watch:
	python -m pip install watchdog
	watchmedo shell-command --patterns="*.py" --recursive --command="pytest -xvs" .