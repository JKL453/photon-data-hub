import uuid
from datetime import datetime
from pydantic import BaseModel
from app.schemas.file import FileRead


class DatasetCreate(BaseModel):
    name: str
    description: str | None = None
    notes: str | None = None


class DatasetRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    owner_id: uuid.UUID
    files: list[FileRead] = []
    notes: str | None 

    class Config:
        from_attributes = True


class DatasetListRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    owner_id: uuid.UUID
    file_count: int


class DatasetUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    notes: str | None = None