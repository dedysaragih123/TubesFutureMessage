from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from app.routers import secure, public
from app import auth
from app.auth import get_user
from app.base import Base, engine
from app.db import get_db, SessionLocal  # Pastikan SessionLocal diimpor
from app.utils.email_utils import send_email
from sqlalchemy.orm import Session
from app.models import Document, Collaborator, User
from datetime import datetime, timedelta  # Pastikan datetime diimpor
import logging
from apscheduler.schedulers.background import BackgroundScheduler

# Inisialisasi aplikasi
app = FastAPI()
scheduler = BackgroundScheduler()

# Middleware CORS (opsional jika frontend di-host di domain berbeda)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "https://future-message-caexg0bxeha9d2et.southeastasia-01.azurewebsites.net/",
                   "https://tubes-future-message.vercel.app/",],  # Ganti dengan domain deploy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(secure.router, prefix="/api/v1", dependencies=[Depends(get_user)], tags=["Secure"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])

# Logging dasar
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.info("Application started.")

# Middleware untuk logging request
@app.middleware("http")
async def add_logging(request: Request, call_next):
    logging.info(f"Incoming request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logging.error(f"Unhandled exception: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Root endpoint
@app.get("/")
async def read_root():
    logging.info("Root endpoint accessed.")
    return {"message": "Welcome to the Future Message API!"}

# Startup event
@app.on_event("startup")
def on_startup():
    if not scheduler.running:
        if not scheduler.get_jobs():
            scheduler.add_job(send_scheduled_emails, 'interval', minutes=1)
        scheduler.start()

# Shutdown event (opsional)
@app.on_event("shutdown")
async def on_shutdown():
    if scheduler.running:
        scheduler.shutdown()

def send_scheduled_emails():
    """
    Mengirimkan email terjadwal berdasarkan dokumen yang memenuhi syarat (delivery_date <= datetime.now dan is_sent == False).
    """
    db = SessionLocal()  # Membuat sesi database secara manual
    try:
        logging.info("Starting email scheduling job...")

        # Ambil dokumen yang belum dikirim dan sudah mencapai delivery_date
        documents = db.query(Document).filter(
            Document.delivery_date <= datetime.now(),
            Document.is_sent == False
        ).all()
        logging.info(f"Found {len(documents)} documents to process.")

        for doc in documents:
            try:
                logging.info(f"Processing document: {doc.title}")

                # Ambil kolaborator untuk dokumen
                collaborators = (
                    db.query(User.email)
                    .join(Collaborator, User.id == Collaborator.collaborator_id)
                    .filter(Collaborator.document_id == doc.id)
                    .all()
                )

                if not collaborators:
                    logging.warning(f"No collaborators found for document ID {doc.id}. Skipping.")
                    continue

                # Kirim email ke setiap kolaborator
                for collaborator in collaborators:
                    try:
                        send_email(
                            to_email=collaborator.email,
                            subject=f"Document: {doc.title}",
                            body=doc.content
                        )
                        logging.info(f"Email sent to {collaborator.email}")
                    except Exception as e:
                        logging.error(f"Failed to send email to {collaborator.email}: {str(e)}")

                # Tandai dokumen sebagai sudah dikirim
                doc.is_sent = True
                doc.sent_at = datetime.now()  # Tambahkan timestamp pengiriman (opsional)
                db.commit()
                logging.info(f"Document '{doc.title}' marked as sent.")
            except Exception as doc_error:
                logging.error(f"Error processing document ID {doc.id}: {str(doc_error)}")
                db.rollback()  # Rollback jika ada error pada dokumen tertentu

        logging.info("Email scheduling job completed successfully.")

    except Exception as e:
        logging.error(f"Error in send_scheduled_emails: {str(e)}")
    finally:
        try:
            db.close()  # Pastikan sesi database selalu ditutup
            logging.info("Database session closed.")
        except Exception as close_error:
            logging.error(f"Error closing database session: {str(close_error)}")

@app.on_event("startup")
def start_scheduler():
    if not scheduler.running:  # Periksa apakah scheduler sudah berjalan
        if not scheduler.get_jobs():
            scheduler.add_job(send_scheduled_emails, 'interval', minutes=1)
        scheduler.start()
