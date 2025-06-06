"""
Note Model

The Note model demonstrates:
- Primary key with UUID
- Column definitions with constraints
- Automatic timestamps
"""

import uuid

from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Note(Base):
    """
    Note entity representing a simple text note in the database.
    
    Attributes:
        id: UUID primary key, automatically generated
        content: Text content of the note (required)
        created_at: Timestamp when note was created
        updated_at: Timestamp when note was last modified
    """
    
    __tablename__ = "notes"
    
    # Primary key with UUID
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        comment="Unique identifier for the note"
    )
    
    # Content field
    content = Column(
        String,
        nullable=False,
        comment="The text content of the note"
    )
    
    # Audit timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the note was created"
    )
    
    # Update timestamp
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when the note was last updated"
    )
    
    def update_content(self, new_content: str) -> None:
        """
        Update the note content.
        
        This method demonstrates business logic within the model,
        similar to entity methods in domain-driven design.
        
        Args:
            new_content: New content for the note
        """
        if not new_content or not new_content.strip():
            raise ValueError("Note content cannot be empty")
        
        self.content = new_content.strip()
        # updated_at will be automatically set by SQLAlchemy onupdate
