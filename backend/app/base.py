from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

Base = declarative_base()

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres:Saragih123@localhost:5432/future_message"

engine = create_engine(DATABASE_URL)