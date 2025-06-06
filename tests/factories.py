"""
Test Data Factories

This module provides factory classes for generating test data.
Using the Factory Boy pattern makes it easy to create test objects
with realistic data and helps maintain DRY principles in tests.
"""

import factory
from factory.fuzzy import FuzzyText
from datetime import datetime, timezone
from uuid import uuid4

from app.models.note import Note
from app.schemas.note import NoteCreate, NoteUpdate


class NoteFactory(factory.Factory):
    """
    Factory for creating Note model instances.
    
    This factory generates Note objects with realistic test data.
    It can be used in both unit tests (without DB) and integration
    tests (with DB session).
    
    Example usage:
        # Create a note instance
        note = NoteFactory()
        
        # Create with custom content
        note = NoteFactory(content="Custom content")
        
        # Create multiple notes
        notes = NoteFactory.create_batch(5)
    """
    
    class Meta:
        model = Note
    
    # Generate random content for each note
    content = FuzzyText(length=50, prefix="Test Note: ")
    
    # ID and timestamps are typically set by the database
    # but we can provide defaults for unit tests
    id = factory.LazyFunction(uuid4)
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)


class NoteCreateFactory(factory.Factory):
    """
    Factory for creating NoteCreate schema instances.
    
    This factory generates valid request data for creating notes.
    Useful for testing API endpoints and service methods.
    """
    
    class Meta:
        model = NoteCreate
    
    content = factory.Faker(
        "paragraph",
        nb_sentences=3,
        variable_nb_sentences=True
    )


class NoteUpdateFactory(factory.Factory):
    """
    Factory for creating NoteUpdate schema instances.
    
    This factory generates valid request data for updating notes.
    """
    
    class Meta:
        model = NoteUpdate
    
    content = factory.Faker(
        "paragraph",
        nb_sentences=2,
        variable_nb_sentences=True
    )


# Specialized factories for edge cases
class EmptyNoteFactory(NoteCreateFactory):
    """Factory for creating notes with empty content (should fail validation)."""
    content = ""


class LongNoteFactory(NoteCreateFactory):
    """Factory for creating notes with very long content."""
    content = factory.LazyFunction(lambda: "x" * 10001)  # Exceeds max length


class MinimalNoteFactory(NoteCreateFactory):
    """Factory for creating notes with minimal valid content."""
    content = "a"  # Single character - minimum valid


# Helper functions for common test scenarios
def create_note_with_session(session, **kwargs):
    """
    Helper function to create and persist a note in the database.
    
    Args:
        session: SQLAlchemy session
        **kwargs: Override default factory attributes
        
    Returns:
        Note: Persisted note instance
    """
    note = NoteFactory(**kwargs)
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


def create_multiple_notes(session, count=5, **kwargs):
    """
    Helper function to create multiple notes in the database.
    
    Args:
        session: SQLAlchemy session
        count: Number of notes to create
        **kwargs: Override default factory attributes
        
    Returns:
        list[Note]: List of persisted note instances
    """
    notes = []
    for i in range(count):
        # Add index to content to make each note unique
        custom_kwargs = kwargs.copy()
        if "content" not in custom_kwargs:
            custom_kwargs["content"] = f"Test Note {i + 1}: {FuzzyText(length=30).fuzz()}"
        
        note = create_note_with_session(session, **custom_kwargs)
        notes.append(note)
    
    return notes
