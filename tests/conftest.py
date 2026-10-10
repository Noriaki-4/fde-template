import os

os.environ.setdefault("NOSQL_ENABLED", "true")
os.environ.setdefault("OPENSEARCH_ENABLED", "true")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.api.main import app
from backend.database.db import get_db
from backend.database.models import Base

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sqlite_url(tmp_path):
    return f"sqlite:///{tmp_path / 'jobs.db'}"


@pytest.fixture
def session_factory(sqlite_url):
    """Session factory on an isolated file DB (also reachable from job subprocesses)."""
    file_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=file_engine)
    yield sessionmaker(autocommit=False, autoflush=False, bind=file_engine)
    file_engine.dispose()


@pytest.fixture
def job_env(monkeypatch, sqlite_url):
    """Environment for job subprocesses: same DB file + test fixture jobs."""
    import tests.fixtures.jobs  # noqa: F401  (registers test jobs in this process)

    monkeypatch.setenv("DATABASE_URL", sqlite_url)
    monkeypatch.setenv("JOB_MODULES", "backend.jobs.definitions,tests.fixtures.jobs")
    monkeypatch.setenv("JOB_LAUNCHER", "local")
