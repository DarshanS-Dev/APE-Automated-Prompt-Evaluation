import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone
import bcrypt
import hashlib
from fastapi import HTTPException, Depends, Header
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User, Key
from app.config import settings

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

def hash_pass(raw: str) -> str:
    return bcrypt.hashpw(raw.encode(), bcrypt.gensalt()).decode()

def verify_pass(raw: str, hashed: str) -> bool:
    return bcrypt.checkpw(raw.encode(), hashed.encode())

def create_token(data: dict):
    to_encode = data.copy()
    expiry = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expiry})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except InvalidTokenError:          # replaces JWTError
        raise HTTPException(401, "Invalid token")
    
async def get_current_user_from_api_key(api_key: str = Header(..., alias="X-API-Key"), db: AsyncSession = Depends(get_db)):
    hashed = hash_api_key(api_key) 
    result = await db.execute(select(Key).where(Key.hashed_key == hashed))
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(401, "Invalid API Key")
    
    users = await db.execute(select(User).where(User.id == key.user_id))
    return users.scalar_one()