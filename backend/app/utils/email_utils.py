import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Document, User, Collaborator  # Sesuaikan impor model Anda

def send_email(db: Session, to_email: str, subject: str, body: str):
    # Konfigurasi SMTP
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "dedybisnis28@gmail.com"
    sender_password = "Saragih123"

    try:
        # Buat email
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Kirim email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()

        print(f"Email sent to {to_email}")
    except Exception as e:
        raise Exception(f"Failed to send email to {to_email}: {e}")
