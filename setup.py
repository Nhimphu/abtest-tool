from setuptools import setup

setup(
    name="abtest-tool",
    version="0.1.0",
    py_modules=["cli"],
    package_dir={"": "src"},
    entry_points={"console_scripts": ["abtest-tool=cli:main"]},
)
