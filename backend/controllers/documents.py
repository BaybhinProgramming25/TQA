from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Document, Message
from helpers.jwt import get_current_user
from helpers.getchunks import parse_pdf
from rag import init_db, delete_index
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

import io
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
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

    if db.query(Document).filter(Document.user_email == user_email, Document.filename == file.filename).first():
        raise HTTPException(status_code=409, detail="A document with this name already exists")

    user_dir = os.path.join(UPLOADS_DIR, user_email)
    os.makedirs(user_dir, exist_ok=True)

    filepath = os.path.join(user_dir, os.path.basename(file.filename))

    pdf_bytes = file.file.read()
    if not pdf_bytes.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    with open(filepath, "wb") as f:
        f.write(pdf_bytes)
    size = len(pdf_bytes)

    doc = Document(
        user_email=user_email,
        filename=file.filename,
        filepath=filepath,
        size=size,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    chunks = parse_pdf(pdf_bytes)
    init_db(chunks, f"{user_email}_{file.filename}", OPENAI_API_KEY)

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


@router.get("/api/documents/{doc_id}/export")
def export_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_email = current_user["username"]
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_email == user_email).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    with open(doc.filepath, "rb") as f:
        pdf_bytes = f.read()

    chunks = parse_pdf(pdf_bytes)

    # Collect semester and course data in document order
    semesters = {}
    for _, metadata in chunks:
        if metadata["type"] == "semester":
            semesters[metadata["semester"]] = {
                "term_gpa": metadata["term_gpa"],
                "cum_gpa": metadata["cum_gpa"],
                "courses": [],
            }
        elif metadata["type"] == "course":
            label = metadata["semester"]
            if label in semesters:
                semesters[label]["courses"].append(metadata)

    wb = Workbook()
    ws = wb.active
    ws.title = "Transcript"

    # Styles
    sem_font      = Font(bold=True, size=12)
    header_font   = Font(bold=True)
    gpa_font      = Font(bold=True, italic=True)
    header_fill   = PatternFill("solid", fgColor="D9E1F2")
    summary_fill  = PatternFill("solid", fgColor="E2EFDA")
    center        = Alignment(horizontal="center")

    COURSE_HEADERS = ["Course", "Description", "Grade", "Credits Attempted", "Credits Earned", "Points"]

    row = 1

    for sem_label, sem_data in semesters.items():
        # Semester header spanning all columns
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=len(COURSE_HEADERS))
        cell = ws.cell(row=row, column=1, value=sem_label)
        cell.font = sem_font
        cell.fill = PatternFill("solid", fgColor="BDD7EE")
        cell.alignment = center
        row += 1

        # Column headers
        for col, h in enumerate(COURSE_HEADERS, 1):
            c = ws.cell(row=row, column=col, value=h)
            c.font = header_font
            c.fill = header_fill
            c.alignment = center
        row += 1

        # Course rows
        for course in sem_data["courses"]:
            ws.cell(row=row, column=1, value=course["course"])
            ws.cell(row=row, column=2, value=course["description"])
            ws.cell(row=row, column=3, value=course["grade"]).alignment = center
            ws.cell(row=row, column=4, value=course["attempted"]).alignment = center
            ws.cell(row=row, column=5, value=course["earned"]).alignment = center
            ws.cell(row=row, column=6, value=course["points"]).alignment = center
            row += 1

        # GPA summary row for this semester
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
        gpa_cell = ws.cell(row=row, column=1, value=f"Term GPA: {sem_data['term_gpa']}   |   Cumulative GPA: {sem_data['cum_gpa']}")
        gpa_cell.font = gpa_font
        gpa_cell.alignment = center
        row += 2  # blank separator

    # Final summary table
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
    summary_title = ws.cell(row=row, column=1, value="GPA Summary")
    summary_title.font = Font(bold=True, size=12)
    summary_title.fill = PatternFill("solid", fgColor="70AD47")
    summary_title.alignment = center
    row += 1

    for col, h in enumerate(["Semester", "Term GPA", "Cumulative GPA"], 1):
        c = ws.cell(row=row, column=col, value=h)
        c.font = header_font
        c.fill = summary_fill
        c.alignment = center
    row += 1

    for sem_label, sem_data in semesters.items():
        ws.cell(row=row, column=1, value=sem_label)
        ws.cell(row=row, column=2, value=sem_data["term_gpa"]).alignment = center
        ws.cell(row=row, column=3, value=sem_data["cum_gpa"]).alignment = center
        row += 1

    # Auto-fit column widths
    col_widths = [30, 40, 10, 20, 15, 10]
    for i, width in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = width

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    export_filename = doc.filename.replace(".pdf", ".xlsx")
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=\"{export_filename}\""}
    )


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

    delete_index(f"{user_email}_{doc.filename}")
    db.query(Message).filter(Message.document_id == doc_id).delete()

    db.delete(doc)
    db.commit()

    return {"message": "Document deleted"}
