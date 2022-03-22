.PHONY: install
install:
	pip install -r requirements.txt

.PHONY: test
test:
	pytest

.PHONY: format
format:
	isort .
	black .

	docformatter -i ezyquant/reader.py

.PHONY: docs
docs:
	pdoc --docformat numpy ezyquant
