venv:
	python3.11 -m venv .venv
	. ./.venv/bin/activate && pip install -r requirements.txt

tests: venv
	PYTHONPATH=$(shell pwd) pytest tests