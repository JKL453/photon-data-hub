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
from app.models.file_tag import FileTag
from app.models.tags import Tag
from app.schemas.user import UserCreate, UserRead
from app.schemas.dataset import DatasetCreate, DatasetRead, DatasetListRead, DatasetUpdate
from app.schemas.file import FileCreate, FileRead, BulkMoveFilesRequest, BulkDeleteFilesRequest
from app.schemas.file_preview import FilePreviewRead
from app.schemas.tag import TagCreate, TagRead
from app.services.storage import upload_fileobj, get_s3_public_client, delete_object
from app.services.preview import (
    generate_trace_thumb_from_h5, 
    generate_trace_thumb_from_h5, 
    generate_acf_detail_from_h5,
    generate_acf_thumb_from_h5,
)
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


@app.patch("/datasets/{dataset_id}", response_model=DatasetRead)
def update_dataset(
    dataset_id: uuid.UUID,
    dataset_in: DatasetUpdate,
    db: Session = Depends(get_db),
):
    dataset = db.get(Dataset, dataset_id)

    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if dataset_in.name is not None:
        dataset.name = dataset_in.name
    if dataset_in.description is not None:
        dataset.description = dataset_in.description

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Dataset name already exists")
    
    db.refresh(dataset)
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


# not stored in db yet
@app.get("/files/{file_id}/trace-detail")
def get_file_trace_detail(
    file_id: uuid.UUID,
    bin_width_ms: float = 10.0,
    max_points: int = 5000,
    db: Session = Depends(get_db),
):
    file = db.query(File).filter(File.id == file_id).first()

    if file is None:
        raise HTTPException(status_code=404, detail="File not found")

    if bin_width_ms <= 0:
        raise HTTPException(status_code=400, detail="bin_width_ms must be > 0")

    if max_points <= 0:
        raise HTTPException(status_code=400, detail="max_points must be > 0")

    try:
        trace_data = generate_trace_thumb_from_h5(
            object_key=file.object_key,
            timing_resolution=5e-9,
            bin_width_ms=bin_width_ms,
            max_points=max_points,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    trace_data["preview_kind"] = "trace_detail"
    trace_data["file_id"] = str(file.id)

    return trace_data


@app.delete("/files/{file_id}")
def delete_file(file_id: uuid.UUID,
                db: Session = Depends(get_db),
                ):
    file = db.query(File).filter(File.id == file_id).first()
    
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    object_key = file.object_key
    
    db.delete(file)
    db.flush() # ensure the file record is deleted before deleting the object

    # check if other files are using the same object_key before deleting the object from storage
    remaining = db.query(File).filter(File.object_key == object_key).count()

    if remaining == 0:
        delete_object(object_key)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error deleting file record")
    
    return {"detail": "File deleted"}


@app.delete("/datasets/{dataset_id}")
def delete_dataset(dataset_id: uuid.UUID, 
                   db: Session = Depends(get_db),
                   ):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    files = db.query(File).filter(File.dataset_id == dataset_id).all()

    for file in files:
        db.delete(file)
        db.flush() # ensure the file record is deleted before deleting the object

        # check if other files are using the same object_key before deleting the object from storage
        remaining = db.query(File).filter(File.object_key == file.object_key).count()

        if remaining == 0:
            delete_object(file.object_key)

    db.delete(dataset)

    try:
        db.commit()
    except IntegrityError: 
        db.rollback()
        raise HTTPException(status_code=500, detail="Error deleting dataset")

    return {"detail": "Dataset deleted"}


@app.post("/files/bulk-delete")
def bulk_delete_files(
    request: BulkDeleteFilesRequest,
    db: Session = Depends(get_db),
):
    files = (
        db.query(File)
        .filter(File.id.in_(request.file_ids))
        .all()
    )

    if len(files) != len(request.file_ids):
        raise HTTPException(status_code=404, detail="One or more files not found")

    for file in files:
        db.delete(file)
        db.flush() # ensure the file record is deleted before deleting the object

        # check if other files are using the same object_key before deleting the object from storage
        remaining = db.query(File).filter(File.object_key == file.object_key).count()

        if remaining == 0:
            delete_object(file.object_key)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error deleting files")

    return {"detail": "Files deleted"}


@app.post("/files/bulk-move")
def bulk_move_files(
    request: BulkMoveFilesRequest,
    db: Session = Depends(get_db),
):
    target_dataset = db.get(Dataset, request.target_dataset_id)

    if target_dataset is None:
        raise HTTPException(status_code=404, detail="Target dataset not found")

    files = (
        db.query(File)
        .filter(File.id.in_(request.file_ids))
        .all()
    )

    if len(files) != len(request.file_ids):
        raise HTTPException(status_code=404, detail="One or more files not found")

    for file in files:
        file.dataset_id = request.target_dataset_id

    db.commit()

    return {"detail": "Files moved"}


@app.post("/files/bulk-copy")
def bulk_copy_files(request: BulkMoveFilesRequest, db: Session = Depends(get_db)):
    if not request.file_ids:
        raise HTTPException(status_code=400, detail="file_ids required")

    if not request.target_dataset_id:
        raise HTTPException(status_code=400, detail="target_dataset_id required")

    files = db.query(File).filter(File.id.in_(request.file_ids)).all()

    if not files:
        raise HTTPException(status_code=404, detail="No files found")

    new_files = []

    for file in files:
        new_file = File(
            id=uuid.uuid4(),
            filename=file.filename,
            object_key=file.object_key,
            dataset_id=request.target_dataset_id,
            created_at=datetime.utcnow(),
        )

        db.add(new_file)
        new_files.append(new_file)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error copying files")
    

    return {
        "copied_files": [str(f.id) for f in new_files],
        "count": len(new_files),
    }


@app.get("/files/{file_id}/acf-detail")
def get_file_acf_detail(
    file_id: uuid.UUID,
    bins_per_dec: int = 30,
    lag_min_exp: int = 0,
    lag_max_exp: int = 7,
    cut_points: int = 50,
    tau_min_s: float | None = 5e-6,
    tau_max_s: float | None = None,
    db: Session = Depends(get_db),
):
    file = db.query(File).filter(File.id == file_id).first()

    if file is None:
        raise HTTPException(status_code=404, detail="File not found")

    if bins_per_dec <= 0:
        raise HTTPException(status_code=400, detail="bins_per_dec must be > 0")

    if lag_max_exp <= lag_min_exp:
        raise HTTPException(status_code=400, detail="lag_max_exp must be > lag_min_exp")

    if cut_points < 0:
        raise HTTPException(status_code=400, detail="cut_points must be >= 0")

    if tau_min_s is not None and tau_min_s < 0:
        raise HTTPException(status_code=400, detail="tau_min_s must be >= 0")

    if tau_max_s is not None and tau_max_s < 0:
        raise HTTPException(status_code=400, detail="tau_max_s must be >= 0")

    if tau_min_s is not None and tau_max_s is not None and tau_max_s <= tau_min_s:
        raise HTTPException(status_code=400, detail="tau_max_s must be > tau_min_s")

    try:
        acf_data = generate_acf_detail_from_h5(
            object_key=file.object_key,
            timing_resolution=5e-9,
            bins_per_dec=bins_per_dec,
            lag_min_exp=lag_min_exp,
            lag_max_exp=lag_max_exp,
            cut_points=cut_points,
            tau_min_s=tau_min_s,
            tau_max_s=tau_max_s,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ImportError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    acf_data["file_id"] = str(file.id)

    return acf_data


@app.post("/files/{file_id}/previews/generate-acf-thumb", response_model=FilePreviewRead)
def generate_acf_thumb_preview(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    file = db.query(File).filter(File.id == file_id).first()

    if file is None:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        preview_data = generate_acf_thumb_from_h5(
            object_key=file.object_key,
            timing_resolution=5e-9,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ImportError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    preview = (
        db.query(FilePreview)
        .filter(
            FilePreview.file_id == file.id,
            FilePreview.preview_type == "acf_thumb",
        )
        .first()
    )

    if preview is None:
        preview = FilePreview(
            file_id=file.id,
            preview_type="acf_thumb",
            preview_data=preview_data,
        )
        db.add(preview)
    else:
        preview.preview_data = preview_data

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error generating preview")
    db.refresh(preview)

    return preview


@app.post("/tags", response_model=TagRead)
def create_tag(tag_in: TagCreate, db: Session = Depends(get_db)):
    existing = db.query(Tag).filter(Tag.name == tag_in.name).first()

    if existing:
        return existing
    
    tag = Tag(name=tag_in.name)
    db.add(tag)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Tag name already exists")
    db.refresh(tag)

    return tag


@app.get("/tags", response_model=list[TagRead])
def list_tags(db: Session = Depends(get_db)):
    return db.query(Tag).order_by(Tag.name).all()


@app.post("/files/{file_id}/tags/{tag_id}")
def add_tag_to_file(
    file_id: uuid.UUID,
    tag_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    file = db.query(File).filter(File.id == file_id).first()
    tag = db.query(Tag).filter(Tag.id == tag_id).first()

    if not file or not tag:
        raise HTTPException(status_code=404, detail="File or Tag not found")

    existing = (
        db.query(FileTag)
        .filter(FileTag.file_id == file_id, FileTag.tag_id == tag_id)
        .first()
    )

    if existing:
        return {"message": "Tag already assigned"}

    file_tag = FileTag(file_id=file_id, tag_id=tag_id)
    db.add(file_tag)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error adding tag to file")

    return {"message": "Tag added"}


@app.delete("/files/{file_id}/tags/{tag_id}")
def remove_tag_from_file(
    file_id: uuid.UUID,
    tag_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    file_tag = (
        db.query(FileTag)
        .filter(FileTag.file_id == file_id, FileTag.tag_id == tag_id)
        .first()
    )

    if not file_tag:
        raise HTTPException(status_code=404, detail="Tag not assigned")

    db.delete(file_tag)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error removing tag from file")

    return {"message": "Tag removed"}


@app.get("/files/{file_id}/tags", response_model=list[TagRead])
def get_file_tags(file_id: uuid.UUID, db: Session = Depends(get_db)):
    file = db.query(File).filter(File.id == file_id).first()

    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    file_tags = (
        db.query(Tag)
        .join(FileTag, Tag.id == FileTag.tag_id)
        .filter(FileTag.file_id == file_id)
        .all()
    )

    return file_tags