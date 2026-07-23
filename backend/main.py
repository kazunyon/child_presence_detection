"""MAMORU BUS backend. Defaults to SQLite; set DATABASE_URL for PostgreSQL."""
from datetime import datetime, timezone
import os
import hashlib
from typing import Generator

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, ForeignKey, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

raw_database_url = os.getenv("DATABASE_URL", "sqlite:///./mamoru_bus.db")
# Render returns postgres:// or postgresql:// URLs. SQLAlchemy uses the psycopg v3 driver explicitly.
DATABASE_URL = raw_database_url.replace("postgres://", "postgresql+psycopg://", 1).replace("postgresql://", "postgresql+psycopg://", 1)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

class Staff(Base):
    __tablename__ = "staff"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(40), default="職員")
    pin_hash: Mapped[str] = mapped_column(String(64), default=lambda: hash_pin("0000"))

class Vehicle(Base):
    __tablename__ = "vehicles"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    plate_number: Mapped[str | None] = mapped_column(String(30), nullable=True)

class BusRoute(Base):
    __tablename__ = "bus_routes"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    direction: Mapped[str] = mapped_column(String(20), default="往路")
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True)

class Child(Base):
    __tablename__ = "children"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    class_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    qr_token: Mapped[str] = mapped_column(String(100), unique=True)

class BusTrip(Base):
    __tablename__ = "bus_trips"
    id: Mapped[int] = mapped_column(primary_key=True)
    route_id: Mapped[int | None] = mapped_column(ForeignKey("bus_routes.id"), nullable=True)
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True)
    direction: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30), default="運行中")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class TripAttendance(Base):
    __tablename__ = "trip_attendance"
    id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("bus_trips.id"))
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id"))
    boarded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    alighted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    boarded_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    alighted_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

class NotificationQueue(Base):
    __tablename__ = "notification_queue"
    id: Mapped[int] = mapped_column(primary_key=True)
    recipient_type: Mapped[str] = mapped_column(String(30))
    recipient: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), default="queued")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class VehicleSafetyCheck(Base):
    __tablename__ = "vehicle_safety_checks"
    id: Mapped[int] = mapped_column(primary_key=True)
    check_type: Mapped[str] = mapped_column(String(40))
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id"))
    staff_name: Mapped[str] = mapped_column(String(100))
    qr_token: Mapped[str] = mapped_column(String(100))
    latitude: Mapped[str | None] = mapped_column(String(30), nullable=True)
    longitude: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class SafetyEvent(Base):
    __tablename__ = "safety_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int | None] = mapped_column(ForeignKey("children.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(40))
    staff_name: Mapped[str] = mapped_column(String(100))
    latitude: Mapped[str | None] = mapped_column(String(30), nullable=True)
    longitude: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class ConfigModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class ChildCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    class_name: str | None = Field(default=None, max_length=50)
    qr_token: str = Field(min_length=1, max_length=100)
class StaffCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    role: str = Field(default="職員", max_length=40)
class VehicleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    plate_number: str | None = Field(default=None, max_length=30)
class RouteCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    direction: str = Field(default="往路", max_length=20)
    vehicle_id: int | None = None
class TripCreate(BaseModel):
    route_id: int | None = None
    vehicle_id: int | None = None
    direction: str = "帰り"
class TripScanIn(BaseModel):
    qr_token: str
    event_type: str = Field(pattern="^(乗車|降車)$")
    staff_id: int
    staff_name: str

class NotificationIn(BaseModel):
    recipient_type: str
    recipient: str
    message: str

class VehicleCheckIn(BaseModel):
    check_type: str
    staff_id: int
    staff_name: str
    qr_token: str
    latitude: str | None = None
    longitude: str | None = None

class LoginIn(BaseModel):
    staff_id: int
    pin: str = Field(min_length=4, max_length=12)
class ScanIn(BaseModel):
    qr_token: str
    event_type: str
    staff_id: int
    staff_name: str
    latitude: str | None = None
    longitude: str | None = None

def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode("utf-8")).hexdigest()

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try: yield db
    finally: db.close()

