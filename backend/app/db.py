"""Database connection and session lifecycle management using SQLAlchemy."""

from typing import Generator, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.config import get_settings

settings = get_settings()

Base = declarative_base()

# Configure SQLAlchemy engine if DATABASE_URL is provided
if settings.DATABASE_URL:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    engine = None
    SessionLocal = None


def get_db() -> Generator[Optional[Session], None, None]:
    """
    Yield a database session and safely close it on request completion.
    In testing/scaffold mode where DATABASE_URL is absent, yields None gracefully.
    """
    if SessionLocal is None:
        yield None
        return

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
