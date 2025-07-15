import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

project = 'abtest-tool'
author = 'Nhimphu'
release = '1.0.1'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'myst_parser',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'alabaster'
html_static_path = ['_static']
