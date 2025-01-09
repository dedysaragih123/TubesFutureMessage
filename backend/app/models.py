from sqlalchemy import create_engine, Column, String, Text, Integer, ForeignKey, Table, DateTime, Boolean
from sqlalchemy.orm import relationship, sessionmaker
from app.base import Base

DATABASE_URL = "postgresql://postgres:Saragih123@localhost:5432/future_message"

engine = create_engine(DATABASE_URL)

# Session untuk database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Many-to-Many Relationship Table
document_collaborators = Table(
    'document_collaborators',
    Base.metadata,
    Column('document_id', Integer, ForeignKey('documents.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Relasi ke Document
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")

    # Relasi ke Collaborator
    collaborations = relationship("Collaborator", back_populates="collaborator")

class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    delivery_date = Column(DateTime, nullable=True)
    owner_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)

    is_sent = Column(Boolean, default=False)  # Menandai dokumen sudah dikirim atau belum
    sent_at = Column(DateTime, nullable=True)

    # Relasi ke User
    owner = relationship("User", back_populates="documents")

    # Relasi ke Collaborators
    collaborators = relationship("Collaborator", back_populates="document")

class Collaborator(Base):
    __tablename__ = "collaborators"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)  # Perbaiki tipe data
    collaborator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relasi ke Document
    document = relationship("Document", back_populates="collaborators")

    # Relasi ke User
    collaborator = relationship("User", back_populates="collaborations")

