# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- Nothing yet

## [1.0.0] - 2025-07-15
### Added
- CLI tool for running A/B analyses from JSON data
- Flask APIs with JWT authentication and Prometheus metrics
- SQLite-backed feature flag store and API endpoints
- Bandit helpers and sequential analysis utilities
- PyQt6 GUI with history panel and plugin support

### Changed
- Switched project to Poetry for dependency management

### Fixed
- CUPED adjustment handles zero-variance covariate correctly
- `compute_custom_metric` rejects dangerous expressions
