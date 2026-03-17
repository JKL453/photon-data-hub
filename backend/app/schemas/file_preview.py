import uuid
from datetime import datetime
from pydantic import BaseModel


class FilePreviewRead(BaseModel):
    id: uuid.UUID
    file_id: uuid.UUID
    preview_type: str
    preview_data: dict
    created_at: datetime

    class Config:
        from_attributes = True