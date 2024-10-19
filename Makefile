venv:
	python3.11 -m venv .venv
	. ./.venv/bin/activate && pip install -r requirements.txt

run_bigchat: venv
	cd big_chat && uvicorn main:app --port 8267

run_ourapi: venv
	cd our_api && uvicorn main:app --port 8266

run_integration: venv
	PYTHONPATH=$(shell pwd) python3.11 integration/main.py

tests: venv
	PYTHONPATH=$(shell pwd) pytest tests