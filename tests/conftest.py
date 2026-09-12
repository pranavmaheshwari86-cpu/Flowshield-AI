import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

API_DIR = os.path.join(REPO_ROOT, "apps", "api")
if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)

# Use unified isolated test database
os.environ["DATABASE_URL"] = "sqlite:///./test_flowshield.db"

from fastapi.testclient import TestClient
from apps.api.app.main import app
from apps.api.app.database import engine, Base, SessionLocal


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    from scripts.seed_db import seed_database
    try:
        seed_database()
    except Exception as e:
        print(f"Seed DB warning in test: {e}")
    yield
    try:
        engine.dispose()
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
