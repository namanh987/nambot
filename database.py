from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nambot.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id            = Column(String, primary_key=True, index=True)
    email         = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    plan          = Column(String, default="free")       # free | pro | unlimited
    token_balance = Column(Integer, default=50_000)      # free tier: 50k tokens
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=datetime.utcnow)


class UsageLog(Base):
    __tablename__ = "usage_history"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    user_id     = Column(String, index=True)
    bot         = Column(String)                         # nambot | anhbot | gembot | deepbot
    question    = Column(String)
    tokens_used = Column(Integer)
    timestamp   = Column(DateTime, default=datetime.utcnow)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
