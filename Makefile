.PHONY: install
install:
	pip install -U -r requirements-dev.txt

.PHONY: test
test:
	coverage run -m pytest

.PHONY: format
format:
	black .
	docformatter -i -r .
	ruff check --fix .

.PHONY: sphinx
sphinx:
	sphinx-build -b html docs/source/ docs/build/html

.PHONY: s3
s3:
	aws s3 sync ./docs/build/html s3://eazyquant-nonprod --delete