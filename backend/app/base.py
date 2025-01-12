from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

Base = declarative_base()

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql://future-message-db_owner:6OFx8MJYcXsE@ep-icy-term-a122wq1s.ap-southeast-1.aws.neon.tech/future-message-db?sslmode=require"

engine = create_engine(DATABASE_URL)

IZIN_SAKIT_BASE_URL = os.getenv("IZIN_SAKIT_BASE_URL")
IZIN_SAKIT_AUTH_TOKEN = os.getenv("IZIN_SAKIT_AUTH_TOKEN")