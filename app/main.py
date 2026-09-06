from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app import models
from app.database import Base, engine, get_database
from app.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Trainer App API")

bearer_scheme = HTTPBearer(auto_error=False)


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


class TrainerCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class TrainerLogin(BaseModel):
    email: EmailStr
    password: str


def get_current_trainer(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    database: Session = Depends(get_database),
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    trainer_email = decode_access_token(
        credentials.credentials
    )

    if trainer_email is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    trainer = (
        database.query(models.Trainer)
        .filter(models.Trainer.email == trainer_email)
        .first()
    )

    if trainer is None or not trainer.is_active:
        raise HTTPException(
            status_code=401,
            detail="Invalid or inactive trainer",
        )

    return trainer


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/trainers/register")
def register_trainer(
    trainer: TrainerCreate,
    database: Session = Depends(get_database),
):
    existing_trainer = (
        database.query(models.Trainer)
        .filter(models.Trainer.email == trainer.email)
        .first()
    )

    if existing_trainer:
        raise HTTPException(
            status_code=409,
            detail="Trainer with this email already exists",
        )

    new_trainer = models.Trainer(
        email=trainer.email,
        hashed_password=hash_password(trainer.password),
    )

    database.add(new_trainer)
    database.commit()
    database.refresh(new_trainer)

    return {
        "id": new_trainer.id,
        "email": new_trainer.email,
        "is_active": new_trainer.is_active,
    }


@app.post("/trainers/login")
def login_trainer(
    trainer: TrainerLogin,
    database: Session = Depends(get_database),
):
    existing_trainer = (
        database.query(models.Trainer)
        .filter(models.Trainer.email == trainer.email)
        .first()
    )

    if not existing_trainer:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not verify_password(
        trainer.password,
        existing_trainer.hashed_password,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        existing_trainer.email
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@app.post("/clients")
def create_client(
    client: ClientCreate,
    database: Session = Depends(get_database),
    _current_trainer: models.Trainer = Depends(
        get_current_trainer
    ),
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
    _current_trainer: models.Trainer = Depends(
        get_current_trainer
    ),
):
    return database.query(models.Client).all()


@app.post("/clients/{client_id}/check-ins")
def create_check_in(
    client_id: int,
    check_in: CheckInCreate,
    database: Session = Depends(get_database),
    _current_trainer: models.Trainer = Depends(
        get_current_trainer
    ),
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
    _current_trainer: models.Trainer = Depends(
        get_current_trainer
    ),
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
    _current_trainer: models.Trainer = Depends(
        get_current_trainer
    ),
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
    _current_trainer: models.Trainer = Depends(
        get_current_trainer
    ),
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
    _current_trainer: models.Trainer = Depends(
        get_current_trainer
    ),
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
    _current_trainer: models.Trainer = Depends(
        get_current_trainer
    ),
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