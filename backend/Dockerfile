# Gunakan image Python sebagai dasar
FROM python:3.11-slim

# Instal dependensi yang diperlukan
RUN apt-get update && apt-get install -y build-essential libpq-dev && \
    pip install --upgrade pip

# Tentukan direktori kerja di dalam container
WORKDIR /app

# Salin file requirements ke dalam container
COPY requirements.txt /app/

# Instal semua dependensi Python
RUN pip install -r requirements.txt

# Salin semua file aplikasi ke dalam container
COPY ./app /app

# Jalankan aplikasi
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
