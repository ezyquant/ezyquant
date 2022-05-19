.PHONY: install
install:
	pip install -U -r requirements.txt

.PHONY: test
test:
	pytest

.PHONY: format
format:
	isort . --skip-gitignore
	black .

	docformatter -i ezyquant/reader.py
	docformatter -i ezyquant/creator.py

.PHONY: pdoc
pdoc:
	pdoc --docformat numpy ezyquant

.PHONY: mkdocs
mkdocs:
	mkdocs serve
