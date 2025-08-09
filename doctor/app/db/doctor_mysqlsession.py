from sqlalchemy.ext.asyncio import AsyncSession
from .mysql import SessionLocal
# from contextlib import asynccontextmanager

# @asynccontextmanager
async def get_async_doctordb():
    async with SessionLocal() as doctor_db:
        try:
            yield doctor_db
        finally:
            await doctor_db.close()