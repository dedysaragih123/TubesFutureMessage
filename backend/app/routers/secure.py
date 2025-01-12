from fastapi import Body, APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.crud import (
    update_document_record,
    add_collaborator,
    get_document,
    create_document_record
)
from app.user_crud import create_user
from app.schemas import DocumentCreate, DocumentUpdate, CollaboratorAdd, UserCreate, EmailRequest, UserLogin
from app.db import get_db
from app.auth import get_current_user, pwd_context
from app.models import Document, Collaborator, User
import logging
from pydantic import ValidationError
from sqlalchemy.sql import exists
import os
from app.utils.email_utils import send_email
from app.utils.izin_sakit import create_sick_leave_request, submit_sick_leave_form, generate_sick_leave_pdf
from urllib.parse import unquote

router = APIRouter()

IZIN_SAKIT_BASE_URL = os.getenv("IZIN_SAKIT_BASE_URL", "https://izinsakit.site")
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


# ====== EMAIL MANAGEMENT ======

@router.post("/send-email")
def send_email_endpoint(
    email_request: EmailRequest,
    user_login: UserLogin = Body(...),
    email: str = Query(...),
    db: Session = Depends(get_db),
):
    """
    Endpoint to send email using email and password directly.
    """
    # Authenticate user
    db_user = db.query(User).filter(User.email == user_login.email).first()
    if not db_user or not pwd_context.verify(user_login.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Send email
    try:
        send_email(
            db=db,
            to_email=email_request.to_email,
            subject=email_request.subject,
            body=email_request.body,
        )
        return {"message": "Emails sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send emails: {str(e)}")

# ====== INTEGRATION: Izin Sakit ======

@router.post("/integrate/sick-leave")
def create_sick_leave(
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint untuk membuat permohonan izin sakit.
    """
    username = data.get("username")
    reason = data.get("reason")

    if not username or not reason:
        raise HTTPException(status_code=400, detail="Username and reason are required")
    if len(reason) < 5:
        raise HTTPException(status_code=400, detail="Reason must be at least 5 characters")

    try:
        response = create_sick_leave_request(username=username, reason=reason)
        logging.info(f"Response from izin sakit: {response}")
        return response
    except HTTPException as e:
        logging.error(f"Error from izin sakit service: {e.detail}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)

@router.post("/integrate/sick-leave-form")
def create_sick_leave_form(
    form_data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint untuk mengirimkan formulir izin sakit.
    """
    username = current_user.email.split('@')[0]  # Generate username dari email
    form_data["username"] = username

    try:
        response = submit_sick_leave_form(form_data)
        return response
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

@router.post("/integrate/sick-leave-save-answers")
def save_answers_to_sick_leave_form(
    answers: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint untuk menyimpan jawaban formulir izin sakit.
    """
    username = current_user.email.split('@')[0]  # Tambahkan username dari email
    answers["username"] = username

    try:
        response = submit_sick_leave_form(answers)
        return {"message": "Sick leave answers saved successfully", "data": response}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

@router.get("/integrate/sick-leave-pdf/{id}")
def generate_pdf_for_sick_leave(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint untuk menghasilkan PDF untuk izin sakit.
    """
    try:
        response = generate_sick_leave_pdf(sick_leave_id=id)
        return response
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
