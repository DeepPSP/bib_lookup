# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

import sys
from pathlib import Path

import sphinx_rtd_theme

try:
    import stanford_theme
except Exception:
    stanford_theme = None

import recommonmark  # noqa: F401
from recommonmark.transform import AutoStructify


project_root = Path(__file__).resolve().parents[2]
src_root = project_root / "bib_lookup"
docs_root = Path(__file__).resolve().parents[0]

sys.path.insert(0, str(project_root))


# -- Project information -----------------------------------------------------

project = "bib-lookup"
copyright = "2023, WEN Hao"
author = "WEN Hao"

# The full version, including alpha/beta/rc tags
release = Path(src_root / "version.py").read_text().split("=")[1].strip()[1:-1]

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "nbsphinx",
    "recommonmark",
    # 'sphinx.ext.autosectionlabel',
    "sphinx_multiversion",
    "sphinx_toolbox.collapse",
    # "numpydoc",
    "sphinxcontrib.tikz",
    "sphinxcontrib.pseudocode",
    "sphinxcontrib.bibtex",
    "sphinxcontrib.proof",
]

# bibtex_bibfiles = ["references.bib"]
# bibtex_bibliography_header = ".. rubric:: 参考文献"
bibtex_bibliography_header = ".. rubric:: References"
bibtex_footbibliography_header = bibtex_bibliography_header

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "np": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable/", None),
    "pd": ("https://pandas.pydata.org/pandas-docs/stable/", None),
}

autodoc_default_options = {
    "show-inheritance": True,
}

html_context = {
    "display_github": True,  # Integrate GitHub
    "github_user": "wenh06",  # Username
    "github_repo": "fl-sim",  # Repo name
    "github_version": "master",  # Version
    "conf_py_path": "/docs/source/",  # Path in the checkout to the docs root
}

html_sidebars = {"*": ["versions.html"]}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# Napoleon settings
napoleon_custom_sections = [
    "ABOUT",
    "ISSUES",
    "Usage",
    "Citation",
    "TODO",
    "Version history",
    "Pipeline",
]
# napoleon_custom_section_rename = False # True is default for backwards compatibility.


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = "alabaster"

if stanford_theme:
    html_theme = "stanford_theme"
    html_theme_path = [stanford_theme.get_html_theme_path()]
else:
    html_theme = "sphinx_rtd_theme"
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
# htmlhelp_basename = "Recommonmarkdoc"

html_theme_options = {
    "collapse_navigation": False,
    "display_version": True,
}


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

master_doc = "index"

numfig = False


linkcheck_ignore = [
    r"https://doi.org/*",  # 418 Client Error
]


def setup(app):
    app.add_config_value(
        "recommonmark_config",
        {
            "url_resolver": lambda url: github_doc_root + url,  # noqa: F821
            "auto_toc_tree_section": "Contents",
        },
        True,
    )
    app.add_transform(AutoStructify)
    app.add_css_file("css/custom.css")
