import pytest
from app import create_app

@pytest.fixture()
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "DATABASE": str(tmp_path / "test.sqlite3"),
    })
    yield app

@pytest.fixture()
def client(app):
    return app.test_client()
