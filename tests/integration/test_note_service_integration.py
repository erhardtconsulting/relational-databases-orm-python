"""
Integration Tests for Note Service with Real Database

This module tests the NoteService with actual database operations.
These tests verify that the service layer works correctly with a real database.
"""

from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models.note import Note
from app.schemas.note import NoteCreate, NoteUpdate
from app.services.note_service import NoteService, get_note_service
from tests.factories import create_note_with_session, create_multiple_notes


@pytest.mark.integration
class TestNoteServiceIntegration:
    """Test suite for NoteService with real database operations."""
    
    def test_create_note_integration(self, test_session):
        """
        Test creating a note with real database.
        
        This test demonstrates:
        - Service integration with database
        - Actual data persistence
        - ID and timestamp generation
        """
        # Arrange
        service = NoteService(test_session)
        note_data = NoteCreate(content="Integration test note")
        
        # Act
        created_note = service.create_note(note_data)
        
        # Assert
        assert created_note.id is not None
        assert created_note.content == "Integration test note"
        assert created_note.created_at is not None
        assert created_note.updated_at is not None
        
        # Verify persistence
        db_note = test_session.query(Note).filter_by(id=created_note.id).first()
        assert db_note is not None
        assert db_note.content == "Integration test note"
    
    def test_get_note_by_id_integration(self, test_session):
        """
        Test retrieving a note by ID from real database.
        
        This test demonstrates:
        - Data retrieval from database
        - Service query functionality
        """
        # Arrange
        service = NoteService(test_session)
        test_note = create_note_with_session(test_session, content="Test retrieval")
        
        # Act
        retrieved_note = service.get_note_by_id(test_note.id)
        
        # Assert
        assert retrieved_note is not None
        assert retrieved_note.id == test_note.id
        assert retrieved_note.content == "Test retrieval"
    
    def test_get_note_by_id_not_found_integration(self, test_session):
        """Test retrieving non-existent note returns None."""
        # Arrange
        service = NoteService(test_session)
        non_existent_id = uuid4()
        
        # Act
        result = service.get_note_by_id(non_existent_id)
        
        # Assert
        assert result is None
    
    def test_get_all_notes_integration(self, test_session):
        """
        Test retrieving all notes from database.
        
        This test demonstrates:
        - Bulk retrieval operations
        - Pagination functionality
        """
        # Arrange - Clear any existing data first
        test_session.query(Note).delete()
        test_session.commit()
        
        service = NoteService(test_session)
        created_notes = create_multiple_notes(test_session, count=5)
        
        # Act
        all_notes = service.get_all_notes()
        
        # Assert
        assert len(all_notes) == 5
        assert all(isinstance(note, Note) for note in all_notes)
        
        # Verify content
        note_contents = [note.content for note in all_notes]
        for created_note in created_notes:
            assert any(created_note.content in content for content in note_contents)
    
    def test_get_all_notes_with_pagination_integration(self, test_session):
        """Test pagination works correctly with real data."""
        # Arrange
        service = NoteService(test_session)
        create_multiple_notes(test_session, count=20)
        
        # Act
        page1 = service.get_all_notes(skip=0, limit=5)
        page2 = service.get_all_notes(skip=5, limit=5)
        page3 = service.get_all_notes(skip=10, limit=5)
        
        # Assert
        assert len(page1) == 5
        assert len(page2) == 5
        assert len(page3) == 5
        
        # Ensure no overlap between pages
        page1_ids = {note.id for note in page1}
        page2_ids = {note.id for note in page2}
        page3_ids = {note.id for note in page3}
        
        assert page1_ids.isdisjoint(page2_ids)
        assert page2_ids.isdisjoint(page3_ids)
        assert page1_ids.isdisjoint(page3_ids)
    
    def test_update_note_integration(self, test_session):
        """
        Test updating a note in the database.
        
        This test demonstrates:
        - Update operations
        - Timestamp updates
        - Data persistence
        """
        # Arrange
        service = NoteService(test_session)
        original_note = create_note_with_session(test_session, content="Original content")
        original_updated_at = original_note.updated_at
        
        # Sleep to ensure timestamp difference (SQLite truncates microseconds)
        import time
        time.sleep(1.1)
        
        update_data = NoteUpdate(content="Updated content")
        
        # Act
        updated_note = service.update_note(original_note.id, update_data)
        
        # Assert
        assert updated_note is not None
        assert updated_note.id == original_note.id
        assert updated_note.content == "Updated content"
        assert updated_note.updated_at > original_updated_at
        
        # Verify persistence
        db_note = test_session.query(Note).filter_by(id=original_note.id).first()
        assert db_note.content == "Updated content"
    
    def test_update_non_existent_note_integration(self, test_session):
        """Test updating non-existent note returns None."""
        # Arrange
        service = NoteService(test_session)
        non_existent_id = uuid4()
        update_data = NoteUpdate(content="This won't work")
        
        # Act
        result = service.update_note(non_existent_id, update_data)
        
        # Assert
        assert result is None
    
    def test_delete_note_integration(self, test_session):
        """
        Test deleting a note from the database.
        
        This test demonstrates:
        - Delete operations
        - Verification of deletion
        """
        # Arrange
        service = NoteService(test_session)
        note_to_delete = create_note_with_session(test_session, content="To be deleted")
        note_id = note_to_delete.id
        
        # Act
        delete_result = service.delete_note(note_id)
        
        # Assert
        assert delete_result is True
        
        # Verify deletion
        deleted_note = test_session.query(Note).filter_by(id=note_id).first()
        assert deleted_note is None
    
    def test_delete_non_existent_note_integration(self, test_session):
        """Test deleting non-existent note returns False."""
        # Arrange
        service = NoteService(test_session)
        non_existent_id = uuid4()
        
        # Act
        result = service.delete_note(non_existent_id)
        
        # Assert
        assert result is False
    
    def test_get_note_service_factory(self, test_session):
        """Test the service factory function."""
        # Act
        service = get_note_service(test_session)
        
        # Assert
        assert isinstance(service, NoteService)
        assert service.db == test_session


