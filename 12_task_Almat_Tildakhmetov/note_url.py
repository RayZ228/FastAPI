from fastapi import APIRouter, Query
from main import get_user, User, Depends, session, select, Note, NoteResponse, NoteUpdate, HTTPException
router = APIRouter()

@router.get("/notes", response_model=List[NoteResponse])
def get_notes(current_user: User = Depends(get_user), skip: int = 0, limit: int = 100, search: str | None = None):
    query = select(Note).where(Note.owner_id == current_user.id)
    if search:
        query = query.where(Note.title.ilike(f"%{search}%") | Note.content.ilike(f"%{search}%"))
    query = query.offset(skip).limit(limit)
    notes = session.exec(query).all()
    return [NoteResponse(id=note.id, title=note.title, content=note.content, owner_id=note.owner_id) for note in notes]

@router.post("/create_note", response_model=NoteResponse)
def create(note: Note, current_user: User = Depends(get_user)):
    note.owner_id = current_user.id
    session.add(note)
    session.commit()
    session.refresh(note)
    return note

@router.get("/note/{note_id}", response_model=NoteResponse)
def note(note_id: int, current_user: User = Depends(get_user)):
    note = session.exec(select(Note).where(Note.id == note_id, Note.owner_id == current_user.id))
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteResponse(id=note.id, title=note.title, content=note.content, owner_id = note.owner_id)

@router.put("/note/{note_id}", response_model=NoteResponse)
def update_note(note_id: int, note_update: NoteUpdate, current_user: User = Depends(get_user)):
    existing_note = session.exec(select(Note).where(Note.id == note_id, Note.owner_id == current_user.id)).first()
    if not existing_note:
        raise HTTPException(status_code=404, detail="Note not found")

    update_data = note_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(note, key, value)
    session.add(note)
    session.commit()
    session.refresh(note)
    return NoteResponse(id=note.id, title=note.title, content=note.content, owner_id=note.owner_id)

@router.delete("/note/{note_id}", response_model=NoteResponse)
def delete_note(note_id: int, current_user: User = Depends(get_user)):
    existing_note = session.exec(select(Note).where(Note.id == note_id, Note.owner_id == current_user.id)).first()
    if not existing_note:
        raise HTTPException(status_code=404, detail="Note not found")

    session.delete(existing_note)
    session.commit()
    return NoteResponse(id=existing_note.id, title=existing_note.title, content=existing_note.content, owner_id=existing_note.owner_id)