"""
Note Pydantic Schemas

This module contains Pydantic models for Note data validation and serialization.
"""

from pydantic import BaseModel, Field, field_validator


class NoteBase(BaseModel):
    """
    Base schema for Note with common fields.
    """
    
    content: str = Field(
        min_length=1,
        max_length=5000,
        description="The text content of the note",
        examples=["This is my first note!", "Shopping list: milk, bread, eggs"]
    )

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        """
        Validate and clean note content.
        
        Args:
            v: The content string to validate
            
        Returns:
            str: Cleaned and validated content
            
        Raises:
            ValueError: If content is invalid
        """
        if not v or not v.strip():
            raise ValueError('Note content cannot be empty or whitespace only')
        
        # Clean the content
        cleaned = v.strip()
        
        if len(cleaned) > 5000:
            raise ValueError('Note content cannot exceed 5000 characters')
            
        return cleaned

class NoteCreate(NoteBase):
    pass


class NoteUpdate(NoteBase):
    pass
