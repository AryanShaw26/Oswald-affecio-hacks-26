r"""
Migration script — adds the ``hashed_password`` column to the existing
``users`` table in PostgreSQL.

Background:
  The ``User`` model (app/models/user.py) defines ``hashed_password`` but
  ``Base.metadata.create_all()`` in main.py does NOT alter pre-existing
  tables, so databases created before this column was added are missing it.
  This script checks for the column and adds it if absent.

Usage:
    cd /backend
    .venv\Scripts\python.exe scripts/migrate_add_hashed_password.py
"""

import sys

from sqlalchemy import inspect, text


def run_migration():
    # Import after sys.path is set up (works both as script and module)
    from app.core.database import engine
    from app.core.config import settings

    print(f"🗄️  Connecting to: {settings.DATABASE_URL.replace(settings.SECRET_KEY or '', '***')}")

    inspector = inspect(engine)
    existing_columns = [col["name"] for col in inspector.get_columns("users")]
    print(f"   Existing columns on 'users': {existing_columns}")

    if "hashed_password" in existing_columns:
        print("✅ Column 'hashed_password' already exists — nothing to do.")
        return True

    print("⚠  Column 'hashed_password' is missing — adding it now...")

    with engine.begin() as conn:
        # Add the column as nullable with a default empty-string hash placeholder.
        # Existing users won't be able to log in until they reset their password,
        # which is the expected behaviour since we don't know their original passwords.
        conn.execute(text(
            "ALTER TABLE users ADD COLUMN hashed_password VARCHAR NOT NULL DEFAULT ''"
        ))

    # Verify
    inspector = inspect(engine)
    updated_columns = [col["name"] for col in inspector.get_columns("users")]
    if "hashed_password" in updated_columns:
        print(f"✅ Migration successful! Updated columns: {updated_columns}")
        return True
    else:
        print("❌ Migration failed — column still not found.")
        return False


if __name__ == "__main__":
    # Ensure the backend package is importable when run from the backend root
    import os
    backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if backend_root not in sys.path:
        sys.path.insert(0, backend_root)

    ok = run_migration()
    sys.exit(0 if ok else 1)
