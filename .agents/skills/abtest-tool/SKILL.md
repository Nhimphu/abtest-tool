```markdown
# abtest-tool Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches you how to contribute to the `abtest-tool` Python codebase, a toolkit for A/B testing statistical analysis. You'll learn the project's coding conventions, how to add new statistical features, update packaging and CI workflows, implement new user-facing features, and perform codebase refactoring. The guide covers file organization, commit styles, and common development workflows with practical examples and suggested commands.

## Coding Conventions

- **Language:** Python (no external framework detected)
- **File Naming:** Use `snake_case` for all Python files.
  - Example: `stats_binomial.py`, `test_multiple.py`
- **Import Style:** Prefer **relative imports** within packages.
  - Example:
    ```python
    from .stats_binomial import binomial_test
    ```
- **Export Style:** Use **named exports** (explicitly define what is exported).
  - Example:
    ```python
    __all__ = ["binomial_test", "BinomialResult"]
    ```
- **Commit Patterns:**
  - Use prefixes like `chore:`, `fix:`, `feat:` in commit messages.
  - Keep commit messages concise (average ~55 characters).
- **Directory Structure:**
  - Core logic: `src/abtest_core/`
  - API: `src/api/`
  - UI: `src/ui/`
  - Tests: `tests/`
  - Packaging/config: `pyproject.toml`, `.github/workflows/`

## Workflows

### Add Core Analysis Feature with Tests
**Trigger:** When you want to add a new statistical method or analysis capability to the core engine.  
**Command:** `/add-core-analysis-feature`

1. Create or update a module in `src/abtest_core/` (e.g., `bayes.py`, `stats_binomial.py`).
2. Update `src/abtest_core/engine.py` to integrate the new method.
3. Update `src/abtest_core/types.py` if new types or results are needed.
4. Add or update a test file in `tests/` (e.g., `tests/test_bayes_core.py`).

**Example:**
```python
# src/abtest_core/stats_binomial.py
def binomial_test(...):
    ...

# src/abtest_core/engine.py
from .stats_binomial import binomial_test
# integrate in engine logic

# tests/test_stats_binomial.py
from abtest_core.stats_binomial import binomial_test
def test_binomial_test():
    ...
```

---

### Add or Update pyproject.toml for Packaging or Tooling
**Trigger:** When you need to change packaging, dependency management, or dev tooling configuration.  
**Command:** `/update-pyproject`

1. Edit `pyproject.toml` to update packages, resources, or dev tools.
2. Optionally, add/remove `__init__.py` stubs or adjust `src/` structure.

**Example:**
```toml
# pyproject.toml
[tool.poetry.dependencies]
numpy = "^1.24"
```

---

### CI Workflow Update
**Trigger:** When you want to improve or fix CI/CD pipelines.  
**Command:** `/update-ci`

1. Edit `.github/workflows/*.yml` files (e.g., `ci.yml`, `docs.yml`).
2. Optionally, update `pyproject.toml` or scripts used in CI.
3. Commit changes to workflow and config files.

**Example:**
```yaml
# .github/workflows/ci.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
```

---

### Implement Feature with Test and UI Integration
**Trigger:** When you want to add a user-facing feature that requires changes across core, API, and UI.  
**Command:** `/add-feature-ui`

1. Add or update logic in `src/abtest_core/*.py` and/or `src/api/*.py`.
2. Update `src/ui/ui_mainwindow.py` or other UI modules for integration.
3. Update or add tests in `tests/` (e.g., `test_logic.py`, `test_ui_exports.py`).

**Example:**
```python
# src/abtest_core/new_feature.py
def new_analysis(...):
    ...

# src/ui/ui_mainwindow.py
from abtest_core.new_feature import new_analysis
# integrate into UI actions

# tests/test_logic.py
def test_new_analysis():
    ...
```

---

### Refactor or Cleanup Core and UI
**Trigger:** When you want to improve code quality, remove unused code, or fix import/type issues.  
**Command:** `/refactor`

1. Edit multiple files in `src/abtest_core/`, `src/ui/`, and/or `tests/` to clean up code or fix imports/types.
2. Update `pyproject.toml` or config files if needed.
3. Remove or rename obsolete modules.

**Example:**
```python
# src/abtest_core/engine.py
# Remove unused imports and unify type annotations
```

## Testing Patterns

- **Framework:** Unknown (not explicitly detected).
- **Test File Naming:** Use `test_*.py` for Python tests (e.g., `test_bayes_core.py`).
- **Location:** Place tests in the `tests/` directory.
- **Style:** Standard Python test functions (likely using `pytest` or `unittest`).
- **Example:**
  ```python
  # tests/test_stats_binomial.py
  def test_binomial_test():
      result = binomial_test(...)
      assert result.p_value < 0.05
  ```

## Commands

| Command                      | Purpose                                                        |
|------------------------------|----------------------------------------------------------------|
| /add-core-analysis-feature    | Add a new statistical method to the core engine with tests     |
| /update-pyproject            | Update packaging, dependencies, or dev tooling                 |
| /update-ci                   | Update or fix CI/CD workflows                                  |
| /add-feature-ui              | Add a user-facing feature with core, API, UI, and tests        |
| /refactor                    | Refactor or clean up codebase-wide (core, UI, types, imports)  |
```
