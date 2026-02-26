import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
# default to a local sqlite file if no DATABASE_URL provided (safe for development)
if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Only pass check_same_thread for sqlite
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """
    Dependency for FastAPI endpoints. Yields a DB session and ensures it's closed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