def seed(db: Session) -> None:
    if db.query(Staff).count() == 0:
        db.add_all([Staff(name="田中 先生", role="運転担当", pin_hash=hash_pin("1234")), Staff(name="佐藤 先生", role="第三者確認", pin_hash=hash_pin("5678"))])
    if db.query(Vehicle).count() == 0:
        db.add(Vehicle(name="2号車", plate_number="品川 500 あ 1234"))
    db.commit()
    if db.query(BusRoute).count() == 0:
        vehicle = db.query(Vehicle).first()
        db.add(BusRoute(name="ひまわり園 送迎便", direction="帰り", vehicle_id=vehicle.id if vehicle else None))
    if db.query(Child).count() == 0:
        db.add_all([Child(name="さくら ちゃん", class_name="年少", qr_token="child-sakura"), Child(name="はると くん", class_name="年長", qr_token="child-haruto")])
    db.commit()

app = FastAPI(title="まもるバス API", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "*").split(","), allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def setup() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db: seed(db)

@app.get("/health")
def health() -> dict[str, str]: return {"status": "ok"}

@app.get("/api/bootstrap")
def bootstrap(db: Session = Depends(get_db)) -> dict:
    return {"children": db.query(Child).all(), "staff": db.query(Staff).all(), "vehicles": db.query(Vehicle).all(), "routes": db.query(BusRoute).all()}

@app.get("/api/children")
def list_children(db: Session = Depends(get_db)): return db.query(Child).order_by(Child.name).all()
@app.post("/api/children", status_code=status.HTTP_201_CREATED)
def create_child(data: ChildCreate, db: Session = Depends(get_db)):
    if db.query(Child).filter_by(qr_token=data.qr_token).first(): raise HTTPException(409, "このQRコードは登録済みです")
    item = Child(**data.model_dump()); db.add(item); db.commit(); db.refresh(item); return item

@app.get("/api/staff")
def list_staff(db: Session = Depends(get_db)): return db.query(Staff).order_by(Staff.name).all()
@app.post("/api/staff", status_code=status.HTTP_201_CREATED)
def create_staff(data: StaffCreate, db: Session = Depends(get_db)):
    item = Staff(**data.model_dump()); db.add(item); db.commit(); db.refresh(item); return item

@app.get("/api/vehicles")
def list_vehicles(db: Session = Depends(get_db)): return db.query(Vehicle).order_by(Vehicle.name).all()
@app.post("/api/vehicles", status_code=status.HTTP_201_CREATED)
def create_vehicle(data: VehicleCreate, db: Session = Depends(get_db)):
    if db.query(Vehicle).filter_by(name=data.name).first(): raise HTTPException(409, "この車両名は登録済みです")
    item = Vehicle(**data.model_dump()); db.add(item); db.commit(); db.refresh(item); return item

@app.get("/api/routes")
def list_routes(db: Session = Depends(get_db)): return db.query(BusRoute).order_by(BusRoute.name).all()
@app.post("/api/routes", status_code=status.HTTP_201_CREATED)
def create_route(data: RouteCreate, db: Session = Depends(get_db)):
    if data.vehicle_id and not db.get(Vehicle, data.vehicle_id): raise HTTPException(404, "車両が見つかりません")
    item = BusRoute(**data.model_dump()); db.add(item); db.commit(); db.refresh(item); return item

@app.post("/api/trips", status_code=status.HTTP_201_CREATED)
def create_trip(data: TripCreate, db: Session = Depends(get_db)):
    trip = BusTrip(**data.model_dump()); db.add(trip); db.commit(); db.refresh(trip); return trip

@app.post("/api/trips/{trip_id}/scans")
def trip_scan(trip_id: int, data: TripScanIn, db: Session = Depends(get_db)):
    trip = db.get(BusTrip, trip_id)
    staff = db.get(Staff, data.staff_id)
    child = db.query(Child).filter_by(qr_token=data.qr_token).first()
    if not trip: raise HTTPException(404, "運行便が見つかりません")
    if trip.status != "運行中": raise HTTPException(409, "この便は完了しています")
    if not staff or staff.name != data.staff_name: raise HTTPException(401, "ログイン状態を確認してください")
    if not child: raise HTTPException(404, "QRコードが登録されていません")
    attendance = db.query(TripAttendance).filter_by(trip_id=trip_id, child_id=child.id).first()
    if not attendance: attendance = TripAttendance(trip_id=trip_id, child_id=child.id); db.add(attendance)
    now = datetime.now(timezone.utc)
    if data.event_type == "乗車":
        if attendance.boarded_at: raise HTTPException(409, "この園児はすでに乗車済みです")
        attendance.boarded_at, attendance.boarded_by = now, staff.name
    else:
        if not attendance.boarded_at: raise HTTPException(409, "乗車記録がないため降車できません")
        if attendance.alighted_at: raise HTTPException(409, "この園児はすでに降車済みです")
        attendance.alighted_at, attendance.alighted_by = now, staff.name
    db.commit(); return {"child": child.name, "event_type": data.event_type, "trip_id": trip_id}

