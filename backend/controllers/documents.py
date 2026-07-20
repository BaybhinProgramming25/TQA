from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database.database import get_db
from database.models import Document, Message

from helpers.jwt import get_current_user
from helpers.limiter import limiter
from helpers.ingest import ingest_transcript
from helpers.store import transcripts

import os
import logging

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
UPLOADS_DIR = os.getenv("UPLOADS_DIR", "/uploads")
router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/api/documents")
@limiter.limit("5/minute")
def upload_document(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    

    user_email = current_user["username"]
    try:
        if db.query(Document).filter(Document.user_email == user_email, Document.filename == file.filename).first():
            raise HTTPException(status_code=409, detail="A document with this name already exists")
    except SQLAlchemyError as e:
        logger.error(f"Could not query document with associated user: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    
    
    filepath = None 
    try: 
        user_dir = os.path.join(UPLOADS_DIR, user_email)
        os.makedirs(user_dir, exist_ok=True)
        filepath = os.path.join(user_dir, os.path.basename(file.filename))
    except OSError as e:
        logger.error(f"Path Not found {e}")
        raise HTTPException(status_code=500, detail="Something went wrong")
    

    pdf_bytes = file.file.read()
    if not pdf_bytes.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")


    with open(filepath, "wb") as f:
        f.write(pdf_bytes)    
    size = len(pdf_bytes)


    transcript_info = None
    try:
        transcript_info = ingest_transcript(filepath)
    except Exception as e:
        logger.error("Failed to ingest transcript for user %s, file %s: %s", user_email, file.filename, e)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

    doc = None
    try:
        doc = Document(
            user_email=user_email,
            filename=file.filename,
            filepath=filepath,
            size=size,
            transcript_text = transcript_info
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error making change to database: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    
    transcripts[user_email] = transcript_info

    return {
        "id": doc.id,
        "filename": doc.filename,
        "size": doc.size,
        "uploaded_at": doc.uploaded_at.isoformat(),
    }


@router.get("/api/documents")
def list_documents(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):

    user_email = current_user["username"]

    docs = None 
    try:
        docs = db.query(Document).filter(Document.user_email == user_email).all()
    except SQLAlchemyError as e:
        logger.error(f"Error querying user: {e}")
        raise HTTPException(status_code=500, detail="Database Error")
    
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "size": doc.size,
            "uploaded_at": doc.uploaded_at.isoformat(),
        }
        for doc in docs
    ]


@router.get("/api/documents/{doc_id}/file")
@limiter.limit("20/minute")
def get_document_file(request: Request, doc_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):

    user_email = current_user["username"]
    try:
        doc = db.query(Document).filter(Document.id == doc_id, Document.user_email == user_email).first()
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error")

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not os.path.exists(doc.filepath):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(doc.filepath, media_type="application/pdf")


@router.delete("/api/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):


    user_email = current_user["username"]

    doc = None
    try:
        doc = db.query(Document).filter(Document.id == doc_id, Document.user_email == user_email).first()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user: {e}")
        raise HTTPException(status_code=500, detail="Database Error")

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if os.path.exists(doc.filepath):
        os.remove(doc.filepath)

    transcripts.pop(user_email, None)

    try:
        db.query(Message).filter(Message.document_id == doc_id).delete()
        db.delete(doc)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="Database Error")

    return {"message": "Document deleted"}
