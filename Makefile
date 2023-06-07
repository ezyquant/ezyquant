.PHONY: install
install:
# Fix zigzag
	pip install -U Cython numpy wheel
	pip install -U -r requirements-dev.txt

.PHONY: test
test:
	pytest

.PHONY: format
format:
	autoflake -i --remove-all-unused-imports --ignore-init-module-imports --expand-star-imports --exclude venv -r .
	isort .
	black .

	docformatter -i ezyquant/reader.py
	docformatter -i ezyquant/creator.py
	docformatter -i ezyquant/indicators.py
	docformatter -i ezyquant/report.py
	docformatter -i ezyquant/utils.py
	docformatter -i ezyquant/backtesting/_backtesting.py
	docformatter -i ezyquant/backtesting/backtesting.py
	docformatter -i ezyquant/backtesting/account.py

.PHONY: venv
venv:
	python -m venv venv

.PHONY: sphinx
sphinx:
	sphinx-build -b html docs/source/ docs/build/html

.PHONY: s3
s3:
	aws s3 sync ./docs/build/html s3://eazyquant-nonprod --delete