import uuid
from datetime import datetime
from pydantic import BaseModel


class DatasetCreate(BaseModel):
    name: str
    description: str | None = None


class DatasetRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    owner_id: uuid.UUID

    class Config:
        from_attributes = True