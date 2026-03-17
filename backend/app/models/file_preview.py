import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

class FilePreview(Base):
    __tablename__ = "file_previews"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, 
        default=uuid.uuid4
    )
    
    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"), 
        nullable=False,
    )

    preview_type: Mapped[str] = mapped_column(
        String, 
        nullable=False,
    )

    preview_data: Mapped[dict] = mapped_column(
        JSON, 
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    file = relationship("File", back_populates="previews")