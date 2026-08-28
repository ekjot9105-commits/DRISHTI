"""
IBVAP Database Setup — SQLite with SQLAlchemy
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from datetime import datetime, timezone

from app.core.config import DATABASE_URL


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Camera(Base):
    """Camera source — either a video file or RTSP stream."""
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    source_type = Column(String(20), nullable=False)  # "file" or "rtsp"
    source_url = Column(Text, nullable=False)  # file path or RTSP URL
    status = Column(String(20), default="inactive")  # active, inactive, error
    location = Column(String(200), default="")  # descriptive location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Event(Base):
    """Detection event logged by the AI pipeline."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(Integer, nullable=False)
    event_type = Column(String(50), nullable=False)  # human_detected, vehicle_detected, face_match, etc.
    severity = Column(String(20), default="info")  # info, warning, critical
    object_class = Column(String(50), default="")
    confidence = Column(Float, default=0.0)
    details = Column(Text, default="")  # JSON string with extra info
    thumbnail_path = Column(Text, default="")
    status = Column(String(20), default="new") # new, acknowledged, resolved, archived
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class WatchlistFace(Base):
    """Face in the recognition watchlist."""
    __tablename__ = "watchlist_faces"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    image_path = Column(Text, nullable=False)
    embedding_path = Column(Text, default="")  # path to stored embedding
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class WatchlistPlate(Base):
    """Vehicle plate in the ANPR watchlist."""
    __tablename__ = "watchlist_plates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plate_number = Column(String(20), nullable=False, unique=True)
    vehicle_description = Column(Text, default="")
    owner_name = Column(String(100), default="")
    alert_level = Column(String(20), default="warning")  # info, warning, critical
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
