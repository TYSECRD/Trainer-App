import pytest
from fastapi.testclient import TestClient

from app import models
from app.database import SessionLocal
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_clients():
    database = SessionLocal()

    database.query(models.Client).delete()
    database.commit()
    database.close()

    yield

    database = SessionLocal()

    database.query(models.Client).delete()
    database.commit()
    database.close()


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_reject_duplicate_client_email():
    client_data = {
        "first_name": "Tyler",
        "last_name": "Test",
        "email": "duplicate@test.com",
        "goal": "Build muscle",
    }

    first_response = client.post("/clients", json=client_data)

    assert first_response.status_code == 200

    second_response = client.post("/clients", json=client_data)

    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Client with this email already exists"
    }


def test_create_and_get_client():
    client_data = {
        "first_name": "Alex",
        "last_name": "Rivera",
        "email": "alex@test.com",
        "goal": "Lose 20 pounds",
    }

    create_response = client.post("/clients", json=client_data)

    assert create_response.status_code == 200

    created_client = create_response.json()

    assert created_client["first_name"] == "Alex"
    assert created_client["last_name"] == "Rivera"
    assert created_client["email"] == "alex@test.com"
    assert created_client["goal"] == "Lose 20 pounds"
    assert "id" in created_client

    get_response = client.get("/clients")

    assert get_response.status_code == 200

    clients = get_response.json()

    assert any(
        saved_client["email"] == "alex@test.com"
        for saved_client in clients
    )