from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Document

router = APIRouter()

@router.get("/public/documents/{document_id}")
def get_public_document(document_id: int, db: Session = Depends(get_db)):
    """
    Endpoint to fetch a public document.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": document.id,
        "title": document.title,
        "content": document.content,
        "delivery_date": document.delivery_date
    }
