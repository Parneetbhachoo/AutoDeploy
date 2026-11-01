
from app import app


def test_homepage():
    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 200
    assert b"Welcome to AutoDeploy CI/CD Platform !" in response.data
    assert b"/dashboard" in response.data


def test_health_endpoint():
    client = app.test_client()
    response = client.get("/health")

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "healthy"
    assert data["application"] == "AutoDeploy"
    assert data["version"] == "1.0.0"


def test_dashboard():
    client = app.test_client()
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"AutoDeploy Dashboard" in response.data
    assert b"Application Status" in response.data
    assert b"Process Start Time" in response.data
