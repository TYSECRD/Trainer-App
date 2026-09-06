import pytest
from fastapi.testclient import TestClient

from app import models
from app.database import SessionLocal
from app.main import app


client = TestClient(app)


def get_auth_headers():
    trainer_data = {
        "email": "auth@test.com",
        "password": "StrongPass123",
    }

    register_response = client.post(
        "/trainers/register",
        json=trainer_data,
    )

    assert register_response.status_code == 200

    login_response = client.post(
        "/trainers/login",
        json=trainer_data,
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {access_token}"
    }


@pytest.fixture(autouse=True)
def clear_database():
    database = SessionLocal()

    database.query(models.DietPlan).delete()
    database.query(models.Workout).delete()
    database.query(models.CheckIn).delete()
    database.query(models.Client).delete()
    database.query(models.Trainer).delete()

    database.commit()
    database.close()

    yield

    database = SessionLocal()

    database.query(models.DietPlan).delete()
    database.query(models.Workout).delete()
    database.query(models.CheckIn).delete()
    database.query(models.Client).delete()
    database.query(models.Trainer).delete()

    database.commit()
    database.close()


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_reject_duplicate_client_email():
    auth_headers = get_auth_headers()

    client_data = {
        "first_name": "Tyler",
        "last_name": "Test",
        "email": "duplicate@test.com",
        "goal": "Build muscle",
    }

    first_response = client.post(
        "/clients",
        json=client_data,
        headers=auth_headers,
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/clients",
        json=client_data,
        headers=auth_headers,
    )

    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Client with this email already exists"
    }


def test_create_and_get_client():
    auth_headers = get_auth_headers()

    client_data = {
        "first_name": "Alex",
        "last_name": "Rivera",
        "email": "alex@test.com",
        "goal": "Lose 20 pounds",
    }

    create_response = client.post(
        "/clients",
        json=client_data,
        headers=auth_headers,
    )

    assert create_response.status_code == 200

    created_client = create_response.json()

    assert created_client["first_name"] == "Alex"
    assert created_client["last_name"] == "Rivera"
    assert created_client["email"] == "alex@test.com"
    assert created_client["goal"] == "Lose 20 pounds"
    assert "id" in created_client

    get_response = client.get(
        "/clients",
        headers=auth_headers,
    )

    assert get_response.status_code == 200

    clients = get_response.json()

    assert any(
        saved_client["email"] == "alex@test.com"
        for saved_client in clients
    )


def test_create_and_get_check_in():
    auth_headers = get_auth_headers()

    client_response = client.post(
        "/clients",
        json={
            "first_name": "Jordan",
            "last_name": "Smith",
            "email": "jordan@test.com",
            "goal": "Lose fat",
        },
        headers=auth_headers,
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
        headers=auth_headers,
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
        f"/clients/{client_id}/check-ins",
        headers=auth_headers,
    )

    assert get_response.status_code == 200

    check_ins = get_response.json()

    assert len(check_ins) == 1
    assert check_ins[0]["weight"] == 225.5


def test_reject_check_in_for_missing_client():
    auth_headers = get_auth_headers()

    response = client.post(
        "/clients/999/check-ins",
        json={
            "weight": 200,
            "energy": 7,
            "diet_adherence": 8,
            "workout_adherence": 8,
            "notes": "Should not save",
        },
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Client not found"
    }


def test_reject_invalid_check_in_scores():
    auth_headers = get_auth_headers()

    client_response = client.post(
        "/clients",
        json={
            "first_name": "Taylor",
            "last_name": "Jones",
            "email": "taylor@test.com",
            "goal": "Build muscle",
        },
        headers=auth_headers,
    )

    assert client_response.status_code == 200

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
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_create_and_get_workout():
    auth_headers = get_auth_headers()

    client_response = client.post(
        "/clients",
        json={
            "first_name": "Chris",
            "last_name": "Walker",
            "email": "chris@test.com",
            "goal": "Build muscle",
        },
        headers=auth_headers,
    )

    assert client_response.status_code == 200

    client_id = client_response.json()["id"]

    workout_response = client.post(
        f"/clients/{client_id}/workouts",
        json={
            "name": "Push Day",
            "exercise": "Bench Press",
            "sets": 4,
            "reps": 8,
            "notes": "Leave one rep in reserve",
        },
        headers=auth_headers,
    )

    assert workout_response.status_code == 200

    workout = workout_response.json()

    assert workout["client_id"] == client_id
    assert workout["name"] == "Push Day"
    assert workout["exercise"] == "Bench Press"
    assert workout["sets"] == 4
    assert workout["reps"] == 8

    get_response = client.get(
        f"/clients/{client_id}/workouts",
        headers=auth_headers,
    )

    assert get_response.status_code == 200

    workouts = get_response.json()

    assert len(workouts) == 1
    assert workouts[0]["exercise"] == "Bench Press"


def test_reject_workout_for_missing_client():
    auth_headers = get_auth_headers()

    response = client.post(
        "/clients/999/workouts",
        json={
            "name": "Pull Day",
            "exercise": "Barbell Row",
            "sets": 4,
            "reps": 10,
            "notes": "Controlled reps",
        },
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Client not found"
    }


