"""
Unit Tests for Pydantic Schemas

This module tests the Pydantic schemas for data validation.
These tests ensure that our request/response models properly validate data.
"""

import pytest
from pydantic import ValidationError

from app.schemas.note import NoteCreate, NoteUpdate, NoteBase


@pytest.mark.unit
class TestNoteSchemas:
    """Test suite for Note Pydantic schemas."""
    
    def test_note_create_valid_content(self):
        """Test creating a NoteCreate schema with valid content."""
        # Arrange
        valid_content = "This is a valid note content"
        
        # Act
        note = NoteCreate(content=valid_content)
        
        # Assert
        assert note.content == valid_content
    
    def test_note_create_strips_whitespace(self):
        """Test that NoteCreate strips leading/trailing whitespace."""
        # Arrange
        content_with_whitespace = "  Content with spaces  "
        
        # Act
        note = NoteCreate(content=content_with_whitespace)
        
        # Assert
        assert note.content == "Content with spaces"
    
    def test_note_create_empty_content_fails(self):
        """Test that empty content raises validation error."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            NoteCreate(content="")
        
        # Verify the error message
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "content" in str(errors[0]['loc'])
    
    def test_note_create_whitespace_only_fails(self):
        """Test that whitespace-only content raises validation error."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            NoteCreate(content="   ")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "cannot be empty or whitespace only" in str(errors[0]['msg'])
    
    def test_note_create_exceeds_max_length(self):
        """Test that content exceeding max length raises validation error."""
        # Arrange
        long_content = "x" * 5001  # Exceeds 5000 character limit
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            NoteCreate(content=long_content)
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        # The actual Pydantic error message
        assert "at most 5000 characters" in str(errors[0]['msg'])
    
    def test_note_create_at_max_length(self):
        """Test that content at exactly max length is valid."""
        # Arrange
        max_content = "x" * 5000  # Exactly at limit
        
        # Act
        note = NoteCreate(content=max_content)
        
        # Assert
        assert note.content == max_content
        assert len(note.content) == 5000
    
    def test_note_create_minimum_valid_content(self):
        """Test that single character content is valid."""
        # Act
        note = NoteCreate(content="a")
        
        # Assert
        assert note.content == "a"
    
    def test_note_update_schema(self):
        """Test NoteUpdate schema behaves the same as NoteCreate."""
        # Arrange
        content = "Updated content"
        
        # Act
        note = NoteUpdate(content=content)
        
        # Assert
        assert note.content == content
    
    def test_note_update_validation_rules(self):
        """Test that NoteUpdate has the same validation rules as NoteCreate."""
        # Test empty content
        with pytest.raises(ValidationError):
            NoteUpdate(content="")
        
        # Test whitespace only
        with pytest.raises(ValidationError):
            NoteUpdate(content="   ")
        
        # Test valid content
        note = NoteUpdate(content="Valid update")
        assert note.content == "Valid update"
    
    def test_note_base_field_metadata(self):
        """Test that field metadata is properly set."""
        # Check field info
        content_field = NoteBase.model_fields['content']
        
        # Assert field constraints are in metadata
        # Metadata contains constraint objects
        metadata = content_field.metadata
        assert len(metadata) == 2  # Should have MinLen and MaxLen constraints
        
        # Check constraints
        min_constraint = metadata[0]  # MinLen
        max_constraint = metadata[1]  # MaxLen
        
        assert hasattr(min_constraint, 'min_length')
        assert min_constraint.min_length == 1
        
        assert hasattr(max_constraint, 'max_length')
        assert max_constraint.max_length == 5000
        
        # Check field description
        assert content_field.description == "The text content of the note"
    
    def test_schema_json_serialization(self):
        """Test that schemas can be serialized to JSON."""
        # Arrange
        note = NoteCreate(content="Test content")
        
        # Act
        json_data = note.model_dump_json()
        
        # Assert
        assert '"content":"Test content"' in json_data
    
    def test_schema_dict_serialization(self):
        """Test that schemas can be converted to dictionaries."""
        # Arrange
        note = NoteCreate(content="Test content")
        
        # Act
        dict_data = note.model_dump()
        
        # Assert
        assert dict_data == {"content": "Test content"}
    
    def test_special_characters_in_content(self):
        """Test that special characters are handled correctly."""
        # Arrange
        special_content = "Note with émojis 😀 and special chars: @#$%"
        
        # Act
        note = NoteCreate(content=special_content)
        
        # Assert
        assert note.content == special_content
    
    def test_multiline_content(self):
        """Test that multiline content is preserved."""
        # Arrange
        multiline_content = """Line 1
Line 2
Line 3"""
        
        # Act
        note = NoteCreate(content=multiline_content)
        
        # Assert
        assert note.content == multiline_content
        assert "\n" in note.content


@pytest.mark.unit
class TestSchemaEdgeCases:
    """Test edge cases and boundary conditions for schemas."""
    
    def test_note_with_only_spaces_between_words(self):
        """Test content with multiple spaces between words."""
        # Arrange
        content = "Word1     Word2     Word3"
        
        # Act
        note = NoteCreate(content=content)
        
        # Assert
        # Content should be preserved as-is (only leading/trailing stripped)
        assert note.content == content
    
    def test_note_with_unicode_characters(self):
        """Test content with various Unicode characters."""
        # Arrange
        unicode_content = "测试 テスト тест 🌍"
        
        # Act
        note = NoteCreate(content=unicode_content)
        
        # Assert
        assert note.content == unicode_content
    
    def test_missing_content_field(self):
        """Test that missing content field raises appropriate error."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            NoteCreate()
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]['type'] == 'missing'
        assert 'content' in str(errors[0]['loc'])
