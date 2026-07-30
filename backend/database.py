"""Database setup and SQLAlchemy models for MTEAS Postgres backend."""
from __future__ import annotations

import os
import hashlib
import secrets
from typing import AsyncGenerator
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:Ab%40123456@localhost/mteas"
)
# Render provides "postgres://" — asyncpg requires "postgresql+asyncpg://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class Household(Base):
    __tablename__ = "households"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    phone = Column(String, nullable=False)
    device_token = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String, nullable=False, index=True)
    keyword = Column(String, nullable=False)
    clap_count = Column(Integer, default=0, nullable=False)
    category = Column(String)
    modifier_phrase = Column(String)
    outcome = Column(String, default="activated", nullable=False)
    household_id = Column(Integer, ForeignKey("households.id"), index=True, nullable=True) # True for legacy compatibility
    device_id = Column(String, nullable=False, default="local") # Legacy support
    dispatch_text = Column(String)
    responder_name = Column(String)
    responded_at = Column(String)
    responder_notes = Column(String)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260_000)
    return salt.hex() + ":" + key.hex()

def verify_password(plain: str, stored: str) -> bool:
    try:
        salt_hex, key_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt, 260_000)
        return secrets.compare_digest(key.hex(), key_hex)
    except Exception:
        return False

# Default seed accounts
_SEED_USERS = [
    ("admin",              "admin123",   "admin"),
    ("responder_health",   "health123",  "health_responder"),
    ("responder_police",   "police123",  "police_responder"),
    ("responder_fire",     "fire123",    "fire_responder"),
]

async def init_db() -> None:
    """Create schema and seed users on first run."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Additive migration: create_all() won't alter an already-existing
        # table, so add newly-introduced nullable columns manually.
        from sqlalchemy import text
        await conn.execute(text(
            "ALTER TABLE events ADD COLUMN IF NOT EXISTS modifier_phrase VARCHAR"
        ))
        await conn.execute(text(
            "ALTER TABLE events ADD COLUMN IF NOT EXISTS responder_notes VARCHAR"
        ))

    async with async_session() as db:
        from sqlalchemy import select, func
        
        # Seed users if empty
        result = await db.execute(select(func.count(User.id)))
        if result.scalar() == 0:
            for uname, pw, role in _SEED_USERS:
                db.add(User(username=uname, password_hash=_hash_password(pw), role=role))
            await db.commit()
            print("[DB] Seed users created in PostgreSQL.")
            
        # Seed a dummy household for map testing
        result = await db.execute(select(func.count(Household.id)))
        if result.scalar() == 0:
            db.add(Household(
                owner_name="Test Home (Rwanda)",
                address="KN 3 Ave, Kigali, Rwanda",
                lat=-1.9441,
                lng=30.0619,
                phone="+250 788 000 000",
                device_token="dev_kigali_123"
            ))
            await db.commit()
            print("[DB] Seed household created.")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
