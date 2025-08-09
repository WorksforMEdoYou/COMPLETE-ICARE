from sqlalchemy.ext.asyncio import AsyncSession
from .mysql import SessionLocal
# from contextlib import asynccontextmanager

# @asynccontextmanager
async def get_async_db():
    async with SessionLocal() as db:
        yield db