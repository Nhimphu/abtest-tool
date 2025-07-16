import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

project = 'abtest-tool'
author = 'Nhimphu'
release = '1.0.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'myst_parser',
]

# Allow including Markdown files and parsing ``include`` directives correctly
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# Mock heavy optional dependencies so autodoc can run without them
autodoc_mock_imports = ['scipy']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'alabaster'
html_static_path = ['_static']
