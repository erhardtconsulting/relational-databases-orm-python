"""
Unit Tests for Note Service

This module tests the NoteService business logic using mocked database sessions.
Unit tests focus on testing the logic in isolation without real database dependencies.
"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models.note import Note
from app.schemas.note import NoteCreate
from app.services.note_service import NoteService
from tests.factories import NoteFactory, NoteCreateFactory, NoteUpdateFactory


@pytest.mark.unit
class TestNoteService:
    """Test suite for NoteService business logic."""
    
    def test_create_note_success(self, mock_session):
        """
        Test successful note creation.
        
        This test demonstrates:
        - Mocking database session behavior
        - Testing service method without real DB
        - Verifying correct method calls
        """
        # Arrange
        service = NoteService(mock_session)
        note_data = NoteCreateFactory()
        expected_note = NoteFactory(content=note_data.content)
        
        # Configure mock to return our expected note when refresh is called
        mock_session.refresh.side_effect = lambda obj: setattr(obj, 'id', expected_note.id)
        
        # Act
        result = service.create_note(note_data)
        
        # Assert
        assert result.content == note_data.content
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
    
    def test_create_note_database_error(self, mock_session):
        """
        Test note creation with database error.
        
        This test demonstrates:
        - Simulating database errors
        - Testing error handling
        - Verifying rollback behavior
        """
        # Arrange
        service = NoteService(mock_session)
        note_data = NoteCreateFactory()
        
        # Configure mock to raise an error on commit
        mock_session.commit.side_effect = SQLAlchemyError("Database connection failed")
        
        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            service.create_note(note_data)
        
        # Verify rollback was called
        mock_session.rollback.assert_called_once()
    
    def test_get_note_by_id_found(self, mock_session):
        """
        Test retrieving a note by ID when it exists.
        
        This test demonstrates:
        - Mocking query chain behavior
        - Testing retrieval logic
        - Verifying correct filtering
        """
        # Arrange
        service = NoteService(mock_session)
        note_id = uuid4()
        expected_note = NoteFactory(id=note_id)
        
        # Configure mock query chain
        mock_session.query.return_value.filter.return_value.first.return_value = expected_note
        
        # Act
        result = service.get_note_by_id(note_id)
        
        # Assert
        assert result == expected_note
        assert result.id == note_id
        mock_session.query.assert_called_with(Note)
        mock_session.query.return_value.filter.assert_called_once()
    
    def test_get_note_by_id_not_found(self, mock_session):
        """
        Test retrieving a note by ID when it doesn't exist.
        
        This test demonstrates:
        - Testing None return value
        - Handling non-existent resources
        """
        # Arrange
        service = NoteService(mock_session)
        note_id = uuid4()
        
        # Configure mock to return None
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = service.get_note_by_id(note_id)
        
        # Assert
        assert result is None
    
    def test_get_all_notes_with_pagination(self, mock_session):
        """
        Test retrieving all notes with pagination.
        
        This test demonstrates:
        - Testing pagination logic
        - Mocking query chain with offset/limit
        """
        # Arrange
        service = NoteService(mock_session)
        expected_notes = NoteFactory.create_batch(5)
        skip = 10
        limit = 5
        
        # Configure mock query chain
        mock_query = mock_session.query.return_value
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = expected_notes
        
        # Act
        result = service.get_all_notes(skip=skip, limit=limit)
        
        # Assert
        assert result == expected_notes
        assert len(result) == 5
        mock_query.offset.assert_called_with(skip)
        mock_query.limit.assert_called_with(limit)
    
    def test_update_note_success(self, mock_session):
        """
        Test successful note update.
        
        This test demonstrates:
        - Testing update logic
        - Mocking existing object retrieval
        - Verifying update method calls
        """
        # Arrange
        service = NoteService(mock_session)
        note_id = uuid4()
        existing_note = NoteFactory(id=note_id, content="Old content")
        update_data = NoteUpdateFactory(content="New content")
        
        # Configure mock to return existing note
        mock_session.query.return_value.filter.return_value.first.return_value = existing_note
        
        # Mock the update_content method
        existing_note.update_content = MagicMock()
        
        # Act
        result = service.update_note(note_id, update_data)
        
        # Assert
        assert result == existing_note
        existing_note.update_content.assert_called_once_with(update_data.content)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(existing_note)
    
    def test_update_note_not_found(self, mock_session):
        """
        Test updating a non-existent note.
        
        This test demonstrates:
        - Handling update of non-existent resources
        - Verifying no database changes occur
        """
        # Arrange
        service = NoteService(mock_session)
        note_id = uuid4()
        update_data = NoteUpdateFactory()
        
        # Configure mock to return None (note not found)
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = service.update_note(note_id, update_data)
        
        # Assert
        assert result is None
        mock_session.commit.assert_not_called()
    
    def test_update_note_database_error(self, mock_session):
        """
        Test note update with database error.
        
        This test demonstrates:
        - Error handling during updates
        - Rollback on failure
        """
        # Arrange
        service = NoteService(mock_session)
        note_id = uuid4()
        existing_note = NoteFactory(id=note_id)
        update_data = NoteUpdateFactory()
        
        # Configure mock
        mock_session.query.return_value.filter.return_value.first.return_value = existing_note
        existing_note.update_content = MagicMock()
        mock_session.commit.side_effect = SQLAlchemyError("Update failed")
        
        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            service.update_note(note_id, update_data)
        
        mock_session.rollback.assert_called_once()
    
    def test_delete_note_success(self, mock_session):
        """
        Test successful note deletion.
        
        This test demonstrates:
        - Testing deletion logic
        - Verifying delete method calls
        """
        # Arrange
        service = NoteService(mock_session)
        note_id = uuid4()
        existing_note = NoteFactory(id=note_id)
        
        # Configure mock
        mock_session.query.return_value.filter.return_value.first.return_value = existing_note
        
        # Act
        result = service.delete_note(note_id)
        
        # Assert
        assert result is True
        mock_session.delete.assert_called_once_with(existing_note)
        mock_session.commit.assert_called_once()
    
    def test_delete_note_not_found(self, mock_session):
        """
        Test deleting a non-existent note.
        
        This test demonstrates:
        - Handling deletion of non-existent resources
        - Returning appropriate boolean result
        """
        # Arrange
        service = NoteService(mock_session)
        note_id = uuid4()
        
        # Configure mock to return None
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = service.delete_note(note_id)
        
        # Assert
        assert result is False
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()
    
    def test_delete_note_database_error(self, mock_session):
        """
        Test note deletion with database error.
        
        This test demonstrates:
        - Error handling during deletion
        - Rollback on failure
        """
        # Arrange
        service = NoteService(mock_session)
        note_id = uuid4()
        existing_note = NoteFactory(id=note_id)
        
        # Configure mock
        mock_session.query.return_value.filter.return_value.first.return_value = existing_note
        mock_session.commit.side_effect = SQLAlchemyError("Delete failed")
        
        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            service.delete_note(note_id)
        
        mock_session.rollback.assert_called_once()


@pytest.mark.unit
class TestNoteServiceEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_create_note_with_whitespace_content(self, mock_session):
        """Test creating a note with content that needs trimming."""
        # Arrange
        service = NoteService(mock_session)
        note_data = NoteCreate(content="  Trimmed content  ")
        
        # Act
        result = service.create_note(note_data)
        
        # Assert
        # The content should be trimmed by the Pydantic validator
        assert result.content == "Trimmed content"
    
    def test_get_all_notes_empty_database(self, mock_session):
        """Test retrieving notes when database is empty."""
        # Arrange
        service = NoteService(mock_session)
        mock_session.query.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        # Act
        result = service.get_all_notes()
        
        # Assert
        assert result == []
        assert len(result) == 0
    
    def test_get_all_notes_with_default_pagination(self, mock_session):
        """Test get_all_notes with default pagination values."""
        # Arrange
        service = NoteService(mock_session)
        expected_notes = NoteFactory.create_batch(3)
        
        # Configure mock
        mock_query = mock_session.query.return_value
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = expected_notes
        
        # Act
        result = service.get_all_notes()  # Using default skip=0, limit=100
        
        # Assert
        assert result == expected_notes
        mock_query.offset.assert_called_with(0)
        mock_query.limit.assert_called_with(100)
