import uuid
from pydantic import BaseModel


class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class TagRead(TagBase):
    id: uuid.UUID

    class Config:
        from_attributes = True