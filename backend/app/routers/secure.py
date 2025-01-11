from fastapi import Body, APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.crud import (
    # create_document as create_document_crud,
    update_document_record,
    add_collaborator,
    get_document,
    create_document_record
)
from app.user_crud import create_user
from app.schemas import DocumentCreate, DocumentUpdate, CollaboratorAdd, UserCreate
from app.db import get_db
from app.auth import get_current_user
from app.models import Document, Collaborator, User
import logging
from pydantic import ValidationError
from sqlalchemy.sql import exists
import requests
import os

router = APIRouter()

IZIN_SAKIT_BASE_URL = os.getenv("IZIN_SAKIT_BASE_URL")
IZIN_SAKIT_AUTH_TOKEN = os.getenv("IZIN_SAKIT_AUTH_TOKEN")
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
            if not collaborator:
                logging.error(f"Collaborator {collaborator_email} not found")
                raise HTTPException(
                    status_code=400,
                    detail=f"Collaborator {collaborator_email} not found",
                )
        
        # Create the document
        new_document = create_document_record(
            db=db,
            document=request,
            owner_id=current_user.id,
        )

        # Add collaborators
        for collaborator_email in request.collaborators:
            collaborator = db.query(User).filter(User.email == collaborator_email).first()
            add_collaborator(
                db=db,
                document_id=new_document.id,
                collaborator_id=collaborator.id,
            )

        logging.info(f"Document created with ID: {new_document.id}")
        return {"message": f"Document '{request.title}' created successfully!"}

    except TypeError as e:
        logging.error(f"TypeError: {str(e)}")
        raise HTTPException(status_code=500, detail=f"TypeError: {str(e)}")
    
    except Exception as e:
        db.rollback()
        logging.error(f"Error creating document: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create document")

@router.put("/document/update")
def update_document(
    email: str = Query(..., description="Email of the user"),
    document: DocumentUpdate = Body(...),
    db: Session = Depends(get_db),
):
    try:
        logging.info(f"Updating document for email: {email}")
        logging.info(f"Document update payload: {document}")

        # Verifikasi pengguna
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logging.error(f"User not found for email: {email}")
            raise HTTPException(status_code=404, detail="User not found")

        # Validasi akses
        is_collaborator = (
            db.query(exists().where(
                (Collaborator.document_id == document.id) &
                (Collaborator.collaborator_id == user.id)
            )).scalar()
        )
        if not is_collaborator and user.id != document.owner_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Panggil fungsi untuk memperbarui dokumen
        updated_doc = update_document_record(
            db=db,
            document_id=document.id,
            title=document.title,
            content=document.content,
        )
        logging.info(f"Document updated successfully: {updated_doc.id}")
        return {"message": "Document updated successfully"}

    except Exception as e:
        db.rollback()
        logging.error(f"Error during document update: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update document: {str(e)}")

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
            raise HTTPException(
                status_code=404, 
                detail=f"User not found",
            )
        new_collaborator = add_collaborator(
            db=db,
            document_id=collaborator.document_id,
            collaborator_id=collaborator_user.id,
        )
        return {"message": "Collaborator added successfully", "collaborator": collaborator_user.email}
    
    except HTTPException as e:
        logging.error(f"Validation error: {str(e)}")
        raise e
    except Exception as e:
        db.rollback()
        logging.error(f"Error adding collaborator: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/document/list")
def list_documents(
    email: str = Query(..., description="Email of the current user"),
    db: Session = Depends(get_db),
):
    """
    Endpoint untuk mengambil daftar dokumen milik pengguna saat ini.
    """
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Ambil dokumen yang dimiliki atau di mana user adalah kolaborator
        owned_documents = db.query(Document).filter(Document.owner_id == user.id).all()
        collaborator_documents = (
            db.query(Document)
            .join(Collaborator, Document.id == Collaborator.document_id)
            .filter(Collaborator.collaborator_id == user.id)
            .all()
        )
        
        documents = owned_documents + collaborator_documents
        return {"documents": [{"id": doc.id, "title": doc.title} for doc in documents]}
    except Exception as e:
        logging.error(f"Error fetching documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch documents.")

