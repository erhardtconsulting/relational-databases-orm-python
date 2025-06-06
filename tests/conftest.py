"""
Test Configuration and Fixtures

This module provides shared fixtures and configuration for all tests.
It demonstrates different approaches to database testing:
- Unit tests with mocked sessions
- Integration tests with real database connections
"""

import os
from typing import Generator
from unittest.mock import Mock, MagicMock

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.note import Note


# Test database URL - using SQLite for fast testing
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture(scope="session")
def test_engine():
    """
    Create a test database engine for the entire test session.
    
    This fixture creates a SQLite in-memory database that persists
    for the entire test session. Using StaticPool ensures the same
    connection is reused, keeping the in-memory database alive.
    """
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {},
        poolclass=StaticPool if "sqlite" in TEST_DATABASE_URL else None,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_session(test_engine) -> Generator[Session, None, None]:
    """
    Create a test database session for integration tests.
    
    This fixture provides a real database session that:
    - Starts a transaction at the beginning of each test
    - Rolls back the transaction at the end of each test
    - Ensures test isolation (no test pollution)
    
    This is the recommended pattern for database testing as it:
    - Keeps tests fast (no need to recreate tables)
    - Ensures isolation (each test gets a clean state)
    - Works with foreign keys and constraints
    """
    # Create a session factory bound to the test engine
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Create a new session
    session = TestSessionLocal()
    
    # Start a transaction
    session.begin()
    
    # Create a nested transaction (savepoint)
    nested = session.begin_nested()
    
    # If the session would commit, restart the nested transaction instead
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            # Ensure we're still in a transaction
            if session.in_transaction():
                session.begin_nested()
    
    yield session
    
    # Rollback the transaction to clean up test data
    session.rollback()
    session.close()


@pytest.fixture
def mock_session() -> Mock:
    """
    Create a mock database session for unit tests.
    
    This fixture provides a mocked SQLAlchemy session that:
    - Doesn't require a real database connection
    - Allows testing of business logic in isolation
    - Can be configured to return specific test data
    
    Use this for unit tests where you want to test the logic
    without the overhead of database operations.
    """
    mock = MagicMock(spec=Session)
    
    # Configure common session methods
    mock.add = MagicMock()
    mock.commit = MagicMock()
    mock.rollback = MagicMock()
    mock.refresh = MagicMock()
    mock.query = MagicMock()
    mock.delete = MagicMock()
    
    # Make query chainable
    mock.query.return_value = mock.query
    mock.query.filter.return_value = mock.query
    mock.query.filter_by.return_value = mock.query
    mock.query.first.return_value = None
    mock.query.all.return_value = []
    mock.query.offset.return_value = mock.query
    mock.query.limit.return_value = mock.query
    
    return mock


@pytest.fixture
def sample_note_data():
    """
    Provide sample note data for testing.
    
    This fixture returns a dictionary with valid note data
    that can be used across different tests.
    """
    return {
        "content": "This is a test note content for automated testing."
    }


@pytest.fixture
def long_note_data():
    """
    Provide sample data for a long note (edge case testing).
    """
    return {
        "content": "Lorem ipsum dolor sit amet. " * 100  # ~2000 characters
    }


@pytest.fixture
def create_test_note(test_session):
    """
    Factory fixture to create test notes in the database.
    
    This fixture returns a function that creates notes,
    allowing tests to easily set up test data.
    
    Example usage in tests:
        def test_something(create_test_note):
            note = create_test_note("Test content")
            # ... test with the note
    """
    def _create_note(content: str = "Test note") -> Note:
        note = Note(content=content)
        test_session.add(note)
        test_session.commit()
        test_session.refresh(note)
        return note
    
    return _create_note


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that don't require database"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests that use real database"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer to run"
    )


# Test environment setup
@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """
    Automatically set up test environment variables.
    
    This fixture runs automatically for all tests and ensures
    that test-specific environment variables are set.
    """
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-testing-only")
    monkeypatch.setenv("DEBUG", "false")
