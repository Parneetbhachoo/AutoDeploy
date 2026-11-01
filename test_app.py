
from app import app


def test_homepage():
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert "Welcome to AutoDeploy CI/CD Platform! version 2" in response.data

def test_health_endpoint():
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "healthy"
    assert data["application"] == "AutoDeploy"
    assert data["version"] == "1.0.0"
