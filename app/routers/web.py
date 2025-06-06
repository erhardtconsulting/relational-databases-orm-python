"""
Web Interface Router

This module provides HTML-based web interface endpoints for the Notes application.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.note import NoteCreate, NoteUpdate
from app.services.note_service import get_note_service

# Create web router
router = APIRouter(
    tags=["web"],
    responses={404: {"description": "Not found"}},
)

# Templates will be injected from main app
templates: Optional[Jinja2Templates] = None


def get_templates(request: Request) -> Jinja2Templates:
    """Get templates from app state."""
    return request.app.state.templates


@router.get("/", response_class=HTMLResponse)
async def web_index(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Home page showing all notes.
    
    This is the main landing page that displays all notes in a simple list
    with options to create, edit, or delete notes.
    """
    try:
        service = get_note_service(db)
        notes = service.get_all_notes()
        
        templates = get_templates(request)
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "notes": notes,
                "title": "All Notes"
            }
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


@router.get("/notes/create", response_class=HTMLResponse)
async def web_notes_create_form(request: Request):
    """
    Display the create note form.
    
    Shows an empty form for creating a new note.
    """
    templates = get_templates(request)
    return templates.TemplateResponse(
        "notes/create.html",
        {
            "request": request,
            "title": "Create New Note"
        }
    )


@router.post("/notes/create")
async def web_notes_create_submit(
    request: Request,
    content: str = Form(..., min_length=1, max_length=10000),
    db: Session = Depends(get_db)
):
    """
    Process the create note form submission.
    
    Creates a new note and redirects to the home page.
    Uses POST-redirect-GET pattern to prevent duplicate submissions.
    """
    try:
        # Validate and create note
        note_data = NoteCreate(content=content.strip())
        service = get_note_service(db)
        service.create_note(note_data)
        
        # Redirect to home page after successful creation
        return RedirectResponse(
            url="/",
            status_code=status.HTTP_303_SEE_OTHER
        )
        
    except ValueError as e:
        # Handle validation errors
        templates = get_templates(request)
        return templates.TemplateResponse(
            "notes/create.html",
            {
                "request": request,
                "title": "Create New Note",
                "error": str(e),
                "content": content
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except SQLAlchemyError as e:
        # Handle database errors
        templates = get_templates(request)
        return templates.TemplateResponse(
            "notes/create.html",
            {
                "request": request,
                "title": "Create New Note",
                "error": "Failed to create note. Please try again.",
                "content": content
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/notes/{note_id}/edit", response_class=HTMLResponse)
async def web_notes_edit_form(
    request: Request,
    note_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Display the edit note form.
    
    Shows a form pre-populated with the existing note content.
    """
    try:
        service = get_note_service(db)
        note = service.get_note_by_id(note_id)
        
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Note with ID {note_id} not found"
            )
        
        templates = get_templates(request)
        return templates.TemplateResponse(
            "notes/edit.html",
            {
                "request": request,
                "note": note,
                "title": "Edit Note"
            }
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


@router.post("/notes/{note_id}/edit")
async def web_notes_edit_submit(
    request: Request,
    note_id: UUID,
    content: str = Form(..., min_length=1, max_length=10000),
    db: Session = Depends(get_db)
):
    """
    Process the edit note form submission.
    
    Updates the existing note and redirects to the home page.
    Uses POST-redirect-GET pattern to prevent duplicate submissions.
    """
    try:
        # Validate and update note
        note_data = NoteUpdate(content=content.strip())
        service = get_note_service(db)
        note = service.update_note(note_id, note_data)
        
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Note with ID {note_id} not found"
            )
        
        # Redirect to home page after successful update
        return RedirectResponse(
            url="/",
            status_code=status.HTTP_303_SEE_OTHER
        )
        
    except ValueError as e:
        # Handle validation errors - show form again with error
        service = get_note_service(db)
        note = service.get_note_by_id(note_id)
        
        templates = get_templates(request)
        return templates.TemplateResponse(
            "notes/edit.html",
            {
                "request": request,
                "note": note,
                "title": "Edit Note",
                "error": str(e),
                "content": content
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except SQLAlchemyError as e:
        # Handle database errors
        service = get_note_service(db)
        note = service.get_note_by_id(note_id)
        
        templates = get_templates(request)
        return templates.TemplateResponse(
            "notes/edit.html",
            {
                "request": request,
                "note": note,
                "title": "Edit Note",
                "error": "Failed to update note. Please try again.",
                "content": content
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/notes/{note_id}/delete")
async def web_notes_delete(
    note_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a note.
    
    Deletes the specified note and redirects to the home page.
    This endpoint is called via form submission or JavaScript.
    """
    try:
        service = get_note_service(db)
        deleted = service.delete_note(note_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Note with ID {note_id} not found"
            )
        
        # Redirect to home page after successful deletion
        return RedirectResponse(
            url="/",
            status_code=status.HTTP_303_SEE_OTHER
        )
        
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
