import requests
from sqlalchemy.orm import Session
from app.models import Document, User, Collaborator  # Sesuaikan impor model Anda
from datetime import datetime
import os
from app.db import SessionLocal 
import logging
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

def get_access_token():
    """
    Fungsi untuk mendapatkan access token dari API external.
    """
    url = "https://api.fintrackit.my.id/v1/auth/token"
    api_key = os.getenv("EXTERNAL_API_KEY", "key_2frPCWYcsH54ughsWJ8_NYHC2WWm1H-Y")
    headers = {
        "X-API-Key": api_key
    }

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to retrieve access token: {e}")

def send_email(db: Session, document_id: int, to_email: str, subject: str, body: str):
    """
    Fungsi untuk mengirim email menggunakan layanan eksternal dengan pembaruan token otomatis.
    """
    bearer_token = get_access_token()
    url = "https://api.fintrackit.my.id/v1/secure/send-email"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "recipient_email": to_email,
        "subject": subject,
        "body": body
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        # Jika berhasil, kembalikan respon
        response.raise_for_status()
        print(f"Email sent successfully to {to_email}")

        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.is_sent = True
            document.sent_at = datetime.now()
            db.commit()

        return response.json()
    except requests.exceptions.HTTPError as http_err:
        # Tangani error jika token expired atau invalid
        if response.status_code == 401:  # Unauthorized
            print("Token expired or invalid. Requesting new token...")
            try:
                # Minta token baru
                new_token = get_access_token()
                print("New token retrieved successfully.")
                # Coba kirim ulang dengan token baru
                headers["Authorization"] = f"Bearer {new_token}"
                retry_response = requests.post(url, headers=headers, json=payload)
                retry_response.raise_for_status()
                print(f"Email sent successfully to {to_email} with refreshed token.")
                return retry_response.json()
            except Exception as e:
                raise Exception(f"Failed to refresh token and resend email: {e}")
        else:
            raise Exception(f"Failed to send email via external service: {http_err}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to send email via external service: {e}")

def send_scheduled_emails(document_id: int):
    """
    Kirim email sesuai dengan jadwal (delivery_date).
    """
    db = SessionLocal()
    try:
        logging.info(f"Processing scheduled email for document ID: {document_id}")

        # Ambil dokumen dari database
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logging.warning(f"Document ID {document_id} not found.")
            return

        # Periksa apakah dokumen sudah dikirim
        if document.is_sent:
            logging.info(f"Document ID {document_id} already sent.")
            return

        # Periksa apakah waktu saat ini >= delivery_date
        now = datetime.now()
        if now < document.delivery_date:
            logging.info(f"Document ID {document_id} scheduled for {document.delivery_date}. Not sending yet.")
            return

        # Ambil kolaborator untuk dokumen
        collaborators = (
            db.query(User.email)
            .join(Collaborator, User.id == Collaborator.collaborator_id)
            .filter(Collaborator.document_id == document_id)
            .all()
        )
        if not collaborators:
            logging.warning(f"No collaborators found for Document ID {document_id}. Skipping.")
            return

        # Kirim email ke setiap kolaborator
        for collaborator in collaborators:
            send_email(
                db=db,
                document_id=document_id,
                to_email=collaborator.email,
                subject=f"Document: {document.title}",
                body=document.content,
            )
            logging.info(f"Email sent to {collaborator.email}")

        # Tandai dokumen sebagai sudah dikirim
        document.is_sent = True
        document.sent_at = datetime.now()
        db.commit()
        logging.info(f"Document ID {document_id} marked as sent.")
    except Exception as e:
        logging.error(f"Error processing document ID {document_id}: {str(e)}")
    finally:
        db.close()
