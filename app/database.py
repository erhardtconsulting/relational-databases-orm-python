"""
Database Configuration

This module handles SQLAlchemy database setup, session management,
and dependency injection for the FastAPI application.
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings

# Get settings instance
settings = get_settings()

# Create SQLAlchemy engine with connection pooling
# Equivalent to Spring Boot's DataSource configuration
engine = create_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL statements in debug mode
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections after 1 hour
)

# Configure SQLite for testing if needed
if "sqlite" in settings.database_url:
    engine = create_engine(
        settings.database_url,
        echo=settings.debug,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # Keep objects usable after commit
)

# Create declarative base for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI.
    
    This function provides database sessions to FastAPI route handlers
    through dependency injection.
    
    The session is automatically closed after each request,
    ensuring proper resource management.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example usage in FastAPI routes:
        @app.get("/notes")
        def get_notes(db: Session = Depends(get_db)):
            return db.query(Note).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database sessions.
    
    This provides a context manager for database operations
    outside of FastAPI routes, ensuring proper session lifecycle
    management with automatic cleanup.
    
    Example:
        with get_db_context() as db:
            note = Note(content="Example")
            db.add(note)
            db.commit()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Optional: Add connection event listeners for debugging
if settings.debug:
    
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Enable foreign key constraints for SQLite."""
        if "sqlite" in settings.database_url:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()


# Database health check function
def check_database_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
