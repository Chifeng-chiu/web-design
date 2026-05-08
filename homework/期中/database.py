import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 優先讀取環境變數 DATABASE_URL（Render PostgreSQL 會自動注入）
# 如果沒有則退回本地 SQLite（開發用）
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./stock_forum.db")

# Render 的 PostgreSQL URL 開頭是 postgres://，SQLAlchemy 需要 postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite 需要特別的 connect_args，PostgreSQL 不需要
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)
