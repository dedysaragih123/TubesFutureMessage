import requests
import logging
from fastapi import HTTPException
import os

# Load environment variables
IZIN_SAKIT_BASE_URL = os.getenv("IZIN_SAKIT_BASE_URL")
IZIN_SAKIT_AUTH_TOKEN = os.getenv("IZIN_SAKIT_AUTH_TOKEN")

# Headers for API requests
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {IZIN_SAKIT_AUTH_TOKEN}",
}

def create_sick_leave_request(username: str, reason: str):
    """
    Mengirim permohonan izin sakit baru ke service izinSakit.

    Args:
        username (str): Username pengguna yang mengajukan izin sakit.
        reason (str): Alasan izin sakit.

    Returns:
        dict: Respons dari API izinSakit.

    Raises:
        HTTPException: Jika terjadi kesalahan saat memanggil API.
    """
    try:
        url = f"{IZIN_SAKIT_BASE_URL.rstrip('/')}/sick-leave"
        payload = {"username": username, "reason": reason}

        logging.info(f"Request URL: {url}")
        logging.info(f"Payload: {payload}")
        logging.info(f"Headers: {HEADERS}")

        response = requests.post(url, json=payload, headers=HEADERS)
        logging.info(f"Response Status Code: {response.status_code}")
        logging.info(f"Response Content: {response.text}")
        response.raise_for_status()  # Raise error for HTTP response codes 4xx/5xx

        logging.info(f"Sick leave request created: {response.json()}")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 401:
            logging.error("Unauthorized: Invalid or expired token")
            raise HTTPException(status_code=401, detail="Unauthorized: Invalid or expired token")
        elif http_err.response.status_code == 400:
            logging.error(f"Bad Request: {http_err.response.text}")
            raise HTTPException(status_code=400, detail=http_err.response.text)
        elif http_err.response.status_code == 404:
            logging.error("Not Found: Check the API endpoint or resource")
            raise HTTPException(status_code=404, detail="Not Found: API endpoint or resource missing")
        raise HTTPException(status_code=502, detail=f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request failed: {req_err}")
        raise HTTPException(status_code=502, detail=f"Error connecting to izin sakit service: {str(req_err)}")

def submit_sick_leave_form(answers: dict):
    """
    Mengirim jawaban formulir izin sakit ke service izinSakit.

    Args:
        answers (dict): Jawaban formulir izin sakit.

    Returns:
        dict: Respons dari API izinSakit.

    Raises:
        HTTPException: Jika terjadi kesalahan saat memanggil API.
    """
    try:
        url = f"{IZIN_SAKIT_BASE_URL.rstrip('/')}/api/sick-leave-form"
        logging.info(f"Request URL: {url}")
        logging.info(f"Payload: {answers}")

        response = requests.post(url, json=answers, headers=HEADERS)
        logging.info(f"Response Status Code: {response.status_code}")
        logging.info(f"Response Content: {response.text}")
        response.raise_for_status()

        logging.info(f"Sick leave form answers submitted: {response.json()}")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP Error: {http_err.response.text}")
        raise HTTPException(status_code=http_err.response.status_code, detail=http_err.response.text)
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request failed: {req_err}")
        raise HTTPException(status_code=500, detail=f"Failed to submit sick leave form: {req_err}")

def generate_sick_leave_pdf(sick_leave_id: int):
    """
    Menghasilkan PDF untuk permohonan izin sakit.

    Args:
        sick_leave_id (int): ID permohonan izin sakit.

    Returns:
        dict: URL atau data PDF dari API izinSakit.

    Raises:
        HTTPException: Jika terjadi kesalahan saat memanggil API.
    """
    try:
        url = f"{IZIN_SAKIT_BASE_URL.rstrip('/')}/api/generate-pdf/{sick_leave_id}"
        logging.info(f"Request URL: {url}")

        response = requests.get(url, headers=HEADERS)
        logging.info(f"Response Status Code: {response.status_code}")
        logging.info(f"Response Content: {response.text}")
        response.raise_for_status()

        logging.info(f"PDF generated for sick leave ID {sick_leave_id}: {response.json()}")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP Error: {http_err.response.text}")
        raise HTTPException(status_code=http_err.response.status_code, detail=http_err.response.text)
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request failed: {req_err}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF for sick leave: {req_err}")
