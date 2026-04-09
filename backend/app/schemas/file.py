import uuid
from datetime import datetime, timezone
from pydantic import BaseModel


class FileCreate(BaseModel):
    filename: str
    object_key: str
    dataset_id: uuid.UUID


class FileRead(BaseModel):
    id: uuid.UUID
    filename: str
    object_key: str
    created_at: datetime
    dataset_id: uuid.UUID
    notes: str | None

    class Config:
        from_attributes = True


class FileUpdate(BaseModel):
    filename: str | None = None
    notes: str | None = None


class BulkMoveFilesRequest(BaseModel):
    file_ids: list[uuid.UUID]
    target_dataset_id: uuid.UUID


class BulkDeleteFilesRequest(BaseModel):
    file_ids: list[uuid.UUID]