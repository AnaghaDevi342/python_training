from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert "database" in response.json()
    assert "redis" in response.json()


def test_get_data():
    response = client.get("/data")
    assert response.status_code == 200


def test_get_data_with_pagination():
    response = client.get("/data?page=1&per_page=5")
    assert response.status_code == 200


def test_get_data_with_department_filter():
    response = client.get("/data?department=90")
    assert response.status_code == 200


def test_invalid_employee():
    response = client.get("/data/999999")
    assert response.status_code == 404


def test_summary_endpoint():
    response = client.get("/analytics/summary")
    assert response.status_code == 200


def test_trends_endpoint():
    response = client.get("/analytics/trends")
    assert response.status_code == 200


def test_docs_endpoint():
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_endpoint():
    response = client.get("/openapi.json")
    assert response.status_code == 200