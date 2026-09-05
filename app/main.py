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