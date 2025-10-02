# server/registry/models.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, DateTime, func

class Base(DeclarativeBase): pass

class DbConnection(Base):
    __tablename__ = "db_connection"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)     # friendly label
    url: Mapped[str]  = mapped_column(String, nullable=False)     # DATABASE_URL (async)
    api_key: Mapped[str] = mapped_column(String, nullable=True)   # simple shared secret (plaintext for now)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_used_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), nullable=True)

class AppState(Base):
    __tablename__ = "app_state"
    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)
