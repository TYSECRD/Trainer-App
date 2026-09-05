import pytest
from fastapi.testclient import TestClient

from app import models
from app.database import SessionLocal
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_database():
    database = SessionLocal()

    database.query(models.CheckIn).delete()
    database.query(models.Client).delete()
    database.commit()
    database.close()

    yield

    database = SessionLocal()

    database.query(models.CheckIn).delete()
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


def test_create_and_get_check_in():
    client_response = client.post(
        "/clients",
        json={
            "first_name": "Jordan",
            "last_name": "Smith",
            "email": "jordan@test.com",
            "goal": "Lose fat",
        },
    )

    assert client_response.status_code == 200

    client_id = client_response.json()["id"]

    check_in_response = client.post(
        f"/clients/{client_id}/check-ins",
        json={
            "weight": 225.5,
            "energy": 8,
            "diet_adherence": 9,
            "workout_adherence": 7,
            "notes": "Good week overall",
        },
    )

    assert check_in_response.status_code == 200

    check_in = check_in_response.json()

    assert check_in["client_id"] == client_id
    assert check_in["weight"] == 225.5
    assert check_in["energy"] == 8
    assert check_in["diet_adherence"] == 9
    assert check_in["workout_adherence"] == 7
    assert check_in["notes"] == "Good week overall"
    assert "created_at" in check_in

    get_response = client.get(
        f"/clients/{client_id}/check-ins"
    )

    assert get_response.status_code == 200

    check_ins = get_response.json()

    assert len(check_ins) == 1
    assert check_ins[0]["weight"] == 225.5


def test_reject_check_in_for_missing_client():
    response = client.post(
        "/clients/999/check-ins",
        json={
            "weight": 200,
            "energy": 7,
            "diet_adherence": 8,
            "workout_adherence": 8,
            "notes": "Should not save",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Client not found"
    }


def test_reject_invalid_check_in_scores():
    client_response = client.post(
        "/clients",
        json={
            "first_name": "Taylor",
            "last_name": "Jones",
            "email": "taylor@test.com",
            "goal": "Build muscle",
        },
    )

    client_id = client_response.json()["id"]

    response = client.post(
        f"/clients/{client_id}/check-ins",
        json={
            "weight": 210,
            "energy": 15,
            "diet_adherence": 0,
            "workout_adherence": 12,
            "notes": "Invalid scores",
        },
    )

    assert response.status_code == 422