.PHONY: install
install:
	pip install -U -r requirements-dev.txt

.PHONY: test
test:
	pytest

.PHONY: format
format:
	autoflake -i \
	--expand-star-imports \
	--remove-all-unused-imports \
	--ignore-init-module-imports \
	--remove-duplicate-keys \
	--remove-unused-variables \
	--exclude venv \
	-r .

	isort .
	black .
	docformatter -i --black -e venv -r .

.PHONY: venv
venv:
	python -m venv venv

.PHONY: sphinx
sphinx:
	sphinx-build -b html docs/source/ docs/build/html

.PHONY: s3
s3:
	aws s3 sync ./docs/build/html s3://eazyquant-nonprod --delete