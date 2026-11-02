import pytest

from psychodelic.app import create_app


@pytest.fixture()
def app(tmp_path):
    return create_app(data_dir=tmp_path / "data", comfy_url="http://127.0.0.1:9")  # port zamkniety = brak serwera


@pytest.fixture()
def client(app):
    from fastapi.testclient import TestClient

    return TestClient(app)
