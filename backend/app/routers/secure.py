from fastapi import Body, APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.crud import (
    update_document_record,
    add_collaborator,
    get_document,
    create_document_record
)
from app.user_crud import create_user
from app.schemas import DocumentCreate, DocumentUpdate, CollaboratorAdd, UserCreate, EmailRequest, UserLogin, SickLeaveForm
from app.db import get_db
from app.auth import get_current_user, pwd_context
from app.models import Document, Collaborator, User
import logging
from pydantic import ValidationError
from sqlalchemy.sql import exists
import os
from app.utils.email_utils import send_email,scheduler, send_scheduled_emails
from urllib.parse import unquote
from apscheduler.triggers.date import DateTrigger
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from typing import Optional

router = APIRouter()

IZIN_SAKIT_BASE_URL = os.getenv("IZIN_SAKIT_BASE_URL", "https://api.izinsakit.site")
IZIN_SAKIT_AUTH_TOKEN = os.getenv("IZIN_SAKIT_AUTH_TOKEN")


# ====== DOCUMENT MANAGEMENT ======

@router.post("/document/create")
def create_document(
    request: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint to create a new document and assign collaborators.
    """
    try:
        logging.info(f"Creating document for user: {current_user.email}")
        
        # Validate collaborators
        for collaborator_email in request.collaborators:
            collaborator = db.query(User).filter(User.email == collaborator_email).first()
            logging.info(f"Validating collaborator: {collaborator_email}")
            if not collaborator:
                logging.error(f"Collaborator {collaborator_email} not found")
                raise HTTPException(
                    status_code=400,
                    detail=f"Collaborator {collaborator_email} not found",
                )
        
        # Create the document
        logging.info("Creating document record...")
        new_document = create_document_record(
            db=db,
            document=request,
            owner_id=current_user.id,
        )

        # Schedule email job with correct delivery_date
        if new_document.delivery_date:
            logging.info(f"Scheduling email for delivery at {new_document.delivery_date}")
            scheduler.add_job(
                send_scheduled_emails,  # Fungsi yang akan dijalankan
                trigger=DateTrigger(run_date=new_document.delivery_date),  # Trigger sesuai delivery_date
                args=[new_document.id],  # Argumen untuk fungsi
                id=f"send_email_{new_document.id}",  # ID unik untuk job
                replace_existing=True,  # Ganti job jika sudah ada
            )
        else:
            logging.warning(f"No delivery_date provided for document {new_document.id}. Skipping scheduling.")

        # Add collaborators
        for collaborator_email in request.collaborators:
            collaborator = db.query(User).filter(User.email == collaborator_email).first()
            add_collaborator(
                db=db,
                document_id=new_document.id,
                collaborator_id=collaborator.id,
            )

        logging.info(f"Document created with ID: {new_document.id}")
        return {
            "message": f"Document '{request.title}' created successfully!",
            "document_id": new_document.id  # Tambahkan document_id ke respons
        }

    except Exception as e:
        db.rollback()
        logging.error(f"Error creating document: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create document")
    finally:
        db.close()

@router.put("/document/update")
def update_document(
    email: str = Query(..., description="Email of the user"),
    document: DocumentUpdate = Body(...),
    db: Session = Depends(get_db),
):
    """
    Endpoint to update a document.
    """
    try:
        logging.info(f"Updating document for email: {email}")

        # Validate user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Validate access
        is_collaborator = (
            db.query(exists().where(
                (Collaborator.document_id == document.id) &
                (Collaborator.collaborator_id == user.id)
            )).scalar()
        )
        if not is_collaborator and user.id != document.owner_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Update document
        updated_doc = update_document_record(
            db=db,
            document_id=document.id,
            title=document.title,
            content=document.content,
        )
        return {"message": f"Document '{updated_doc.title}' updated successfully!"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update document: {str(e)}")

@router.get("/document/view/{document_id}")
def view_document(
    document_id: int,
    email: str = Query(..., description="Email of the current user"),
    db: Session = Depends(get_db),
):
    """
    Endpoint to view a document's details.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check access (as owner or collaborator)
    document = (
        db.query(Document)
        .filter(
            (Document.id == document_id) &
            (
                (Document.owner_id == user.id) | 
                db.query(Collaborator)
                .filter(
                    Collaborator.document_id == document_id,
                    Collaborator.collaborator_id == user.id
                ).exists()
            )
        )
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found or access denied")

    return {"id": document.id, "title": document.title, "content": document.content}

@router.post("/document/add-collaborator")
def add_collaborator_to_document(
    collaborator: CollaboratorAdd, 
    db: Session = Depends(get_db),
):
    """
    Endpoint to add a collaborator to a document.
    """
    try:
        collaborator_user = db.query(User).filter(User.email == collaborator.collaborator_email).first()
        if not collaborator_user:
            raise HTTPException(status_code=404, detail="User not found")
        add_collaborator(
            db=db,
            document_id=collaborator.document_id,
            collaborator_id=collaborator_user.id,
        )
        return {"message": "Collaborator added successfully", "collaborator": collaborator_user.email}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add collaborator: {str(e)}")

@router.get("/validate-collaborator/{email}")
def validate_collaborator(
    email: str, 
    db: Session = Depends(get_db),
):
    """
    Endpoint to validate if an email exists in the user database.
    """
    email = unquote(email)  # Decode email jika diperlukan
    logging.info(f"Validating collaborator email: {email}")
    try:
        # Query database
        user = db.query(User).filter(User.email == email).first()
        logging.info(f"Query result for {email}: {user}")

        if not user:
            return {"valid": False, "message": "User not found"}
        return {"valid": True, "message": "User exists"}
    except Exception as e:
        logging.error(f"Error validating email: {str(e)}")
        raise HTTPException(status_code=500, detail="Error validating email")

@router.get("/document/list")
def list_documents(
    email: str = Query(..., description="Email of the current user"),
    db: Session = Depends(get_db),
):
    """
    Endpoint to list documents owned or collaborated on by a user.
    """
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        owned_documents = db.query(Document).filter(Document.owner_id == user.id).all()
        collaborator_documents = (
            db.query(Document)
            .join(Collaborator, Document.id == Collaborator.document_id)
            .filter(Collaborator.collaborator_id == user.id)
            .all()
        )
        
        documents = {doc.id: {"id": doc.id, "title": doc.title} for doc in owned_documents + collaborator_documents}
        return {"documents": list(documents.values())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch documents: {str(e)}")

@router.post("/document/send-email/{document_id}")
def send_email_endpoint(
    document_id: int,
    email_request: EmailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint untuk mengirim email dengan menggunakan layanan eksternal.
    """
    try:
        # Validasi dokumen dan akses pengguna
        document = db.query(Document).filter(
            Document.id == document_id, Document.owner_id == current_user.id
        ).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found or access denied")

        to_email = email_request.to_email
        subject = email_request.subject or f"Document: {document.title}"
        body = email_request.body or f"<h1>{document.title}</h1><p>{document.content}</p>"

        # Kirim email
        result = send_email(db, document_id, to_email, subject, body)
        return {
            "message": "Email sent successfully",
            "result": result,
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email")

@router.on_event("startup")
def start_secure_scheduler():
    if not scheduler.running:
        scheduler.start()
        logging.info("Scheduler started in secure.py")