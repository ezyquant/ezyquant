# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

from datetime import datetime  # noqa: E402

import ezyquant as ez  # noqa: E402

# -- Project information -----------------------------------------------------

project = "EzyQuant"
author = "Fintech (Thailand) Company Limited"
copyright = f"2022-{datetime.now().year}, Thailand Capital Market Development Fund (CMDF)"  # noqa: A001
release = ez.__version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autosummary",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

autosummary_generate = True

autoclass_content = "init"
autodoc_default_options = {
    "member-order": "bysource",
    "undoc-members": True,
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_book_theme"
html_logo = "_static/logo-text-right.svg"
html_title = project
html_copy_source = True
html_favicon = "_static/logo.svg"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_css_files = ["css/custom.css"]

html_theme_options = {
    "path_to_docs": "docs",
    "repository_url": "https://github.com/ezyquant/ezyquant",
    "use_issues_button": True,
    "use_repository_button": True,
    "use_download_button": True,
    "use_sidenotes": True,
    "use_fullscreen_button": False,
    "show_navbar_depth": 2,
}
