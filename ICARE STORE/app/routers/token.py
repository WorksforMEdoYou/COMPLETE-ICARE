from fastapi import APIRouter, Depends, HTTPException, Body
from ..jwt import verify_token, create_access_token, REFRESH_SECRET_KEY, create_refresh_token
import logging

router = APIRouter()

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.post("/refresh-token")
async def refresh_access_token(refresh_token: str = Body(..., embed=True)):
    try:
        payload = await verify_token(refresh_token, secret_key=REFRESH_SECRET_KEY)
        mobile = payload.get("store_mobile")
        role = payload.get("role")

        if role != "store":
            raise HTTPException(status_code=403, detail="Only store users can refresh token")

        new_access_token = await create_access_token(data={"store_mobile": mobile, "role": role})
        new_refresh_token = await create_refresh_token(data={"store_mobile": mobile, "role": role})
        return {"access_token": new_access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.post("/access-token")
async def refresh_access_token(refresh_token: str = Body(..., embed=True)):
    try:
        payload = await verify_token(refresh_token, secret_key=REFRESH_SECRET_KEY)
        mobile = payload.get("store_mobile")
        role = payload.get("role")

        if role != "store":
            raise HTTPException(status_code=403, detail="Only store users can refresh token")

        new_access_token = await create_access_token(data={"store_mobile": mobile, "role": role})
        return {"access_token": new_access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid refresh token")