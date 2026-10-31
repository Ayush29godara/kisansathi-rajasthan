"""Database connection and session lifecycle management using SQLAlchemy."""

from typing import Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import StaticPool
from app.config import get_settings

settings = get_settings()

Base = declarative_base()

# Normalize postgres:// to postgresql:// if needed
db_url = settings.DATABASE_URL
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

if settings.ENVIRONMENT == "test":
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
elif db_url:
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        connect_args={"connect_timeout": 2},
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    engine = None
    SessionLocal = None

_db_reachable: Optional[bool] = None


def check_db_health() -> bool:
    """Execute simple ping query to check database responsiveness (cached after first failure)."""
    global _db_reachable
    if engine is None:
        return False
    if _db_reachable is False:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        _db_reachable = True
        return True
    except Exception:
        _db_reachable = False
        return False


def get_db() -> Generator[Optional[Session], None, None]:
    """
    Yield an active database session and close it upon request termination.
    In testing/offline environments where SessionLocal is None or unreachable, yields None.
    """
    if SessionLocal is None or not check_db_health():
        yield None
        return

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
