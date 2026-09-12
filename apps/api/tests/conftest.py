import os
import sys
import pytest

# Use isolated test database to prevent race conditions with running dev servers
os.environ["DATABASE_URL"] = "sqlite:///./test_flowshield.db"

# Ensure app and scripts packages are reachable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, Base, SessionLocal


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    # Ensure seed data exists
    from scripts.seed_db import seed_database
    seed_database()
    yield
    # Cleanup test db
    try:
        engine.dispose()
        if os.path.exists("./test_flowshield.db"):
            os.remove("./test_flowshield.db")
    except Exception:
        pass


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
