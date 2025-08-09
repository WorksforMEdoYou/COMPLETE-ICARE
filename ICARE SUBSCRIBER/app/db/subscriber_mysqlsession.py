from sqlalchemy.ext.asyncio import AsyncSession
from .mysql import SessionLocal
# from contextlib import asynccontextmanager

# @asynccontextmanager
async def get_async_subscriberdb():
    async with SessionLocal() as subscriber_db:
        try:
            yield subscriber_db
        finally:
            await subscriber_db.close()