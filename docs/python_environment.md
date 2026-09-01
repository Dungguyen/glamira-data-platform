# Python Environment Validation

## Purpose

This document validates the reproducible Python development environment for
the Glamira Data Engineering project.

## Tooling

Package and environment manager:

`uv`

Python version:

`3.12.13`

Project environment:

`.venv`

## Dependency Management

The project uses:

- `pyproject.toml` for project metadata and dependency declarations
- `uv.lock` for reproducible dependency resolution
- `.python-version` for Python version selection
- `.venv` for the local virtual environment

The virtual environment is excluded from Git.

## Current Dependency Tree

```text
glamira-data-platform
└── pymongo 4.17.0
    └── dnspython 2.8.0