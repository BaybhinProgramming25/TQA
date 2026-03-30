from fastapi import APIRouter, Depends, HTTPException, Form, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Document, Message
from helpers.jwt import get_current_user
from helpers.limiter import limiter
from rag import query

import os
import logging

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
router = APIRouter()
logger = logging.getLogger(__name__)

EXPORT_KEYWORDS = {"export", "excel", "spreadsheet", "xlsx", "download"}
def _is_export_intent(message: str) -> bool:
    words = set(message.lower().split())
    return bool(words & EXPORT_KEYWORDS)


@router.get("/api/messages/{document_id}")
def get_messages(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_email == current_user["username"]
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    messages = (
        db.query(Message)
        .filter(Message.document_id == document_id, Message.user_email == current_user["username"])
        .order_by(Message.created_at)
        .all()
    )
    return [
        {"id": m.id, "sender": m.sender, "text": m.text, "created_at": m.created_at.isoformat()}
        for m in messages
    ]


@router.post("/parse")
@limiter.limit("10/minute")
def parse(
    request: Request,
    message: str = Form(...),
    document_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_email == current_user["username"]
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if _is_export_intent(message):
        reply = "Sure! Exporting your transcript to Excel now..."
        db.add_all([
            Message(user_email=current_user["username"], document_id=doc.id, sender="user", text=message),
            Message(user_email=current_user["username"], document_id=doc.id, sender="ai", text=reply),
        ])
        db.commit()
        return JSONResponse(content={"message": reply, "action": "export"})

    try:
        answer = query(message, f"{doc.user_email}_{doc.filename}", OPENAI_API_KEY)
    except Exception as e:
        logger.error("OpenAI query error for doc %s, user %s: %s", document_id, current_user["username"], e)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

    db.add_all([
        Message(user_email=current_user["username"], document_id=doc.id, sender="user", text=message),
        Message(user_email=current_user["username"], document_id=doc.id, sender="ai", text=answer),
    ])
    db.commit()

    return JSONResponse(content={"message": answer})
