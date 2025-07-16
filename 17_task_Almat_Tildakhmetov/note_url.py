import aioredis
from fastapi import APIRouter, Query, Depends
from main import get_user, User, session, select, Note, NoteResponse, NoteUpdate, HTTPException
from .redis_client import get_redis
from typing import List
import json

router = APIRouter()

@router.get("/notes", response_model=List[NoteResponse])
async def get_notes(current_user: User = Depends(get_user), skip: int = 0, limit: int = 100, search: str | None = None):
    redis = await get_redis()
    cache_key = f"notes:{current_user.id}:{skip}:{limit}:{search}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    query = select(Note).where(Note.owner_id == current_user.id)
    if search:
        query = query.where(Note.title.ilike(f"%{search}%") | Note.content.ilike(f"%{search}%"))
    query = query.offset(skip).limit(limit)
    notes = session.exec(query).all()
    result = [NoteResponse(id=note.id, title=note.title, content=note.content, owner_id=note.owner_id).dict() for note in notes]
    await redis.set(cache_key, json.dumps(result), ex=60)  # TTL 60 сек
    return result

@router.post("/create_note", response_model=NoteResponse)
async def create(note: Note, current_user: User = Depends(get_user)):
    note.owner_id = current_user.id
    session.add(note)
    session.commit()
    session.refresh(note)
    redis = await get_redis()
    await redis.delete_pattern(f"notes:{current_user.id}:*")
    return note

@router.get("/note/{note_id}", response_model=NoteResponse)
async def note(note_id: int, current_user: User = Depends(get_user)):
    note = session.exec(select(Note).where(Note.id == note_id, Note.owner_id == current_user.id))
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteResponse(id=note.id, title=note.title, content=note.content, owner_id = note.owner_id)

@router.put("/note/{note_id}", response_model=NoteResponse)
async def update_note(note_id: int, note_update: NoteUpdate, current_user: User = Depends(get_user)):
    existing_note = session.exec(select(Note).where(Note.id == note_id, Note.owner_id == current_user.id)).first()
    if not existing_note:
        raise HTTPException(status_code=404, detail="Note not found")
    update_data = note_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(existing_note, key, value)
    session.add(existing_note)
    session.commit()
    session.refresh(existing_note)
    redis = await get_redis()
    await redis.delete_pattern(f"notes:{current_user.id}:*")
    return NoteResponse(id=existing_note.id, title=existing_note.title, content=existing_note.content, owner_id=existing_note.owner_id)

@router.delete("/note/{note_id}", response_model=NoteResponse)
async def delete_note(note_id: int, current_user: User = Depends(get_user)):
    existing_note = session.exec(select(Note).where(Note.id == note_id, Note.owner_id == current_user.id)).first()
    if not existing_note:
        raise HTTPException(status_code=404, detail="Note not found")
    session.delete(existing_note)
    session.commit()
    redis = await get_redis()
    await redis.delete_pattern(f"notes:{current_user.id}:*")
    return NoteResponse(id=existing_note.id, title=existing_note.title, content=existing_note.content, owner_id=existing_note.owner_id)