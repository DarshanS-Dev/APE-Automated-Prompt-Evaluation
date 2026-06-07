from fastapi import APIRouter, Depends, HTTPException
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.database import get_db
from app import auth

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model= schemas.UserResponse)
async def register (user: schemas.UserInput, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.email==user.email))
    is_exists = result.scalar_one_or_none()

    if is_exists:
        raise HTTPException(400, "Email already exists")
    
    hashed_password = auth.hash_pass(user.password)

    new_user = models.User(email= user.email, hashed_password= hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    data = {"sub": new_user.id}
    return {"token":auth.create_token(data)}

@router.post("/login", response_model= schemas.UserResponse)
async def login (user: schemas.UserInput, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.email==user.email))
    curr_user = result.scalar_one_or_none()

    if not curr_user:
        raise HTTPException(401, "Invalid email")
    
    if not auth.verify_pass(user.password, curr_user.hashed_password):
        raise HTTPException(401, "Invalid password")
    
    data = {"sub": curr_user.id}
    return {"token":auth.create_token(data)}

@router.post("/key", response_model=schemas.ApiKeyResponse)
async def key (token = Depends(auth.oauth2), db: AsyncSession = Depends(get_db)):
    payload = auth.verify_token(token)

    api_key = secrets.token_urlsafe(32)

    new_key = models.Key(
        hashed_key = auth.hash_api_key(api_key),
        user_id = payload["sub"]
    )

    db.add(new_key)
    await db.commit()

    return {"key": api_key}
