.PHONY: install
install:
	pip install -U -r requirements.txt

.PHONY: test
test:
	pytest

.PHONY: format
format:
	isort .
	black .

	docformatter -i ezyquant/reader.py
	docformatter -i ezyquant/creator.py
	docformatter -i ezyquant/indicators.py
	docformatter -i ezyquant/report.py
	docformatter -i ezyquant/backtest/backtest.py
	docformatter -i ezyquant/backtest/account.py

.PHONY: venv
venv:
	python -m venv venv

.PHONY: pdoc
pdoc:
	pdoc --docformat numpy ezyquant

.PHONY: mkdocs
mkdocs:
	mkdocs serve
