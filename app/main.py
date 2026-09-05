from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
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