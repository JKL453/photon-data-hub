from fastapi import FastAPI, Depends, HTTPException, UploadFile, File as FastAPIFile
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import text, select, func

import socket
import uuid
from datetime import datetime, timezone

from app.db.session import get_db
from app.core.config import settings
from app.core.security import hash_password
from app.models import User, Dataset, File, FilePreview
from app.schemas.user import UserCreate, UserRead
from app.schemas.dataset import DatasetCreate, DatasetRead, DatasetListRead
from app.schemas.file import FileCreate, FileRead
from app.schemas.file_preview import FilePreviewRead
from app.services.storage import upload_fileobj, get_s3_public_client
from app.services.preview import generate_trace_thumb_from_h5
from app.core.config import settings

app = FastAPI(title="PhotonDataHub API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/datasets", response_model=list[DatasetListRead])
def list_datasets(db: Session = Depends(get_db)):
    rows = (db.query(
        Dataset.id,
        Dataset.name,
        Dataset.description,
        Dataset.created_at,
        Dataset.owner_id,
        func.count(File.id).label("file_count"),
    )
    .outerjoin(File, File.dataset_id == Dataset.id)
    .group_by(
            Dataset.id,
            Dataset.name,
            Dataset.description,
            Dataset.created_at,
            Dataset.owner_id,
        )
        .all()
    )
    
    return [
        {
            "id": row.id,
            "name": row.name,
            "description": row.description,
            "created_at": row.created_at,
            "owner_id": row.owner_id,
            "file_count": row.file_count,
        }
        for row in rows
    ]


@app.get("/datasets/{dataset_id}", response_model=DatasetRead)
def get_dataset(dataset_id: uuid.UUID, db: Session = Depends(get_db)):
    stmt = (
        select(Dataset)
        .options(selectinload(Dataset.files))
        .where(Dataset.id == dataset_id)
    )
    dataset = db.execute(stmt).scalar_one_or_none()

    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return dataset


@app.post("/files", response_model=FileRead)
def create_file(
    file_in: FileCreate,
    db: Session = Depends(get_db),
):
    file = File(
        filename=file_in.filename,
        object_key=file_in.object_key,
        dataset_id=file_in.dataset_id,
    )

    db.add(file)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="File already exists")
    db.refresh(file)
    return file


@app.get("/files/{file_id}", response_model=FileRead)
def get_file(file_id: uuid.UUID, 
             db: Session = Depends(get_db)
             ):
    file = db.query(File).filter(File.id == file_id).first()

    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    return file


@app.get("/datasets/{dataset_id}/files", response_model=list[FileRead])
def list_files_for_dataset(
    dataset_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    files = db.query(File).filter(File.dataset_id == dataset_id).all()
    return files


@app.post("/datasets/{dataset_id}/upload", response_model=FileRead)
def upload_dataset_file(
    dataset_id: uuid.UUID,
    uploaded_file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
):
    object_key = f"datasets/{dataset_id}/{uploaded_file.filename}"

    upload_fileobj(
        file_obj=uploaded_file.file,
        object_key=object_key,
        content_type=uploaded_file.content_type,
    )

    file_record = File(
        filename=uploaded_file.filename,
        object_key=object_key,
        dataset_id=dataset_id,
    )

    db.add(file_record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="File already exists")
    db.refresh(file_record)
    return file_record


@app.get("/files/{file_id}/download")
def get_file_download_url(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    file = db.query(File).filter(File.id == file_id).first()

    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    s3 = get_s3_public_client(object_key=file.object_key)

    url = s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.s3_bucket,
            "Key": file.object_key,
        },
        ExpiresIn=3600,
    )

    return {"download_url": url}
    

@app.post("/files/{file_id}/previews", response_model=FilePreviewRead)
def create_preview(file_id: uuid.UUID, db: Session = Depends(get_db)):
    preview = FilePreview(
        file_id=file_id,
        preview_type="trace_thumb",
        preview_data={
            "x": [0, 1, 2 ,3],
            "y": [10, 20, 15, 25],
        },
    )

    db.add(preview)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Preview already exists")
    db.refresh(preview)

    return preview


@app.get("/files/{file_id}/previews", response_model=list[FilePreviewRead])
def get_previews(file_id: uuid.UUID, db: Session = Depends(get_db)):
    previews = db.query(FilePreview).filter(FilePreview.file_id == file_id).all()
    return previews


@app.post("/files/{file_id}/previews/generate-trace-thumb", response_model=FilePreviewRead)
def generate_trace_thumb_preview(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    file = db.query(File).filter(File.id == file_id).first()

    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    preview_data = generate_trace_thumb_from_h5(
        object_key=file.object_key,
        timing_resolution=5e-9,
        bin_width_ms=100.0,
        max_points=300,
    )

    preview = (
        db.query(FilePreview)
        .filter(
            FilePreview.file_id == file.id,
            FilePreview.preview_type == "trace_thumb"
        )
        .first()
    )

    if preview:
        preview.preview_data = preview_data
        preview.created_at = datetime.now(timezone.utc)
    else:
        preview = FilePreview(
            file_id=file.id,
            preview_type="trace_thumb",
            preview_data=preview_data,
        )
        db.add(preview)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Preview already exists")
    db.refresh(preview)

    return preview


@app.get("/files/{file_id}/previews/{preview_type}", response_model=FilePreviewRead)
def get_file_preview_by_type(
    file_id: uuid.UUID,
    preview_type: str,
    db: Session = Depends(get_db),
):
    preview = (
        db.query(FilePreview)
        .filter(
            FilePreview.file_id == file_id,
            FilePreview.preview_type == preview_type,
        )
        .first()
    )

    if preview is None:
        raise HTTPException(status_code=404, detail="Preview not found")

    return preview