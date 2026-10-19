"""Shared pytest fixtures.

Environment variables are set before importing the application so the job
manager and settings bind to an isolated temporary data directory.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

TEST_DATA = Path(tempfile.mkdtemp(prefix="docupro-tests-"))
os.environ["DOCUPRO_DATA_DIR"] = str(TEST_DATA)
os.environ.setdefault("DOCUPRO_RETENTION_MINUTES", "10")
os.environ.setdefault("DOCUPRO_MAX_UPLOAD_MB", "30")
os.environ.setdefault("DOCUPRO_MAX_PAGES", "40")
os.environ.setdefault("DOCUPRO_MAX_PIXELS", "40000000")
os.environ.setdefault("DOCUPRO_CONVERSION_TIMEOUT", "180")
os.environ.setdefault("DOCUPRO_RATE_LIMIT", "600")
os.environ.setdefault("DOCUPRO_RATE_BURST", "200")
os.environ.setdefault("DOCUPRO_LOG_LEVEL", "WARNING")

SERVICES_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SERVICES_DIR))
REPO_ROOT = SERVICES_DIR.parent.parent

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def corpus() -> Path:
    """Generate the corpus once per test session."""
    sys.path.insert(0, str(REPO_ROOT / "tests" / "corpus"))
    import make_corpus

    target = TEST_DATA / "corpus"
    target.mkdir(parents=True, exist_ok=True)
    if not (target / "report-fr.pdf").exists():
        make_corpus.main.__globals__["sys"].argv = ["make_corpus.py", str(target)]
        make_corpus.main()
    return target


@pytest.fixture(scope="session")
def client(corpus):
    from fastapi.testclient import TestClient

    from docupro_api.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def settings():
    from docupro_api.config import get_settings

    return get_settings()
