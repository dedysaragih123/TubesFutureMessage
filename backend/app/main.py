from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from app.routers import secure, public
from app import auth
from app.auth import get_user
from app.base import Base, engine
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from app.db import get_db, SessionLocal
from app.utils.email_utils import send_email
from sqlalchemy.orm import Session
from app.models import Document, Collaborator, User
from datetime import datetime, timedelta

# Inisialisasi aplikasi
app = FastAPI()
scheduler = BackgroundScheduler()

# Middleware CORS (opsional jika frontend di-host di domain berbeda)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "https://my-app.vercel.app",],  # Ganti dengan domain deploy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(secure.router, prefix="/api/v1", dependencies=[Depends(get_user)], tags=["Secure"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])

# Logging dasar
logging.basicConfig(level=logging.INFO)

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
async def on_startup():
    if not scheduler.running:
        scheduler.add_job(send_scheduled_emails, 'interval', minutes=1)
        scheduler.start()

# Shutdown event (opsional)
@app.on_event("shutdown")
async def on_shutdown():
    if scheduler.running:
        scheduler.shutdown()

def send_scheduled_emails():
    # Membuat sesi database secara manual
    db = SessionLocal()
    try:
        logging.info("Starting email scheduling job...")

        # Ambil dokumen yang belum dikirim dan sudah mencapai delivery_date
        documents = db.query(Document).filter(
            Document.delivery_date <= datetime.now(),
            Document.is_sent == False
        ).all()
        logging.info(f"Found {len(documents)} documents to process.")

        for doc in documents:
            logging.info(f"Processing document: {doc.title}")

            # Ambil kolaborator untuk dokumen
            collaborators = (
                db.query(User.email)
                .join(Collaborator, User.id == Collaborator.collaborator_id)
                .filter(Collaborator.document_id == doc.id)
                .all()
            )

            # Kirim email ke setiap kolaborator
            for collaborator in collaborators:
                send_email(
                    to_email=collaborator.email,
                    subject=f"Document: {doc.title}",
                    body=doc.content
                )
                logging.info(f"Email sent to {collaborator.email}")

            # Tandai dokumen sebagai sudah dikirim
            doc.is_sent = True
            doc.sent_at = datetime.now()  # Tambahkan timestamp pengiriman (opsional)
            db.commit()
            logging.info(f"Document '{doc.title}' marked as sent.")

        logging.info("Email scheduling job completed successfully.")

    except Exception as e:
        logging.error(f"Error in send_scheduled_emails: {str(e)}")
    finally:
        db.close()  # Pastikan sesi database selalu ditutup
        logging.info("Database session closed.")

@app.on_event("startup")
def start_scheduler():
    if not scheduler.running:  # Periksa apakah scheduler sudah berjalan
        if not scheduler.get_jobs():
            scheduler.add_job(send_scheduled_emails, 'interval', minutes=1)
        scheduler.start()
