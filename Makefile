.PHONY: run test
run:
	python -u src/urdu_exec_bot/app.py

test:
	pytest -q
