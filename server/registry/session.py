# server/registry/session.py
import os
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

REGISTRY_URL = os.getenv("REGISTRY_DATABASE_URL", "sqlite+aiosqlite:///./data/registry.db")

registry_engine: AsyncEngine = create_async_engine(
    REGISTRY_URL, future=True, echo=os.getenv("SQL_ECHO", "0") == "1"
)

RegistrySessionLocal = sessionmaker(
    bind=registry_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False, autocommit=False
)

async def get_registry_session():
    async with RegistrySessionLocal() as session:
        yield session
