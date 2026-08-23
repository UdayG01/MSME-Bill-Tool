import os
import tempfile
from pathlib import Path

import pytest


TEST_DIR = Path(tempfile.mkdtemp(prefix="msme_billing_tests_"))
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = f"sqlite:///{(TEST_DIR / 'test.db').as_posix()}"
os.environ["MIGRATION_DATABASE_URL"] = os.environ["DATABASE_URL"]
os.environ["FRONTEND_ORIGINS"] = "http://testserver"
os.environ["SESSION_COOKIE_SECURE"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

from core.session import _SESSIONS  # noqa: E402
from db.database import Base, engine  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    _SESSIONS.clear()
    with TestClient(app) as test_client:
        yield test_client
    _SESSIONS.clear()
    Base.metadata.drop_all(bind=engine)
