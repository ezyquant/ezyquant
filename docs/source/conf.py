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
from datetime import datetime

import sphinx_material

sys.path.insert(0, os.path.abspath("../.."))


# -- Project information -----------------------------------------------------

project = "Ezyquant"
author = "Thailand Capital Market Development Fund"
copyright = f"2022-{datetime.now().year}, {author}"
release = "0.1.2"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

autoclass_content = "init"
autodoc_default_options = {
    "member-order": "bysource",
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

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named 'default.css' will overwrite the builtin 'default.css'.
html_static_path = ["_static"]

# -- HTML theme settings ------------------------------------------------

html_show_sourcelink = False
html_sidebars = {
    "**": ["logo-text.html", "globaltoc.html", "localtoc.html", "searchbox.html"]
}

extensions.append("sphinx_material")
html_theme_path = sphinx_material.html_theme_path()
html_context = sphinx_material.get_html_context()
html_theme = "sphinx_material"

# material theme options (see theme.conf for more information)
html_theme_options = {
    # "base_url": "http://bashtage.github.io/sphinx-material/",
    "repo_url": "https://github.com/ezyquant/ezyquant",
    "repo_name": project,
    # "google_analytics_account": "UA-XXXXX",
    "html_minify": False,
    "html_prettify": True,
    "css_minify": True,
    # "logo_icon": "&#xe869",
    "repo_type": "github",
    "globaltoc_depth": -1,
    "globaltoc_collapse": True,
    "color_primary": "blue",
    "color_accent": "cyan",
    "theme_color": "#2196f3",
    # "master_doc": False,
    "nav_links": [
        # {"href": "index", "internal": True, "title": "Ezyquant"},
        {"href": "get_started", "internal": True, "title": "Get Started"},
        {"href": "user_guide/setup", "internal": True, "title": "User Guide"},
        {"href": "reference/ezyquant", "internal": True, "title": "API Reference"},
    ],
    # "heroes": {
    #     "index": "A responsive Material Design theme for Sphinx sites.",
    #     "customization": "Configuration options to personalize your site.",
    # },
    "table_classes": ["plain"],
}

language = "en"

todo_include_todos = True
# html_logo = "_static/ezyquant.png"
# html_favicon = "_static/ezyquant.png"

html_use_index = True
html_domain_indices = True
