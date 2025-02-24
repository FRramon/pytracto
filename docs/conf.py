# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
import pydata_sphinx_theme
sys.path.insert(0, os.path.abspath(os.path.join('..', 'pytracto')))

project = 'pytracto'
copyright = '2024, Francois Ramon'
author = 'Francois Ramon'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration


templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon','myst_parser','sphinx_copybutton','nbsphinx','sphinx_design']

source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'markdown',
    '.md': 'markdown',
}

nbsphinx_allow_errors = True
# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

#html_theme = 'sphinx_rtd_theme'
html_theme = 'pydata_sphinx_theme'

html_static_path = ["_static"]
html_extra_path = ['tutorial']
html_css_files = [
    "custom.css",
]
# html_theme_options = {
#     # Options specific to pydata_sphinx_theme
#     "github_url": "https://github.com/FRramon/pytracto",
# }
