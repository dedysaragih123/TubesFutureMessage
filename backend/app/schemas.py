from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

# Document schemas
class DocumentBase(BaseModel):
    title: str
    content: str
    delivery_date: Optional[datetime] = None
    collaborators: Optional[List[EmailStr]] = Field(default_factory=list)  # Daftar email kolaborator disimpan langsung di tabel documents

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    id: int  # ID dokumen yang akan diupdate
    title: Optional[str]
    content: Optional[str]
    delivery_date: Optional[datetime]

class DocumentResponse(DocumentBase):
    id: int
    owner_id: int

class CollaboratorAdd(BaseModel):
    document_id: int
    collaborator_email: EmailStr

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class DocumentCreate(BaseModel):
    title: str
    content: str
    delivery_date: datetime
    collaborators: List[EmailStr] = Field(default_factory=list)

    @validator("delivery_date", pre=True)
    def validate_delivery_date(cls, value):
        # Tambahkan waktu default jika hanya tanggal diberikan
        if isinstance(value, str) and len(value) == 10:  # Format: YYYY-MM-DD
            value += "T00:00:00"
        
        delivery_date = datetime.fromisoformat(value)
        if delivery_date < datetime.now():
            raise ValueError("Delivery date must be in the future.")
        return delivery_date
    
class EmailRequest(BaseModel):
    to_email: EmailStr
    subject: str
    body: str

class LoginRequest(BaseModel):
    username: EmailStr
    password: str