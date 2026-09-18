"""Database schema management.

Replaces Alembic for this project. Run it from the backend/ directory:

    python -m scripts.db status
    python -m scripts.db create
    python -m scripts.db reset --yes

WHAT THIS CAN AND CANNOT DO
---------------------------
`create` calls SQLAlchemy's metadata.create_all(), which issues CREATE TABLE
for every table that does not exist yet. It is NOT a migration tool:

    adding a new model          -> `create` picks it up
    adding a column to a model  -> `create` does NOTHING (the table exists)
    renaming or dropping a column -> `create` does NOTHING

When you change an existing model you have two options:
  1. `reset --yes`   - drop everything and rebuild. Destroys all data.
                       Fine while developing; never on data you care about.
  2. write the ALTER TABLE yourself and run it with `python -m scripts.db sql`.

The schema is defined in app/models/*.py. That is the single source of truth -
this script only applies it.
"""

import argparse
import sys

from sqlalchemy import inspect, text

from app.core.config import settings
from app.db.database import Base, engine

# Registers User, Conversation and Message on Base.metadata.
# Without this import the metadata is empty and `create` would silently
# create nothing at all.
import app.models  # noqa: F401


def _target() -> str:
    """Human-readable description of which database we are about to touch."""
    return f"{settings.POSTGRES_DB} on {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}"


def cmd_status(_args: argparse.Namespace) -> int:
    """Show what the models declare vs. what the database actually has."""
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    declared = [t.name for t in Base.metadata.sorted_tables]

    print(f"Database: {_target()}\n")

    for name in declared:
        if name not in existing:
            print(f"  [MISSING] {name}")
            continue

        db_columns = {c["name"] for c in inspector.get_columns(name)}
        model_columns = {c.name for c in Base.metadata.tables[name].columns}

        # A column in the model but not the database is the exact case
        # `create` cannot fix - surface it loudly rather than let it confuse
        # you as a runtime error later.
        missing = model_columns - db_columns
        extra = db_columns - model_columns
        row_count = engine.connect().execute(text(f'SELECT count(*) FROM "{name}"')).scalar()

        flag = "OK     " if not (missing or extra) else "DRIFT  "
        print(f"  [{flag}] {name:<15} {len(db_columns):>2} columns, {row_count:>4} rows")
        if missing:
            print(f"             model has columns the table lacks: {sorted(missing)}")
            print("             -> run `reset --yes`, or ALTER TABLE by hand")
        if extra:
            print(f"             table has columns the model lacks: {sorted(extra)}")

    unmanaged = existing - set(declared)
    if unmanaged:
        print(f"\n  Tables not described by any model: {sorted(unmanaged)}")

    return 0


def cmd_create(_args: argparse.Namespace) -> int:
    """Create every table that does not exist yet. Safe to re-run."""
    before = set(inspect(engine).get_table_names())
    Base.metadata.create_all(bind=engine)
    after = set(inspect(engine).get_table_names())

    created = sorted(after - before)
    if created:
        print(f"Created on {_target()}: {', '.join(created)}")
    else:
        print(f"Nothing to create on {_target()} - all tables already exist.")
    print("\nNote: existing tables were left untouched, including any that have")
    print("drifted from their model. Run `status` to check.")
    return 0


def cmd_drop(args: argparse.Namespace) -> int:
    """Drop every table this project manages. Destroys all data."""
    if not _confirm(args, "DROP every table (all data will be lost)"):
        return 1

    # Reverse dependency order: messages before conversations before users,
    # so no foreign key is left pointing at a table that is already gone.
    Base.metadata.drop_all(bind=engine)
    print(f"Dropped all project tables on {_target()}.")
    return 0


def cmd_reset(args: argparse.Namespace) -> int:
    """drop + create. The usual command after changing a model."""
    if not _confirm(args, "RESET the schema (drop every table, then recreate)"):
        return 1

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    names = ", ".join(t.name for t in Base.metadata.sorted_tables)
    print(f"Reset {_target()}. Tables now: {names}")
    return 0


def cmd_sql(args: argparse.Namespace) -> int:
    """Run one SQL statement - the escape hatch for hand-written ALTERs."""
    with engine.begin() as conn:  # begin() commits on success, rolls back on error
        result = conn.execute(text(args.statement))
        if result.returns_rows:
            for row in result:
                print(row)
        else:
            print(f"OK ({result.rowcount} rows affected)")
    return 0


def _confirm(args: argparse.Namespace, action: str) -> bool:
    """Destructive commands require --yes, or typing the database name."""
    if args.yes:
        return True

    print(f"About to {action}")
    print(f"on {_target()}")
    answer = input(f"Type the database name ({settings.POSTGRES_DB}) to continue: ")
    if answer.strip() == settings.POSTGRES_DB:
        return True

    print("Cancelled - nothing was changed.")
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.db",
        description="Create, inspect and reset the application schema.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="compare models against the live database").set_defaults(
        func=cmd_status
    )
    sub.add_parser("create", help="create missing tables (safe to re-run)").set_defaults(
        func=cmd_create
    )

    p_drop = sub.add_parser("drop", help="drop all project tables (DESTRUCTIVE)")
    p_drop.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    p_drop.set_defaults(func=cmd_drop)

    p_reset = sub.add_parser("reset", help="drop then create (DESTRUCTIVE)")
    p_reset.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    p_reset.set_defaults(func=cmd_reset)

    p_sql = sub.add_parser("sql", help="execute one SQL statement")
    p_sql.add_argument("statement", help='e.g. "ALTER TABLE users ADD COLUMN name varchar(100)"')
    p_sql.set_defaults(func=cmd_sql, yes=True)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
