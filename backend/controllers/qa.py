from fastapi import APIRouter, Depends, HTTPException, Form, Request
from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.database import get_db
from database.models import Document, Message
from helpers.jwt import get_current_user
from helpers.limiter import limiter
from rag import query_stream
from langchain_core.messages import HumanMessage, AIMessage

import os
import json
import logging

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
router = APIRouter()
logger = logging.getLogger(__name__)


EXPORT_KEYWORDS = {"export", "excel", "spreadsheet", "xlsx", "download"}
def _is_export_intent(message: str) -> bool:
    
    words = set(message.lower().split())
    return bool(words & EXPORT_KEYWORDS)


@router.get("/api/messages/{document_id}")
def get_messages(document_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):

    doc = None 
    try:
        doc = db.query(Document).filter(
            Document.id == document_id,
            Document.user_email == current_user["username"]
        ).first()
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error")
    

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    

    messages = None 
    try: 
        messages = (
            db.query(Message)
            .filter(Message.document_id == document_id, Message.user_email == current_user["username"])
            .order_by(Message.created_at)
            .all()
        )
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error")
    

    return [
        {"id": m.id, "sender": m.sender, "text": m.text, "created_at": m.created_at.isoformat()}
        for m in messages
    ]

@router.post("/parse")
@limiter.limit("10/minute")
async def parse(request: Request, message: str = Form(...), document_id: int = Form(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):

    if not message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    doc = None
    try:
        doc = db.query(Document).filter(
            Document.id == document_id,
            Document.user_email == current_user["username"]
        ).first()
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database querying error")

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if _is_export_intent(message):
        reply = "Sure! Exporting your transcript to Excel now..."
        try:
            db.add_all([
                Message(user_email=current_user["username"], document_id=doc.id, sender="user", text=message),
                Message(user_email=current_user["username"], document_id=doc.id, sender="ai", text=reply),
            ])
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(status_code=500, detail="Database Error")

        async def export_stream():
            yield f"data: {json.dumps({'action': 'export', 'message': reply})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(export_stream(), media_type="text/event-stream")

    history = []
    try:
        recent = (
            db.query(Message)
            .filter(Message.document_id == doc.id, Message.user_email == current_user["username"])
            .order_by(Message.created_at.desc())
            .limit(10)
            .all()
        )
        for m in reversed(recent):
            if m.sender == "user":
                history.append(HumanMessage(content=m.text))
            else:
                history.append(AIMessage(content=m.text))
    except SQLAlchemyError:
        history = []

    async def rag_stream():
        full_answer = []
        try:
            async for chunk in query_stream(message, f"{doc.user_email}_{doc.filename}", OPENAI_API_KEY, ANTHROPIC_API_KEY, history):
                full_answer.append(chunk)
                yield f"data: {json.dumps({'token': chunk})}\n\n"
        except Exception as e:
            logger.error("Stream error for doc %s, user %s: %s", document_id, current_user["username"], e)
            yield f"data: {json.dumps({'error': True})}\n\n"
            return

        answer = "".join(full_answer)
        try:
            db.add_all([
                Message(user_email=current_user["username"], document_id=doc.id, sender="user", text=message),
                Message(user_email=current_user["username"], document_id=doc.id, sender="ai", text=answer),
            ])
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            logger.error("DB error saving streamed message for doc %s", document_id)

        yield "data: [DONE]\n\n"

    return StreamingResponse(rag_stream(), media_type="text/event-stream")
