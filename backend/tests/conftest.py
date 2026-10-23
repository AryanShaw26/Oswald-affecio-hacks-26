import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure test DB URL is set before loading settings — use in-memory SQLite
# with StaticPool so all connections share the same DB and avoid file locking
# on Windows.
os.environ["DATABASE_URL"] = "sqlite:///"

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Ensure direct ``SessionLocal`` calls (used by some tests to assert
# persistence) see the same in-memory SQLite database that the routes
# write to.  Without this, ``SessionLocal`` would bind to the original
# engine from ``app.core.database`` (no StaticPool) and committed rows
# would be invisible.
import app.core.database as _db_module  # noqa: E402
_db_module.SessionLocal = TestingSessionLocal
_db_module.engine = engine

@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    # Start from a clean slate – drop any stale tables first (important
    # when re-running tests).
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_tables():
    """Clear all row data after each test so tests don't leak state."""
    yield
    # Delete in reverse dependency order (children before parents)
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())

@pytest.fixture()
def db():
    """Provide a DB session for tests"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture()
def client():
    return TestClient(app)