@router.get("/document/view/{document_id}")
def view_document(
    document_id: int,
    email: str = Query(..., description="Email of the current user"),
    db: Session = Depends(get_db),
):
    # Validasi email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Cek apakah user memiliki akses ke dokumen
    document = (
        db.query(Document)
        .filter((Document.id == document_id) & ((Document.owner_id == user.id) |
                                                (db.query(Collaborator).filter(
                                                    Collaborator.document_id == document_id,
                                                    Collaborator.collaborator_id == user.id
                                                ).exists())))
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found or access denied")

    return {"id": document.id, "title": document.title, "content": document.content}

@router.post("/signup")
def signup(
    user: UserCreate, 
    db: Session = Depends(get_db),
):
    """
    Endpoint to sign up a new user.
    """
    logging.info(f"Signup attempt for email: {user.email}")
    try:
        # Validate if email is already registered
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            logging.error(f"Signup failed: Email {user.email} already registered")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Add the new user
        new_user = create_user(db, user=user)
        logging.info(f"User created successfully: {new_user.email}")
        return {"message": "User successfully created", "user": new_user}
    except Exception as e:
        logging.error(f"Error during signup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validate-collaborator/{email}")
def validate_collaborator(
    email: str, 
    db: Session = Depends(get_db),
):
    """
    Endpoint to validate if an email exists in the user database.
    """
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return {"valid": False, "message": "User not found"}
        return {"valid": True, "message": "User exists"}
    except Exception as e:
        logging.error(f"Error validating email: {str(e)}")
        raise HTTPException(status_code=500, detail="Error validating email")

@router.post("/document/send-pdf/{document_id}")
def send_pdf_to_email(
    document_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mengintegrasikan API izinSakit untuk mengirimkan PDF via email berdasarkan document_id.
    """
    try:
        # Ambil dokumen berdasarkan document_id
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Ambil kolaborator terkait dokumen
        collaborators = (
            db.query(User.email)
            .join(Collaborator, User.id == Collaborator.collaborator_id)
            .filter(Collaborator.document_id == document_id)
            .all()
        )
        if not collaborators:
            raise HTTPException(
                status_code=404, detail="No collaborators found for the document"
            )

        # Kirim PDF ke setiap kolaborator
        responses = []
        for collaborator_email in collaborators:
            payload = {"email": collaborator_email[0]}  # Ambil email dari query result
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {IZIN_SAKIT_AUTH_TOKEN}",
            }

            # Panggil API izinSakit
            response = requests.post(
                f"{IZIN_SAKIT_BASE_URL}/api/send-pdf/{document_id}",
                json=payload,
                headers=headers,
            )

            # Parsing respons API izinSakit
            if response.status_code == 202:
                responses.append(
                    {
                        "email": collaborator_email[0],
                        "status": "queued",
                        "jobId": response.json().get("jobId"),
                        "message": response.json().get("message"),
                    }
                )
                logging.info(f"PDF queued for email: {collaborator_email[0]}")
            elif response.status_code == 400:
                responses.append(
                    {
                        "email": collaborator_email[0],
                        "status": "error",
                        "message": response.json().get("message"),
                    }
                )
                logging.warning(
                    f"PDF not generated for email: {collaborator_email[0]}"
                )
            else:
                responses.append(
                    {
                        "email": collaborator_email[0],
                        "status": "failed",
                        "message": response.text,
                    }
                )
                logging.error(
                    f"Failed to send PDF to email: {collaborator_email[0]}"
                )

        return {"message": "PDF processing completed", "responses": responses}

    except Exception as e:
        logging.error(f"Error in send_pdf_to_email: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {str(e)}"
        )