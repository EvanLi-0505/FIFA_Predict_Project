"""Database abstraction layer shared by the Web and Desktop backends.

Development Prompt.md Section 10 requires that business logic never contain
SQL specific to one database engine, and that Web (MySQL) and Desktop
(SQLite) share the same repository/service abstraction. This package
achieves that with a single SQLAlchemy ORM model set and repository
implementation, parameterised only by the SQLAlchemy connection URL passed
to `database.engine.create_db_engine`. No dialect-specific SQL or column
types are used anywhere in this package — everything goes through the ORM,
so the exact same code path runs against MySQL and SQLite.

Design decision (documented here rather than silently, per Development
Prompt.md Section 44): the conceptual `matches` and `teams` tables sketched
in Section 35 are NOT implemented as database tables. Match-level data
(tens of thousands of rows per dataset version) stays on disk as CSV under
`datasets/`, exactly like the built-in dataset, and is read directly by
`core.dataset.io` / `core.pipeline` — this is dramatically faster than
row-by-row ORM access for the pandas-based feature engineering pipeline,
and avoids duplicating the same match data in two places. The database only
stores dataset/model/prediction METADATA:
    datasets        - one row per dataset version (builtin or uploaded)
    model_versions  - one row per trained model artifact
    predictions     - prediction history
"""
