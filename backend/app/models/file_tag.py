import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class FileTag(Base):
    __tablename__ = "file_tags"

    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("files.id"),
        primary_key=True,
    )

    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tags.id"),
        primary_key=True,
    )

    file = relationship(
        "File",
        back_populates="file_tags",
    )

    tag = relationship(
        "Tag",
        back_populates="file_tags",
    )