@app.get("/api/trips/{trip_id}/status")
def trip_status(trip_id: int, db: Session = Depends(get_db)):
    trip = db.get(BusTrip, trip_id)
    if not trip: raise HTTPException(404, "運行便が見つかりません")
    rows = db.query(TripAttendance, Child).join(Child, Child.id == TripAttendance.child_id).filter(TripAttendance.trip_id == trip_id).all()
    children = [{"child_id": c.id, "name": c.name, "boarded_at": a.boarded_at, "alighted_at": a.alighted_at} for a,c in rows]
    boarded = sum(1 for x in children if x["boarded_at"]); alighted = sum(1 for x in children if x["alighted_at"])
    return {"trip_id": trip_id, "status": trip.status, "boarded": boarded, "alighted": alighted, "unconfirmed": boarded-alighted, "children": children}

@app.post("/api/trips/{trip_id}/complete")
def complete_trip(trip_id: int, db: Session = Depends(get_db)):
    summary = trip_status(trip_id, db)
    if summary["unconfirmed"]: raise HTTPException(409, "未降車の園児がいるため完了できません")
    trip = db.get(BusTrip, trip_id); trip.status="完了"; trip.completed_at=datetime.now(timezone.utc); db.commit(); return {"status":"完了"}
@app.post("/api/notifications", status_code=status.HTTP_201_CREATED)
def queue_notification(data: NotificationIn, db: Session = Depends(get_db)):
    item = NotificationQueue(**data.model_dump()); db.add(item); db.commit(); db.refresh(item)
    return {"id": item.id, "status": item.status, "created_at": item.created_at}

@app.get("/api/notifications")
def list_notifications(db: Session = Depends(get_db)):
    return db.query(NotificationQueue).order_by(NotificationQueue.created_at.desc()).limit(100).all()
@app.post("/api/vehicle-checks", status_code=status.HTTP_201_CREATED)
def vehicle_check(data: VehicleCheckIn, db: Session = Depends(get_db)):
    staff = db.get(Staff, data.staff_id)
    if not staff or staff.name != data.staff_name: raise HTTPException(401, "ログイン状態を確認してください")
    item = VehicleSafetyCheck(**data.model_dump()); db.add(item); db.commit(); db.refresh(item)
    return {"id": item.id, "check_type": item.check_type, "recorded_at": item.created_at}
@app.post("/api/auth/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    staff = db.get(Staff, data.staff_id)
    if not staff or staff.pin_hash != hash_pin(data.pin):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="職員IDまたはPINが正しくありません")
    return {"id": staff.id, "name": staff.name, "role": staff.role}

@app.get("/api/rides/status")
def ride_status(db: Session = Depends(get_db)):
    result = []
    for child in db.query(Child).order_by(Child.name):
        latest = db.query(SafetyEvent).filter_by(child_id=child.id).order_by(SafetyEvent.created_at.desc()).first()
        result.append({"id": child.id, "name": child.name, "class_name": child.class_name, "qr_token": child.qr_token, "state": latest.event_type if latest else "未確認"})
    return result
@app.post("/api/scans")
def scan(data: ScanIn, db: Session = Depends(get_db)):
    staff = db.get(Staff, data.staff_id)
    if not staff or staff.name != data.staff_name: raise HTTPException(401, "ログイン状態を確認してください")
    child = db.query(Child).filter_by(qr_token=data.qr_token).first()
    if not child: raise HTTPException(404, "QRコードが登録されていません")
    event = SafetyEvent(child_id=child.id, event_type=data.event_type, staff_name=data.staff_name, latitude=data.latitude, longitude=data.longitude)
    db.add(event); db.commit(); db.refresh(event)
    return {"child": child.name, "event_id": event.id, "recorded_at": event.created_at}






