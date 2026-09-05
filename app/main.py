from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app import models
from app.database import Base, engine, get_database


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Trainer App API")


class ClientCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    goal: str


class CheckInCreate(BaseModel):
    weight: float = Field(gt=0)
    energy: int = Field(ge=1, le=10)
    diet_adherence: int = Field(ge=1, le=10)
    workout_adherence: int = Field(ge=1, le=10)
    notes: str

class WorkoutCreate(BaseModel):
    name: str
    exercise: str
    sets: int = Field(gt=0)
    reps: int = Field(gt=0)
    notes: str

class DietPlanCreate(BaseModel):
    name: str
    calories: int = Field(gt=0)
    protein: int = Field(ge=0)
    carbs: int = Field(ge=0)
    fat: int = Field(ge=0)
    notes: str


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/clients")
def create_client(
    client: ClientCreate,
    database: Session = Depends(get_database),
):
    existing_client = (
        database.query(models.Client)
        .filter(models.Client.email == client.email)
        .first()
    )

    if existing_client:
        raise HTTPException(
            status_code=409,
            detail="Client with this email already exists",
        )

    new_client = models.Client(
        first_name=client.first_name,
        last_name=client.last_name,
        email=client.email,
        goal=client.goal,
    )

    database.add(new_client)
    database.commit()
    database.refresh(new_client)

    return new_client


@app.get("/clients")
def get_clients(
    database: Session = Depends(get_database),
):
    return database.query(models.Client).all()


@app.post("/clients/{client_id}/check-ins")
def create_check_in(
    client_id: int,
    check_in: CheckInCreate,
    database: Session = Depends(get_database),
):
    existing_client = (
        database.query(models.Client)
        .filter(models.Client.id == client_id)
        .first()
    )

    if not existing_client:
        raise HTTPException(
            status_code=404,
            detail="Client not found",
        )

    new_check_in = models.CheckIn(
        client_id=client_id,
        weight=check_in.weight,
        energy=check_in.energy,
        diet_adherence=check_in.diet_adherence,
        workout_adherence=check_in.workout_adherence,
        notes=check_in.notes,
    )

    database.add(new_check_in)
    database.commit()
    database.refresh(new_check_in)

    return new_check_in


@app.get("/clients/{client_id}/check-ins")
def get_check_ins(
    client_id: int,
    database: Session = Depends(get_database),
):
    existing_client = (
        database.query(models.Client)
        .filter(models.Client.id == client_id)
        .first()
    )

    if not existing_client:
        raise HTTPException(
            status_code=404,
            detail="Client not found",
        )

    return (
        database.query(models.CheckIn)
        .filter(models.CheckIn.client_id == client_id)
        .order_by(models.CheckIn.created_at)
        .all()
    )

@app.post("/clients/{client_id}/workouts")
def create_workout(
    client_id: int,
    workout: WorkoutCreate,
    database: Session = Depends(get_database),
):
    existing_client = (
        database.query(models.Client)
        .filter(models.Client.id == client_id)
        .first()
    )

    if not existing_client:
        raise HTTPException(
            status_code=404,
            detail="Client not found",
        )

    new_workout = models.Workout(
        client_id=client_id,
        name=workout.name,
        exercise=workout.exercise,
        sets=workout.sets,
        reps=workout.reps,
        notes=workout.notes,
    )

    database.add(new_workout)
    database.commit()
    database.refresh(new_workout)

    return new_workout


@app.get("/clients/{client_id}/workouts")
def get_workouts(
    client_id: int,
    database: Session = Depends(get_database),
):
    existing_client = (
        database.query(models.Client)
        .filter(models.Client.id == client_id)
        .first()
    )

    if not existing_client:
        raise HTTPException(
            status_code=404,
            detail="Client not found",
        )

    return (
        database.query(models.Workout)
        .filter(models.Workout.client_id == client_id)
        .order_by(models.Workout.created_at)
        .all()
    )

@app.post("/clients/{client_id}/diet-plans")
def create_diet_plan(
    client_id: int,
    diet_plan: DietPlanCreate,
    database: Session = Depends(get_database),
):
    existing_client = (
        database.query(models.Client)
        .filter(models.Client.id == client_id)
        .first()
    )

    if not existing_client:
        raise HTTPException(
            status_code=404,
            detail="Client not found",
        )

    new_diet_plan = models.DietPlan(
        client_id=client_id,
        name=diet_plan.name,
        calories=diet_plan.calories,
        protein=diet_plan.protein,
        carbs=diet_plan.carbs,
        fat=diet_plan.fat,
        notes=diet_plan.notes,
    )

    database.add(new_diet_plan)
    database.commit()
    database.refresh(new_diet_plan)

    return new_diet_plan

@app.get("/clients/{client_id}/diet-plans")
def get_diet_plans(
    client_id: int,
    database: Session = Depends(get_database),
):
    existing_client = (
        database.query(models.Client)
        .filter(models.Client.id == client_id)
        .first()
    )

    if not existing_client:
        raise HTTPException(
            status_code=404,
            detail="Client not found",
        )

    return (
        database.query(models.DietPlan)
        .filter(models.DietPlan.client_id == client_id)
        .order_by(models.DietPlan.created_at)
        .all()
    )