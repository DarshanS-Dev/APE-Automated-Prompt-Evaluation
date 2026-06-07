from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import hashlib
from fastapi import HTTPException, Depends, Header
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User, Key
from app.config import settings

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

def hash_pass(raw: str):
    return pwd_context.hash(raw)

def verify_pass(raw_password: str, hashed: str):
    return pwd_context.verify(raw_password, hashed)

def create_token(data: dict):
    to_encode = data.copy()
    expiry = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expiry})
    return jwt.encode(to_encode, settings.secret_key, algorithms=[settings.algorithm])

def verify_token(token: str):
    try: 
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        raise HTTPException(401, "Invalid token")
    
async def get_current_user_from_api_key(api_key: str = Header(..., alias="X-API-Key"), db: AsyncSession = Depends(get_db)):
    hashed = hash_api_key(api_key) 
    result = await db.execute(select(Key).where(Key.hashed_key == hashed))
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(401, "Invalid API Key")
    
    users = await db.execute(select(User).where(User.id == key.user_id))
    return users.scalar_one()