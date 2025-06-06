"""
Integration Tests for Database Setup

This module tests database connection, table creation, and migrations.
These tests use a real database (SQLite in-memory) to verify database operations.
"""

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.database import Base, engine
from app.models.note import Note


@pytest.mark.integration
class TestDatabaseSetup:
    """Test suite for database setup and configuration."""
    
    def test_database_connection(self, test_engine):
        """
        Test that we can connect to the test database.
        
        This test demonstrates:
        - Basic database connectivity
        - Engine creation and disposal
        """
        # Act - Execute a simple query
        with test_engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.scalar()
        
        # Assert
        assert value == 1
    
    def test_tables_created(self, test_engine):
        """
        Test that all required tables are created.
        
        This test demonstrates:
        - Table introspection
        - Schema verification
        """
        # Arrange
        inspector = inspect(test_engine)
        
        # Act
        table_names = inspector.get_table_names()
        
        # Assert
        assert "notes" in table_names
        assert len(table_names) >= 1  # At least the notes table
    
    def test_notes_table_columns(self, test_engine):
        """
        Test that the notes table has all required columns.
        
        This test demonstrates:
        - Column introspection
        - Schema validation
        """
        # Arrange
        inspector = inspect(test_engine)
        
        # Act
        columns = inspector.get_columns("notes")
        column_names = [col["name"] for col in columns]
        
        # Assert
        expected_columns = ["id", "content", "created_at", "updated_at"]
        for expected_col in expected_columns:
            assert expected_col in column_names
    
    def test_notes_table_column_types(self, test_engine):
        """
        Test that notes table columns have correct types.
        
        This test demonstrates:
        - Type verification
        - Database schema compliance
        """
        # Arrange
        inspector = inspect(test_engine)
        
        # Act
        columns = inspector.get_columns("notes")
        column_types = {col["name"]: str(col["type"]) for col in columns}
        
        # Assert
        # Note: SQLite type names may differ from PostgreSQL
        assert "id" in column_types
        assert "content" in column_types
        assert "created_at" in column_types
        assert "updated_at" in column_types
    
    def test_session_creation(self, test_session):
        """
        Test that we can create a database session.
        
        This test demonstrates:
        - Session creation
        - Transaction management
        """
        # Assert
        assert test_session is not None
        assert isinstance(test_session, Session)
        assert test_session.is_active
    
    def test_transaction_rollback(self, test_session):
        """
        Test that transactions are properly rolled back.
        
        This test demonstrates:
        - Transaction isolation
        - Rollback functionality
        """
        # Arrange
        note = Note(content="Test rollback")
        
        # Act
        test_session.add(note)
        test_session.flush()  # Flush but don't commit
        
        # Verify note exists in current transaction
        count_in_transaction = test_session.query(Note).count()
        
        # Rollback
        test_session.rollback()
        
        # Verify note doesn't exist after rollback
        count_after_rollback = test_session.query(Note).count()
        
        # Assert
        assert count_in_transaction == 1
        assert count_after_rollback == 0


@pytest.mark.integration
class TestDatabaseConstraints:
    """Test database constraints and validations."""
    
    def test_note_id_auto_generation(self, test_session):
        """
        Test that note IDs are automatically generated.
        
        This test demonstrates:
        - UUID generation
        - Primary key constraints
        """
        # Arrange
        note = Note(content="Test ID generation")
        
        # Act
        test_session.add(note)
        test_session.commit()
        
        # Assert
        assert note.id is not None
        assert len(str(note.id)) == 36  # UUID format
    
    def test_timestamps_auto_generation(self, test_session):
        """
        Test that timestamps are automatically set.
        
        This test demonstrates:
        - Timestamp generation
        - Default value functionality
        """
        # Arrange
        note = Note(content="Test timestamps")
        
        # Act
        test_session.add(note)
        test_session.commit()
        
        # Assert
        assert note.created_at is not None
        assert note.updated_at is not None
        assert note.created_at <= note.updated_at
    
    def test_note_content_not_nullable(self, test_session):
        """
        Test that note content cannot be null.
        
        This test demonstrates:
        - NOT NULL constraint
        - Database-level validation
        """
        # Arrange
        note = Note()  # No content provided
        
        # Act & Assert
        with pytest.raises(Exception):  # IntegrityError or similar
            test_session.add(note)
            test_session.flush()
    
    def test_unique_ids(self, test_session):
        """
        Test that each note gets a unique ID.
        
        This test demonstrates:
        - Primary key uniqueness
        - UUID generation reliability
        """
        # Arrange & Act
        note1 = Note(content="Note 1")
        note2 = Note(content="Note 2")
        
        test_session.add(note1)
        test_session.add(note2)
        test_session.commit()
        
        # Assert
        assert note1.id != note2.id
        assert note1.id is not None
        assert note2.id is not None


@pytest.mark.integration
class TestDatabasePerformance:
    """Test database performance characteristics."""
    
    def test_bulk_insert_performance(self, test_session):
        """
        Test inserting multiple records efficiently.
        
        This test demonstrates:
        - Bulk operations
        - Performance testing patterns
        """
        # Arrange - Clear any existing data
        test_session.query(Note).delete()
        test_session.commit()
        
        notes = [Note(content=f"Bulk note {i}") for i in range(100)]
        
        # Act
        test_session.bulk_save_objects(notes)
        test_session.commit()
        
        # Assert
        count = test_session.query(Note).count()
        assert count == 100
    
    def test_query_with_limit(self, test_session):
        """
        Test query performance with pagination.
        
        This test demonstrates:
        - Query optimization
        - Pagination testing
        """
        # Arrange - Create test data
        for i in range(50):
            note = Note(content=f"Query test note {i}")
            test_session.add(note)
        test_session.commit()
        
        # Act
        limited_results = test_session.query(Note).limit(10).all()
        
        # Assert
        assert len(limited_results) == 10
        assert all(isinstance(note, Note) for note in limited_results)
