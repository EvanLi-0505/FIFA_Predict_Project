"""Shared ML/business core for the FIFA World Cup prediction system.

This package is the single source of truth for data cleaning, feature
engineering, model training, and prediction. Both the Web backend (FastAPI +
MySQL) and the Desktop backend (bundled FastAPI + SQLite) import from here.
No web framework or database driver code may live in this package.
"""
