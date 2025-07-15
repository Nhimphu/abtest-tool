from pathlib import Path
from setuptools import setup

version: dict = {}
with open(Path(__file__).parent / "src" / "__init__.py", "r", encoding="utf-8") as f:
    exec(f.read(), version)

setup(
    name="abtest-tool",
    version=version["__version__"],
    py_modules=["cli"],
    package_dir={"": "src"},
    entry_points={"console_scripts": ["abtest-tool=cli:main"]},
)
