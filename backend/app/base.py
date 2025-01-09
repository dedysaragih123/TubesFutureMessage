from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

Base = declarative_base()

DATABASE_URL = "postgresql://postgres:Saragih123@postgres_db:5432/future_message"

engine = create_engine(DATABASE_URL)