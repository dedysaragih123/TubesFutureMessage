# db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from app.models import User, Collaborator
from app.schemas import UserCreate, DocumentCreate
from fastapi import HTTPException
from app.base import Base
import logging
from app.models import Document
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "DATABASE_URL=postgresql://future-message-db_owner:6OFx8MJYcXsE@ep-icy-term-a122wq1s.ap-southeast-1.aws.neon.tech/future-message-db?sslmode=require"

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    logging.info("Database engine created successfully.")
except Exception as e:
    logging.error(f"Failed to create database engine: {str(e)}")
    raise

def get_db():
    """
    Provides a database session for FastAPI dependency injection.
    """
    db = None
    try:
        db = SessionLocal()
        logging.info("Database session created successfully.")
        yield db
    except Exception as e:
        logging.error(f"Database connection error: {str(e)}")
        raise
    finally:
        if db:
            db.close()
            logging.info("Database session closed.")

api_keys = {
    "e54d4431-5dab-474e-b71a-0db1fcb9e659": "7oDYjo3d9r58EJKYi5x4E8",
    "5f0c7127-3be9-4488-b801-c7b6415b45e9": "mUP7PpTHmFAkxcQLWKMY8t"
}

# Data dokumen disimpan di sini, di mana setiap dokumen memiliki ID, konten, dan daftar kolaborator.
documents = {}

def create_user(db: Session, user: UserCreate):
    """
    Menambahkan pengguna baru ke database.
    """
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        name=user.name,
        email=user.email,
        hashed_password=user.password  # Gunakan hashing untuk keamanan
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def check_api_key(api_key: str):
    return api_key in api_keys

def get_user_from_api_key(api_key: str, db: Session):
    if api_key not in api_keys:
        raise HTTPException(status_code=401, detail="Invalid API key")
    email = api_keys[api_key]
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def create_document(db: Session, document: DocumentCreate, owner_id: int):
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


def update_document(db: Session, document_id: int, title: str, content: str, delivery_date: str):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.title = title
    doc.content = content
    doc.delivery_date = delivery_date
    db.commit()
    db.refresh(doc)
    return doc

def add_collaborator(db: Session, document_id: int, user_id: int):
    from app.models import Collaborator  # Impor jika belum dilakukan
    collaborator = Collaborator(document_id=document_id, collaborator_id=user_id)
    db.add(collaborator)
    db.commit()
    return collaborator

def get_document(doc_id, user_id):
    if doc_id not in documents or user_id not in documents[doc_id]["collaborators"]:
        raise PermissionError("User not authorized to access this document")
    return documents[doc_id]

def send_document_via_email(db: Session, document_id: int):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    collaborators = (
        db.query(User.email)
        .join(Collaborator, User.id == Collaborator.collaborator_id)
        .filter(Collaborator.document_id == document_id)
        .all()
    )
    for collaborator in collaborators:
        print(f"Sending document '{doc.title}' to {collaborator.email}")


def get_user_by_email(db: Session, email: str):
    """
    Mengambil pengguna berdasarkan email dari database.
    """
    return db.query(User).filter(User.email == email).first()