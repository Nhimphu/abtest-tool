import os
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

project = 'abtest-tool'
author = 'Nhimphu'
release = '1.0.0'

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
]

# Allow including Markdown files and parsing ``include`` directives correctly
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# Mock heavy optional dependencies so autodoc can run without them
autodoc_mock_imports = [
    "numpy",
    "pandas",
    "scipy",
    "matplotlib",
    "PySide6",
    "sklearn",
    "sqlalchemy",
    "uvicorn",
    "gunicorn",
    "logic",
]

autodoc_typehints = "description"
autodoc_member_order = "bysource"
napoleon_google_docstring = True
napoleon_use_param = True

myst_enable_extensions = []
myst_heading_anchors = 0

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'alabaster'
html_static_path = ['_static']
