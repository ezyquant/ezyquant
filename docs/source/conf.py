# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

from datetime import datetime

# -- Project information -----------------------------------------------------

project = "Ezyquant"
author = "Thailand Capital Market Development Fund (CMDF)"
copyright = f"2022-{datetime.now().year}, {author}"
release = "0.1.6"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autosummary",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    # "sphinx_thebe",
]

autosummary_generate = True

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
html_theme = "sphinx_book_theme"
# html_logo = "_static/ezyquant.svg"
html_title = project
html_copy_source = True
html_sourcelink_suffix = ""
# html_favicon = "_static/ezyquant.svg"
html_last_updated_fmt = ""

html_sidebars = {
    "**": [
        "sidebar-logo.html",
        "search-field.html",
        # "postcard.html",
        # "recentposts.html",
        # "tagcloud.html",
        # "categories.html",
        # "archives.html",
        "sbt-sidebar-nav.html",
    ]
}
# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
# html_css_files = ["custom.css"]
# jupyter_execute_notebooks = "cache"

html_theme_options = {
    "path_to_docs": "docs",
    "repository_url": "https://github.com/ezyquant/ezyquant",
    # "launch_buttons": {
    #     "binderhub_url": "https://mybinder.org",
    #     "colab_url": "https://colab.research.google.com/",
    #     "deepnote_url": "https://deepnote.com/",
    #     "notebook_interface": "jupyterlab",
    #     "thebe": True,
    # },
    "use_issues_button": True,
    "use_repository_button": True,
    "use_download_button": True,
    "use_sidenotes": True,
}

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
