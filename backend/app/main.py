from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from sqlalchemy import text
from app.core.config import settings
from app.core.security import hash_password
import socket
import uuid

from app.models import User, Dataset
from app.schemas.user import UserCreate, UserRead
from app.schemas.dataset import DatasetCreate, DatasetRead

app = FastAPI(title="PhotonDataHub API")


@app.get("/health")
def health():
    return {"status": "ok"}

def _tcp_check(host: str, port: int, timeout_s: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return True
    except OSError:
        return False


@app.get("/health/ready")
def ready():
    db_ok = _tcp_check(settings.postgres_host, settings.postgres_port)
    s3_ok = _tcp_check("minio", 9000)

    status = "ok" if (db_ok and s3_ok) else "degraded"
    return {
        "status": status,
        "checks": {
            "db_tcp": db_ok,
            "minio_tcp": s3_ok,
        },
    }


@app.get("/health/db-test")
def db_test(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1")).scalar()
    return {"db_test": result}


@app.post("/users", response_model=UserRead)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    user = User(
        email = user_in.email,
        hashed_password = hash_password(user_in.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")
    db.refresh(user)
    return user


@app.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@app.post("/datasets", response_model=DatasetRead)
def create_dataset(
    dataset_in: DatasetCreate,
    owner_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    dataset = Dataset(
        name = dataset_in.name,
        description = dataset_in.description,
        owner_id = owner_id,
    )

    db.add(dataset)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Dataset name already exists")
    db.refresh(dataset)
    return dataset


@app.get("/datasets", response_model=list[DatasetRead])
def list_datasets(db: Session = Depends(get_db)):
    datasets = db.query(Dataset).all()
    return datasets


@app.get("/datasets/{dataset_id}", response_model=DatasetRead)
def get_dataset(dataset_id: uuid.UUID, db: Session = Depends(get_db)):
    dataset = db.get(Dataset, dataset_id)

    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return dataset