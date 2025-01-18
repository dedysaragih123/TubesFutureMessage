from sqlalchemy.orm import Session
from app.models import User, Document, Collaborator
from app.schemas import UserCreate, DocumentCreate, DocumentUpdate
from fastapi import HTTPException, Depends, Query, Body
from passlib.context import CryptContext
from uuid import uuid4
from app.auth import get_current_user
from app.db import get_db
import logging
from sqlalchemy.sql import exists
from datetime import datetime

# User CRUD
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# Document CRUD
def create_document_record(db: Session, document: DocumentCreate, owner_id: int):
    new_document = Document(
        title=document.title,
        content=document.content,
        delivery_date=document.delivery_date,
        owner_id=owner_id,
    )
    db.add(new_document)
    db.commit()
    db.refresh(new_document)
    return new_document

def update_document_record(db: Session, document_id: int, title: str, content: str):
    """
    Fungsi untuk memperbarui judul dan konten dokumen.
    
    Args:
        db (Session): Objek sesi database.
        document_id (int): ID dokumen yang akan diperbarui.
        title (str): Judul baru dokumen.
        content (str): Konten baru dokumen.
    
    Returns:
        Document: Objek dokumen yang telah diperbarui.
    
    Raises:
        HTTPException: Jika dokumen tidak ditemukan.
    """
    # Cari dokumen berdasarkan ID
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Update hanya jika nilai diberikan
    if title is not None:
        doc.title = title
    if content is not None:
        doc.content = content

    # Simpan perubahan ke database
    db.commit()
    db.refresh(doc)

    return doc


def add_collaborator(db: Session, document_id: str, collaborator_id: int):
    # Validasi jika dokumen atau kolaborator tidak ada
    document = db.query(Document).filter(Document.id == document_id).first()
    user = db.query(User).filter(User.id == collaborator_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if not user:
        raise HTTPException(status_code=404, detail="Collaborator not found")

    # Tambahkan kolaborator baru
    new_collaborator = Collaborator(
        document_id=document_id,
        collaborator_id=collaborator_id
    )
    db.add(new_collaborator)
    db.commit()
    return new_collaborator

def get_document(db: Session, document_id: str):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

def get_document_by_id(db: Session, document_id: int):
    """
    Mengambil dokumen berdasarkan ID.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

def log_document_sent(db: Session, document_id: int, recipient_email: str):
    """
    Menandai dokumen sebagai terkirim dan mencatat log pengiriman.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document.is_sent = True
    document.sent_at = datetime.now()  # Tanggal dan waktu pengiriman
    db.commit()
    db.refresh(document)
    logging.info(f"Document '{document.title}' sent to {recipient_email}.")
    return document