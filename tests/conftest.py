import pytest

from backend_lab import create_app


@pytest.fixture
def app(tmp_path):
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite3"), "COUNTRIES_FILE": None})


@pytest.fixture
def client(app):
    return app.test_client()