def test_create_and_get_diet_plan():
    auth_headers = get_auth_headers()

    client_response = client.post(
        "/clients",
        json={
            "first_name": "Morgan",
            "last_name": "Lee",
            "email": "morgan@test.com",
            "goal": "Lose fat",
        },
        headers=auth_headers,
    )

    assert client_response.status_code == 200

    client_id = client_response.json()["id"]

    diet_response = client.post(
        f"/clients/{client_id}/diet-plans",
        json={
            "name": "Cut Phase",
            "calories": 2200,
            "protein": 200,
            "carbs": 180,
            "fat": 65,
            "notes": "Keep meals simple and consistent",
        },
        headers=auth_headers,
    )

    assert diet_response.status_code == 200

    diet_plan = diet_response.json()

    assert diet_plan["client_id"] == client_id
    assert diet_plan["name"] == "Cut Phase"
    assert diet_plan["calories"] == 2200
    assert diet_plan["protein"] == 200
    assert diet_plan["carbs"] == 180
    assert diet_plan["fat"] == 65

    get_response = client.get(
        f"/clients/{client_id}/diet-plans",
        headers=auth_headers,
    )

    assert get_response.status_code == 200

    diet_plans = get_response.json()

    assert len(diet_plans) == 1
    assert diet_plans[0]["name"] == "Cut Phase"


def test_reject_diet_plan_for_missing_client():
    auth_headers = get_auth_headers()

    response = client.post(
        "/clients/999/diet-plans",
        json={
            "name": "Maintenance",
            "calories": 2500,
            "protein": 180,
            "carbs": 250,
            "fat": 70,
            "notes": "Should not save",
        },
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Client not found"
    }


def test_register_trainer():
    response = client.post(
        "/trainers/register",
        json={
            "email": "trainer@test.com",
            "password": "StrongPass123",
        },
    )

    assert response.status_code == 200

    trainer = response.json()

    assert trainer["email"] == "trainer@test.com"
    assert trainer["is_active"] is True
    assert "id" in trainer
    assert "hashed_password" not in trainer
    assert "password" not in trainer


def test_reject_duplicate_trainer_email():
    trainer_data = {
        "email": "duplicate.trainer@test.com",
        "password": "StrongPass123",
    }

    first_response = client.post(
        "/trainers/register",
        json=trainer_data,
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/trainers/register",
        json=trainer_data,
    )

    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Trainer with this email already exists"
    }


def test_reject_short_trainer_password():
    response = client.post(
        "/trainers/register",
        json={
            "email": "short@test.com",
            "password": "123",
        },
    )

    assert response.status_code == 422


def test_trainer_login_returns_token():
    register_response = client.post(
        "/trainers/register",
        json={
            "email": "login@test.com",
            "password": "StrongPass123",
        },
    )

    assert register_response.status_code == 200

    login_response = client.post(
        "/trainers/login",
        json={
            "email": "login@test.com",
            "password": "StrongPass123",
        },
    )

    assert login_response.status_code == 200

    login_data = login_response.json()

    assert "access_token" in login_data
    assert login_data["token_type"] == "bearer"


def test_reject_login_with_wrong_password():
    client.post(
        "/trainers/register",
        json={
            "email": "wrongpass@test.com",
            "password": "StrongPass123",
        },
    )

    response = client.post(
        "/trainers/login",
        json={
            "email": "wrongpass@test.com",
            "password": "WrongPass456",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid email or password"
    }


def test_reject_login_with_unknown_email():
    response = client.post(
        "/trainers/login",
        json={
            "email": "nobody@test.com",
            "password": "StrongPass123",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid email or password"
    }


def test_reject_clients_without_auth():
    response = client.get("/clients")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Authentication required"
    }

def test_update_client():
    auth_headers = get_auth_headers()

    create_response = client.post(
        "/clients",
        json={
            "first_name": "Alex",
            "last_name": "Rivera",
            "email": "alex.update@test.com",
            "goal": "Lose fat",
        },
        headers=auth_headers,
    )

    client_id = create_response.json()["id"]

    update_response = client.patch(
        f"/clients/{client_id}",
        json={
            "goal": "Build muscle",
        },
        headers=auth_headers,
    )

    assert update_response.status_code == 200

    updated_client = update_response.json()

    assert updated_client["goal"] == "Build muscle"
    assert updated_client["email"] == "alex.update@test.com"


def test_reject_update_for_missing_client():
    auth_headers = get_auth_headers()

    response = client.patch(
        "/clients/999",
        json={
            "goal": "Build muscle",
        },
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Client not found"
    }


def test_delete_client():
    auth_headers = get_auth_headers()

    create_response = client.post(
        "/clients",
        json={
            "first_name": "Delete",
            "last_name": "Test",
            "email": "delete@test.com",
            "goal": "Test deletion",
        },
        headers=auth_headers,
    )

    client_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/clients/{client_id}",
        headers=auth_headers,
    )

    assert delete_response.status_code == 200
    assert delete_response.json() == {
        "message": "Client deleted successfully"
    }

    database = SessionLocal()

    deleted_client = (
        database.query(models.Client)
        .filter(models.Client.id == client_id)
        .first()
    )

    database.close()

    assert deleted_client is None


def test_reject_delete_for_missing_client():
    auth_headers = get_auth_headers()

    response = client.delete(
        "/clients/999",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Client not found"
    }