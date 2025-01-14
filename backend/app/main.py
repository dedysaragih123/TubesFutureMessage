from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from app.routers import secure
from app import auth
from app.auth import get_user
from app.base import Base, engine
from app.db import SessionLocal  # Pastikan SessionLocal diimpor
from sqlalchemy.orm import Session
from app.models import Document, Collaborator, User
from datetime import datetime, timedelta  # Pastikan datetime diimpor
import logging
from apscheduler.schedulers.background import BackgroundScheduler

# Inisialisasi aplikasi
app = FastAPI()
scheduler = BackgroundScheduler()
import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
logging.info(f"Python version: {sys.version}")
logging.info(f"Working directory: {os.getcwd()}")
logging.info(f"Environment variables: {os.environ}")


# Middleware CORS (opsional jika frontend di-host di domain berbeda)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                #    "https://future-message-caexg0bxeha9d2et.southeastasia-01.azurewebsites.net",
                    "https://tubes-future-message-f185jejxu-dedys-projects-a843acc4.vercel.app",  # Domain khusus build Vercel
                   "https://tubes-future-message.vercel.app"],  # Ganti dengan domain deploy
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

# Function to start the scheduler
@app.on_event("startup")
def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        logging.info("Scheduler started.")

# Shutdown scheduler on application shutdown
@app.on_event("shutdown")
def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logging.info("Scheduler stopped.")