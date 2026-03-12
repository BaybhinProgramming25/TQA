import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import Document
from helpers.jwt import get_current_user

UPLOADS_DIR = "/uploads"
router = APIRouter()


@router.post("/api/documents")
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    user_email = current_user["username"]
    user_dir = os.path.join(UPLOADS_DIR, user_email)
    os.makedirs(user_dir, exist_ok=True)

    filepath = os.path.join(user_dir, file.filename)

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    size = os.path.getsize(filepath)

    doc = Document(
        user_email=user_email,
        filename=file.filename,
        filepath=filepath,
        size=size,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "id": doc.id,
        "filename": doc.filename,
        "size": doc.size,
        "uploaded_at": doc.uploaded_at.isoformat(),
    }


@router.get("/api/documents")
def list_documents(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_email = current_user["username"]
    docs = db.query(Document).filter(Document.user_email == user_email).all()
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "size": doc.size,
            "uploaded_at": doc.uploaded_at.isoformat(),
        }
        for doc in docs
    ]


@router.delete("/api/documents/{doc_id}")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_email = current_user["username"]
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_email == user_email).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if os.path.exists(doc.filepath):
        os.remove(doc.filepath)

    db.delete(doc)
    db.commit()

    return {"message": "Document deleted"}
