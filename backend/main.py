"""FastAPI API for MAMORU BUS. SQLite development database; DATABASE_URL can point to PostgreSQL later."""
from datetime import datetime, timezone
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import DateTime, ForeignKey, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mamoru_bus.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
Session = sessionmaker(bind=engine)
class Base(DeclarativeBase): pass
class Child(Base):
    __tablename__ = "children"; id: Mapped[int] = mapped_column(primary_key=True); name: Mapped[str] = mapped_column(String(100)); qr_token: Mapped[str] = mapped_column(String(100), unique=True)
class SafetyEvent(Base):
    __tablename__ = "safety_events"; id: Mapped[int] = mapped_column(primary_key=True); child_id: Mapped[int|None] = mapped_column(ForeignKey("children.id"), nullable=True); event_type: Mapped[str] = mapped_column(String(40)); staff_name: Mapped[str] = mapped_column(String(100)); latitude: Mapped[str|None] = mapped_column(String(30)); longitude: Mapped[str|None] = mapped_column(String(30)); created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
class ScanIn(BaseModel): qr_token: str; event_type: str; staff_name: str; latitude: str|None=None; longitude: str|None=None
app = FastAPI(title="まもるバス API")
@app.on_event("startup")
def setup(): Base.metadata.create_all(engine)
@app.get("/health")
def health(): return {"status":"ok"}
@app.post("/api/scans")
def scan(data: ScanIn):
    with Session() as db:
        child = db.query(Child).filter_by(qr_token=data.qr_token).first()
        if not child: raise HTTPException(404, "QRコードが登録されていません")
        event = SafetyEvent(child_id=child.id,event_type=data.event_type,staff_name=data.staff_name,latitude=data.latitude,longitude=data.longitude); db.add(event); db.commit()
        return {"child": child.name, "event_id": event.id, "recorded_at": event.created_at}
