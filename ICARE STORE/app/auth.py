from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from .jwt import verify_token
from sqlalchemy.ext.asyncio import AsyncSession
from .db.mysql_session import get_async_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/storeapi/token")

async def get_current_store_user(
    token: str = Depends(oauth2_scheme)):
    try:
        payload = await verify_token(token)
        mobile = payload.get("store_mobile") 

        if payload.get("role") != "store":
            raise HTTPException(status_code=403, detail="Access forbidden: Not a store user")
        return mobile
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token" + str(e))