@pytest.mark.integration
class TestNoteServiceTransactions:
    """Test transaction behavior and error handling."""
    
    def test_rollback_on_error(self, test_session):
        """
        Test that transactions are rolled back on error.
        
        This test demonstrates:
        - Transaction isolation
        - Error recovery
        """
        # Arrange
        service = NoteService(test_session)
        initial_count = test_session.query(Note).count()
        
        # Create a note but simulate an error before commit
        note_data = NoteCreate(content="This will be rolled back")
        
        try:
            # Start creating the note
            db_note = Note(content=note_data.content)
            test_session.add(db_note)
            
            # Simulate an error
            raise SQLAlchemyError("Simulated database error")
            
        except SQLAlchemyError:
            test_session.rollback()
        
        # Assert
        final_count = test_session.query(Note).count()
        assert final_count == initial_count
    
    def test_concurrent_updates(self, test_session):
        """
        Test behavior with concurrent-like updates.
        
        This test demonstrates:
        - Last-write-wins behavior
        - Update consistency
        """
        # Arrange
        service = NoteService(test_session)
        note = create_note_with_session(test_session, content="Initial content")
        
        # Act - Simulate two "concurrent" updates
        update1 = NoteUpdate(content="Update 1")
        update2 = NoteUpdate(content="Update 2")
        
        service.update_note(note.id, update1)
        final_note = service.update_note(note.id, update2)
        
        # Assert
        assert final_note.content == "Update 2"
        
        # Verify in database
        db_note = test_session.query(Note).filter_by(id=note.id).first()
        assert db_note.content == "Update 2"


@pytest.mark.integration
class TestNoteServiceEdgeCases:
    """Test edge cases and boundary conditions with real database."""
    
    def test_very_long_content(self, test_session):
        """Test handling of maximum length content."""
        # Arrange
        service = NoteService(test_session)
        long_content = "x" * 5000  # Maximum allowed length
        note_data = NoteCreate(content=long_content)
        
        # Act
        created_note = service.create_note(note_data)
        
        # Assert
        assert created_note is not None
        assert len(created_note.content) == 5000
        assert created_note.content == long_content
    
    def test_unicode_content_persistence(self, test_session):
        """Test that Unicode content is properly stored and retrieved."""
        # Arrange
        service = NoteService(test_session)
        unicode_content = "Hello 你好 مرحبا שלום 🌍🎉"
        note_data = NoteCreate(content=unicode_content)
        
        # Act
        created_note = service.create_note(note_data)
        retrieved_note = service.get_note_by_id(created_note.id)
        
        # Assert
        assert retrieved_note.content == unicode_content
    
    def test_empty_database_pagination(self, test_session):
        """Test pagination on empty database."""
        # Arrange
        service = NoteService(test_session)
        
        # Ensure database is empty
        test_session.query(Note).delete()
        test_session.commit()
        
        # Act
        results = service.get_all_notes(skip=0, limit=10)
        
        # Assert
        assert results == []
        assert len(results) == 0
    
    def test_update_maintains_created_at(self, test_session):
        """Test that updates don't change created_at timestamp."""
        # Arrange
        service = NoteService(test_session)
        note = create_note_with_session(test_session, content="Original")
        original_created_at = note.created_at
        
        # Sleep to ensure timestamp difference (SQLite truncates microseconds) 
        import time
        time.sleep(1.1)
        
        # Act
        update_data = NoteUpdate(content="Updated")
        updated_note = service.update_note(note.id, update_data)
        
        # Assert
        assert updated_note.created_at == original_created_at
        assert updated_note.updated_at > original_created_at
