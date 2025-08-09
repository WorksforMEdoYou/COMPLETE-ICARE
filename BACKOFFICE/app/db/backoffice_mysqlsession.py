from sqlalchemy.ext.asyncio import AsyncSession
from .mysql import SessionLocal
# from contextlib import asynccontextmanager

# @asynccontextmanager
async def get_async_backofficedb():
    async with SessionLocal() as backoffice_db:
        try:
            yield backoffice_db
        finally:
            await backoffice_db.close()