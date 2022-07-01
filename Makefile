.PHONY: install
install:
	pip install -U -r requirements-dev.txt

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
	docformatter -i ezyquant/utils.py
	docformatter -i ezyquant/backtest/_backtest.py
	docformatter -i ezyquant/backtest/backtest.py
	docformatter -i ezyquant/backtest/account.py

.PHONY: venv
venv:
	python -m venv venv

.PHONY: sphinx
sphinx:
	rm -r docs/build
	sphinx-apidoc -f -o docs/source/reference ezyquant
	sphinx-build -b html docs/source/ docs/build/html