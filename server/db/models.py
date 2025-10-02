# server/db/models.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime, Index, func

class Base(DeclarativeBase): pass

class UploadFile(Base):
    __tablename__ = "upload_file"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    original_name: Mapped[str] = mapped_column(String, nullable=False)
    saved_path: Mapped[str] = mapped_column(String, nullable=False)
    sha256: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    rows_loaded: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    relationships = relationship("Relationship", back_populates="dataset", cascade="all, delete-orphan")

class Relationship(Base):
    __tablename__ = "relationship"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("upload_file.id"), index=True, nullable=False)
    parent_item: Mapped[str] = mapped_column(String, index=True, nullable=False)
    child_item: Mapped[str]  = mapped_column(String, index=True, nullable=False)
    sequence_no: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    level: Mapped[int]       = mapped_column(Integer, index=True, nullable=False)

    dataset = relationship("UploadFile", back_populates="relationships")

Index("ix_rel_dataset_parent_seq", Relationship.dataset_id, Relationship.parent_item, Relationship.sequence_no)
Index("ix_rel_dataset_child", Relationship.dataset_id, Relationship.child_item)
