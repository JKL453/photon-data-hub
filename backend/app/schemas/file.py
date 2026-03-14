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

    class Config:
        from_attributes = True