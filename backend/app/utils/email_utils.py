import requests
from sqlalchemy.orm import Session
from app.models import Document, User, Collaborator  # Sesuaikan impor model Anda
from datetime import datetime
import os

def get_access_token():
    """
    Fungsi untuk mendapatkan access token dari API external.
    """
    url = "https://api.fintrackit.my.id/v1/auth/token"
    api_key = os.getenv("EXTERNAL_API_KEY", "key_btICYdooxK6e426PIxuGBW0Sc3yqePp7")
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
