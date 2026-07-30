"""Auth routes — login endpoint.

POST /api/auth/login   returns a JWT access token (OAuth2 password flow)
GET  /api/auth/me      returns the currently authenticated user's info
"""
from __future__ import annotations

import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from backend.auth import create_access_token, get_current_user
from backend.database import get_db, verify_password, _hash_password, User, Household

router = APIRouter()


@router.post("/login", summary="Obtain a JWT access token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == form_data.username, User.is_active == 1))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(username=user.username, role=user.role)
    return {
        "access_token": token,
        "token_type":   "bearer",
        "username":     user.username,
        "role":         user.role,
    }

class ResponderSignup(BaseModel):
    username: str
    password: str
    role: str # health_responder, police_responder, fire_responder, admin

@router.post("/signup/responder", summary="Register a new responder account")
async def signup_responder(data: ResponderSignup, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already registered")
        
    new_user = User(
        username=data.username,
        password_hash=_hash_password(data.password),
        role=data.role
    )
    db.add(new_user)
    await db.commit()
    return {"status": "success", "username": data.username, "role": data.role}

class HouseholdSignup(BaseModel):
    owner_name: str
    address: str
    lat: float
    lng: float
    phone: str

@router.post("/signup/household", summary="Register a new household device")
async def signup_household(data: HouseholdSignup, db: AsyncSession = Depends(get_db)):
    device_token = "dev_" + secrets.token_hex(12)
    new_house = Household(
        owner_name=data.owner_name,
        address=data.address,
        lat=data.lat,
        lng=data.lng,
        phone=data.phone,
        device_token=device_token
    )
    db.add(new_house)
    await db.commit()
    return {
        "status": "success", 
        "owner_name": data.owner_name, 
        "device_token": device_token
    }

@router.get("/me", summary="Get current user info")
async def get_me(user: dict = Depends(get_current_user)):
    return user
