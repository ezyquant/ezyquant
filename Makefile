.PHONY: install
install:
	pip install .
	pip uninstall ezyquant

.PHONY: test
test:
	pip install pytest
	pytest

.PHONY: format
format:
	isort . --skip-gitignore
	black .

	docformatter -i ezyquant/reader.py
	docformatter -i ezyquant/creator.py

.PHONY: docs
docs:
	pdoc --docformat numpy ezyquant

.PHONY: mkdocs
mkdocs:
	pip install mkdocs mkdocs-material
	mkdocs serve
