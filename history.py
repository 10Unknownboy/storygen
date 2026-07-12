from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from config import DATABASE_URL, IST_TZ

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UploadHistory(Base):
    __tablename__ = "upload_history"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    birthday = Column(String)
    upload_timestamp = Column(DateTime, default=lambda: datetime.now(IST_TZ).replace(tzinfo=None))
    media_id = Column(String, nullable=True)
    success = Column(Boolean, default=False)
    error_message = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)

def record_upload(username: str, birthday: str, success: bool, media_id: str = None, error_message: str = None):
    db = SessionLocal()
    try:
        record = UploadHistory(
            username=username,
            birthday=birthday,
            success=success,
            media_id=media_id,
            error_message=error_message
        )
        db.add(record)
        db.commit()
    finally:
        db.close()

def has_uploaded_today(username: str) -> bool:
    """Check if the user has a successful upload recorded today (IST)."""
    db = SessionLocal()
    try:
        today = datetime.now(IST_TZ).date()
        records = db.query(UploadHistory).filter(
            UploadHistory.username == username,
            UploadHistory.success == True
        ).all()
        
        for r in records:
            # Re-localize naive datetime from DB to IST
            dt_ist = IST_TZ.localize(r.upload_timestamp)
            if dt_ist.date() == today:
                return True
        return False
    finally:
        db.close()

def get_recent_uploads(limit=10):
    db = SessionLocal()
    try:
        return db.query(UploadHistory).order_by(UploadHistory.upload_timestamp.desc()).limit(limit).all()
    finally:
        db.close()
