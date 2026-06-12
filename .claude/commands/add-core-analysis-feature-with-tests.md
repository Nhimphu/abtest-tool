---
name: add-core-analysis-feature-with-tests
description: Workflow command scaffold for add-core-analysis-feature-with-tests in abtest-tool.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /add-core-analysis-feature-with-tests

Use this workflow when working on **add-core-analysis-feature-with-tests** in `abtest-tool`.

## Goal

Implements a new statistical analysis feature or engine in the abtest_core, integrates it into the engine, and adds corresponding tests.

## Common Files

- `src/abtest_core/engine.py`
- `src/abtest_core/types.py`
- `src/abtest_core/*.py`
- `tests/test_*.py`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Create or update a module in src/abtest_core (e.g., bayes.py, multiple.py, sequential.py, cuped.py, stats_binomial.py, stats_continuous.py, stats_ratio.py)
- Update src/abtest_core/engine.py to integrate the new method
- Update src/abtest_core/types.py if new types or results are needed
- Add or update a test file in tests/ (e.g., tests/test_bayes_core.py, tests/test_multiple.py, tests/test_sequential.py, tests/test_cuped.py, tests/test_stats_binomial.py, etc.)

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.