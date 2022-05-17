.PHONY: install
install:
	pip install .
	pip uninstall ezyquant

.PHONY: test
test:
	pip install pytest --upgrade
	pytest

.PHONY: format
format:
	isort .
	black .

	docformatter -i ezyquant/reader.py

.PHONY: pdoc
pdoc:
	pip install pdoc --upgrade
	pdoc --docformat numpy ezyquant

.PHONY: mkdocs
mkdocs:
	pip install mkdocs mkdocs-material --upgrade
	mkdocs serve
