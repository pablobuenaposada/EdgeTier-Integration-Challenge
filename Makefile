venv:
	python3.11 -m venv .venv
	. ./.venv/bin/activate && pip install -r requirements.txt

run:
	PYTHONPATH=$(shell pwd) python3.11 integration/main.py

tests: venv
	PYTHONPATH=$(shell pwd) pytest tests