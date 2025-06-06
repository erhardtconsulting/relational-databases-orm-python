"""
Note Service

This module implements the business logic and data access layer for notes.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.note import Note
from app.schemas.note import NoteCreate, NoteUpdate


class NoteService:
    """
    Service class for Note business logic and data access.
    
    This class implements the Repository pattern and serves as the
    business logic layer between controllers and the database.
    
    The service handles:
    - CRUD operations
    - Business rule validation
    - Transaction management
    - Error handling
    """
    
    def __init__(self, db: Session):
        """
        Initialize the service with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create_note(self, note_data: NoteCreate) -> Note:
        """
        Create a new note.
        
        Args:
            note_data: Validated note creation data
            
        Returns:
            Note: The created note with generated ID and timestamps
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Create new note instance
            db_note = Note(content=note_data.content)
            
            # Add to session and commit
            self.db.add(db_note)
            self.db.commit()
            self.db.refresh(db_note)  # Refresh to get generated fields
            
            return db_note
            
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def get_note_by_id(self, note_id: UUID) -> Optional[Note]:
        """
        Retrieve a note by its ID.
        
        Args:
            note_id: UUID of the note to retrieve
            
        Returns:
            Note | None: The note if found, None otherwise
        """
        return self.db.query(Note).filter(Note.id == note_id).first()
    
    def get_all_notes(self, skip: int = 0, limit: int = 100) -> list[type[Note]]:
        """
        Retrieve all notes with pagination.
        
        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            
        Returns:
            List[Note]: List of notes
        """
        return self.db.query(Note).offset(skip).limit(limit).all()
    
    def update_note(self, note_id: UUID, note_data: NoteUpdate) -> Optional[Note]:
        """
        Update an existing note.
        
        Args:
            note_id: UUID of the note to update
            note_data: Validated note update data
            
        Returns:
            Note | None: Updated note if found, None otherwise
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Find existing note
            db_note = self.get_note_by_id(note_id)
            
            if not db_note:
                return None
            
            # Update fields
            db_note.update_content(note_data.content)
            
            # Commit changes
            self.db.commit()
            self.db.refresh(db_note)
            
            return db_note
            
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def delete_note(self, note_id: UUID) -> bool:
        """
        Delete a note by ID.
        
        Args:
            note_id: UUID of the note to delete
            
        Returns:
            bool: True if note was deleted, False if not found
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Find existing note
            db_note = self.get_note_by_id(note_id)
            
            if not db_note:
                return False
            
            # Delete the note
            self.db.delete(db_note)
            self.db.commit()
            
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e


def get_note_service(db: Session) -> NoteService:
    """
    Factory function for creating NoteService instances.
    
    This function provides dependency injection pattern,
    similar to @Autowired in Spring Boot.
    
    Args:
        db: Database session dependency
        
    Returns:
        NoteService: Configured service instance
    """
    return NoteService(db)
