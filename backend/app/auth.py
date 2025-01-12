from fastapi import Depends, HTTPException, APIRouter, Request
from sqlalchemy.orm import Session
from app.db import get_user_by_email, get_db
from app.schemas import UserCreate, UserLogin
from app.user_crud import create_user
from app.models import User
from passlib.context import CryptContext
from jose import jwt,JWTError
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
import logging

router = APIRouter()
SECRET_KEY = "e4f01b2c8a4e4268f9ad3e3f5c2a4d2e4c8f0a1d3b6c7e2f1a0d5f9c8b1e2a4" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

@router.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    try:
        existing_user = get_user_by_email(db, email=user.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        new_user = create_user(db, user=user)
        return {"message": "User successfully created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def get_user(email: str, db: Session = Depends(get_db)):
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def create_access_token(data: dict):
    to_encode = data.copy()   
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # Token berlaku 1 jam
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    try:
        # Cari pengguna berdasarkan email
        db_user = db.query(User).filter(User.email == user.email).first()
        if not db_user:
            # Jika email tidak ditemukan
            raise HTTPException(status_code=404, detail="Email is not registered")

        # Verifikasi password
        if not pwd_context.verify(user.password, db_user.hashed_password):
            # Jika password salah
            raise HTTPException(status_code=401, detail="Incorrect password")

        # Generate token jika login berhasil
        token = create_access_token(data={"sub": db_user.email})
        return {"access_token": token, "token_type": "bearer"}

    except HTTPException as e:
        logging.warning(f"Login failed: {e.detail}")
        raise e
    except Exception as e:
        logging.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred during login")

def verify_password(plain_password: str, hashed_password: str):
    """
    Fungsi untuk memverifikasi password pengguna.
    """
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        logging.info(f"Received token: {token}")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError as e:
        logging.error(f"JWT decoding error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")
    
