#!/bin/bash
set -e
python3 -m pip install --upgrade pip
python3 -m pip install -e backend
exec gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
