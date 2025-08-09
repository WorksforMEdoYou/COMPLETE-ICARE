from sqlalchemy.ext.asyncio import AsyncSession
from .mysqldb import SessionLocal
# from contextlib import asynccontextmanager

# @asynccontextmanager
async def get_async_sp_db() -> AsyncSession:
    async with SessionLocal() as sp_db:
        try:
            yield sp_db
        finally:
            await sp_db.close()