import os
import sys
sys.path.insert(0, os.path.abspath('../../'))
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'IIGM Ionogram tools'
copyright = '2025, Vimal'
author = 'Vimal'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'numpydoc',
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
html_theme_options={
    'navbar_start': ['navbar-logo'],
    'navbar_center': ['custom-center-spacer'],
    'navbar_end': ['theme-switcher']
}

html_static_path = ['_static']
html_sidebars = {
    "**": ['sidebar-nav-bs'],
    "manualdoc/guitutorial": []
}
