#!/bin/bash
set -e
python3 -m pip install --upgrade pip
python3 -m pip install -e backend
python3 -m gunicorn app:app -c src/gunicorn.conf.py
