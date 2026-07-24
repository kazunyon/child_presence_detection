"""MAMORU BUS API — tenant-scoped safety record backend."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import pbkdf2_hmac, sha256
import base64
import hmac
import json
import os
from pathlib import Path
import secrets
from typing import Generator, Literal
from urllib.error import URLError
from urllib.request import Request as UrlRequest, urlopen
from uuid import NAMESPACE_URL, uuid4, uuid5

from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine, inspect, or_, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

raw_database_url = os.getenv("DATABASE_URL", "sqlite:///./mamoru_bus.db")
DATABASE_URL = raw_database_url.replace("postgres://", "postgresql+psycopg://", 1).replace("postgresql://", "postgresql+psycopg://", 1)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
JWT_SECRET = os.getenv("JWT_SECRET", "development-only-change-me")
JWT_ALGORITHM = "HS256"
TOKEN_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "480"))
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads")).resolve()
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_ORGANIZATION_ID = int(os.getenv("LINE_ORGANIZATION_ID", "0"))
security = HTTPBearer()


class Base(DeclarativeBase):
    pass


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Staff(Base):
    __tablename__ = "staff"
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(40), default="operator")
    password_hash: Mapped[str] = mapped_column(String(256))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (UniqueConstraint("organization_id", "name", name="uq_vehicle_org_name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    plate_number: Mapped[str | None] = mapped_column(String(30), nullable=True)


class BusRoute(Base):
    __tablename__ = "bus_routes"
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    direction: Mapped[str] = mapped_column(String(20), default="往路")
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True)


class Child(Base):
    __tablename__ = "children"
    __table_args__ = (UniqueConstraint("organization_id", "qr_token", name="uq_child_org_qr"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    class_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    qr_token: Mapped[str] = mapped_column(String(100))


class BusTrip(Base):
    __tablename__ = "bus_trips"
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    route_id: Mapped[int | None] = mapped_column(ForeignKey("bus_routes.id"), nullable=True)
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True)
    direction: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30), default="運行中")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class TripAttendance(Base):
    __tablename__ = "trip_attendance"
    __table_args__ = (UniqueConstraint("trip_id", "child_id", name="uq_attendance_trip_child"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("bus_trips.id"))
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id"))
    boarded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    alighted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    boarded_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    alighted_by: Mapped[str | None] = mapped_column(String(100), nullable=True)


class VehicleSafetyCheck(Base):
    __tablename__ = "vehicle_safety_checks"
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    trip_id: Mapped[int | None] = mapped_column(ForeignKey("bus_trips.id"), nullable=True)
    check_type: Mapped[str] = mapped_column(String(40))
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id"))
    staff_name: Mapped[str] = mapped_column(String(100))
    qr_token: Mapped[str] = mapped_column(String(100))
    latitude: Mapped[str | None] = mapped_column(String(30), nullable=True)
    longitude: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class NotificationQueue(Base):
    __tablename__ = "notification_queue"
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    recipient_type: Mapped[str] = mapped_column(String(30))
    recipient: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(String(500))
    channel: Mapped[str] = mapped_column(String(30), default="webhook")
    status: Mapped[str] = mapped_column(String(30), default="queued")
    provider_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class LineContact(Base):
    __tablename__ = "line_contacts"
    __table_args__ = (UniqueConstraint("organization_id", "line_user_id", name="uq_line_contact_org_user"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    line_user_id: Mapped[str] = mapped_column(String(100))
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("staff.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    resource_type: Mapped[str] = mapped_column(String(60))
    resource_id: Mapped[str] = mapped_column(String(60))
    detail: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class AdminPinRecovery(Base):
    __tablename__ = "admin_pin_recoveries"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id"))
    used_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class SyncEvent(Base):
    __tablename__ = "sync_events"
    __table_args__ = (UniqueConstraint("organization_id", "client_event_id", name="uq_sync_org_event"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    client_event_id: Mapped[str] = mapped_column(String(80))
    outcome: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class VideoEvidence(Base):
    __tablename__ = "video_evidence"
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("bus_trips.id"))
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("staff.id"))
    file_name: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(255), unique=True)
    content_type: Mapped[str] = mapped_column(String(100))
    ai_status: Mapped[str] = mapped_column(String(30), default="queued")
    ai_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class LoginIn(BaseModel):
    staff_id: int
    pin: str = Field(min_length=4, max_length=128)

class StaffCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    role: Literal["admin", "operator", "verifier"] = "operator"
    pin: str = Field(min_length=8, max_length=128)
class ChildCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    class_name: str | None = Field(default=None, max_length=50)
    qr_token: str = Field(min_length=1, max_length=100)
class VehicleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    plate_number: str | None = Field(default=None, max_length=30)
class RouteCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    direction: str = Field(default="往路", max_length=20)
    vehicle_id: int | None = None
class OrganizationUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
class ChildUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    class_name: str | None = Field(default=None, max_length=50)
    qr_token: str | None = Field(default=None, min_length=1, max_length=100)
class StaffUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    role: Literal["admin", "operator", "verifier"] | None = None
    pin: str | None = Field(default=None, min_length=4, max_length=128)
    is_active: bool | None = None
class VehicleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    plate_number: str | None = Field(default=None, max_length=30)
class RouteUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    direction: str | None = Field(default=None, max_length=20)
    vehicle_id: int | None = None
class TripCreate(BaseModel):
    route_id: int | None = None
    vehicle_id: int | None = None
    direction: str = "帰り"
class TripScanIn(BaseModel):
    qr_token: str
    event_type: Literal["乗車", "降車"]
class VehicleCheckIn(BaseModel):
    trip_id: int | None = None
    check_type: str = Field(min_length=1, max_length=40)
    qr_token: str = Field(min_length=1, max_length=100)
    latitude: str | None = None
    longitude: str | None = None
class NotificationIn(BaseModel):
    recipient_type: str
    recipient: str
    message: str = Field(max_length=500)
    channel: Literal["line", "webhook", "email", "sms", "push"] = "line"
class ThirdApprovalIn(BaseModel):
    staff_id: int
    pin: str = Field(min_length=4, max_length=128)

class AdminPinRecoveryIn(BaseModel):
    staff_id: int = 3
    new_pin: str = Field(min_length=8, max_length=128)

class SyncItem(BaseModel):
    client_event_id: str = Field(min_length=1, max_length=80)
    trip_id: int
    qr_token: str
    event_type: Literal["乗車", "降車"]
class SyncIn(BaseModel):
    events: list[SyncItem] = Field(max_length=100)


def hash_pin(pin: str) -> str:
    salt = secrets.token_bytes(16)
    derived = pbkdf2_hmac("sha256", pin.encode(), salt, 210_000)
    return "pbkdf2_sha256$210000$" + base64.b64encode(salt + derived).decode()


def verify_pin(pin: str, encoded: str) -> bool:
    try:
        _, rounds, payload = encoded.split("$", 2)
        raw = base64.b64decode(payload.encode())
        actual = pbkdf2_hmac("sha256", pin.encode(), raw[:16], int(rounds))
        return hmac.compare_digest(raw[16:], actual)
    except (ValueError, TypeError):
        return False


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def audit(db: Session, actor: Staff | None, action: str, resource_type: str, resource_id: int | str, detail: dict | None = None) -> None:
    db.add(AuditLog(organization_id=actor.organization_id if actor else 0, actor_id=actor.id if actor else None, action=action, resource_type=resource_type, resource_id=str(resource_id), detail=json.dumps(detail or {}, ensure_ascii=False)))


def current_staff(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> Staff:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        staff_id, organization_id = int(payload["sub"]), int(payload["org"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "認証情報が無効です")
    staff = db.get(Staff, staff_id)
    if not staff or not staff.is_active or staff.organization_id != organization_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "ログインし直してください")
    return staff


def require_roles(*roles: str):
    def dependency(actor: Staff = Depends(current_staff)) -> Staff:
        if actor.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "この操作を行う権限がありません")
        return actor
    return dependency


def trip_for_org(db: Session, trip_id: int, actor: Staff) -> BusTrip:
    trip = db.get(BusTrip, trip_id)
    if not trip or trip.organization_id != actor.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "運行便が見つかりません")
    return trip


def scan_trip(db: Session, actor: Staff, trip_id: int, qr_token: str, event_type: str) -> dict:
    trip = trip_for_org(db, trip_id, actor)
    if trip.status != "運行中":
        raise HTTPException(status.HTTP_409_CONFLICT, "この便は完了しています")
    child = db.query(Child).filter_by(organization_id=actor.organization_id, qr_token=qr_token).first()
    if not child:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "QRコードが登録されていません")
    attendance = db.query(TripAttendance).filter_by(trip_id=trip.id, child_id=child.id).first()
    if not attendance:
        attendance = TripAttendance(trip_id=trip.id, child_id=child.id)
        db.add(attendance)
    now = datetime.now(timezone.utc)
    if event_type == "乗車":
        if attendance.boarded_at:
            raise HTTPException(status.HTTP_409_CONFLICT, "この園児はすでに乗車済みです")
        attendance.boarded_at, attendance.boarded_by = now, actor.name
    else:
        if not attendance.boarded_at:
            raise HTTPException(status.HTTP_409_CONFLICT, "乗車記録がないため降車できません")
        if attendance.alighted_at:
            raise HTTPException(status.HTTP_409_CONFLICT, "この園児はすでに降車済みです")
        attendance.alighted_at, attendance.alighted_by = now, actor.name
    audit(db, actor, f"trip.{event_type}", "trip", trip.id, {"child_id": child.id})
    return {"child": child.name, "event_type": event_type, "trip_id": trip.id}


def trip_summary(db: Session, trip: BusTrip) -> dict:
    rows = db.query(TripAttendance, Child).join(Child, Child.id == TripAttendance.child_id).filter(TripAttendance.trip_id == trip.id).all()
    children = [{"child_id": c.id, "name": c.name, "boarded_at": a.boarded_at, "alighted_at": a.alighted_at} for a, c in rows]
    boarded = sum(x["boarded_at"] is not None for x in children)
    alighted = sum(x["alighted_at"] is not None for x in children)
    check_types = {row[0] for row in db.query(VehicleSafetyCheck.check_type).filter_by(organization_id=trip.organization_id, trip_id=trip.id).all()}
    return {
        "trip_id": trip.id,
        "status": trip.status,
        "boarded": boarded,
        "alighted": alighted,
        "unconfirmed": boarded - alighted,
        "tail_confirmed": "tail_qr" in check_types,
        "third_party_confirmed": "third_party" in check_types,
        "children": children,
    }


def seed(db: Session) -> None:
    # The legacy migration can create the first organization before any staff.
    # Seed only a truly empty staff directory, and reuse that organization.
    if db.query(Staff).count():
        return
    org = db.query(Organization).order_by(Organization.id).first()
    if not org:
        org = Organization(name="デモ園")
        db.add(org); db.flush()
    db.add_all([
        Staff(organization_id=org.id, name="田中 先生", role="operator", password_hash=hash_pin("1234")),
        Staff(organization_id=org.id, name="佐藤 先生", role="verifier", password_hash=hash_pin("5678")),
        Staff(organization_id=org.id, name="管理者", role="admin", password_hash=hash_pin("admin1234")),
        Vehicle(organization_id=org.id, name="2号車", plate_number="品川 500 あ 1234"),
        Child(organization_id=org.id, name="さくら ちゃん", class_name="年少", qr_token="child-sakura"),
        Child(organization_id=org.id, name="はると くん", class_name="年長", qr_token="child-haruto"),
    ])
    db.flush()
    vehicle = db.query(Vehicle).filter_by(organization_id=org.id).first()
    db.add(BusRoute(organization_id=org.id, name="ひまわり園 送迎便", direction="帰り", vehicle_id=vehicle.id))
    db.commit()


def migrate_legacy_database() -> None:
    """Upgrade the original single-kindergarten schema without deleting its records."""
    legacy_columns = {
        "staff": {"organization_id": "INTEGER", "password_hash": "VARCHAR(256)", "is_active": "BOOLEAN DEFAULT TRUE"},
        "vehicles": {"organization_id": "INTEGER"},
        "bus_routes": {"organization_id": "INTEGER"},
        "children": {"organization_id": "INTEGER"},
        "bus_trips": {"organization_id": "INTEGER"},
        "vehicle_safety_checks": {"organization_id": "INTEGER", "trip_id": "INTEGER"},
        "notification_queue": {"organization_id": "INTEGER", "channel": "VARCHAR(30) DEFAULT 'webhook'", "provider_response": "TEXT", "sent_at": "TIMESTAMP"},
    }
    tables = set(inspect(engine).get_table_names())
    with engine.begin() as connection:
        for table, columns in legacy_columns.items():
            if table not in tables:
                continue
            existing = {column["name"] for column in inspect(connection).get_columns(table)}
            for name, definition in columns.items():
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))

        # Old installations stored all data in one kindergarten. Keep that data and
        # attach it to one organization before tenant filtering is enabled.
        org_id = connection.execute(text("SELECT id FROM organizations ORDER BY id LIMIT 1")).scalar()
        if org_id is None:
            org_id = connection.execute(text("INSERT INTO organizations (name, created_at) VALUES (:name, :created_at) RETURNING id"), {"name": "既存園", "created_at": datetime.now(timezone.utc)}).scalar()
        for table in ("staff", "vehicles", "bus_routes", "children", "bus_trips", "vehicle_safety_checks", "notification_queue"):
            if table in tables:
                connection.execute(text(f"UPDATE {table} SET organization_id = :org_id WHERE organization_id IS NULL"), {"org_id": org_id})

    with SessionLocal() as db:
        # Legacy installations used SHA-256 PIN hashes. Convert the shipped staff
        # accounts to the current slow password hash on first startup.
        pin_by_name = {"田中 先生": "1234", "佐藤 先生": "5678", "管理者": "admin1234"}
        role_map = {"運転担当": "operator", "第三者確認": "verifier", "管理者": "admin", "職員": "operator"}
        changed = False
        for staff in db.query(Staff).all():
            # Shipped test accounts used a legacy SHA-256 value before PBKDF2.
            # Repair only those named defaults; never overwrite a current PBKDF2 PIN.
            if staff.name in pin_by_name and (not staff.password_hash or not staff.password_hash.startswith("pbkdf2_sha256$")):
                staff.password_hash = hash_pin(pin_by_name[staff.name]); changed = True
            if not staff.is_active:
                staff.is_active = True; changed = True
            mapped_role = role_map.get(staff.role)
            if mapped_role and staff.role != mapped_role:
                staff.role = mapped_role; changed = True
        if changed:
            db.commit()
app = FastAPI(title="まもるバス API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","), allow_methods=["*"], allow_headers=["*"], allow_credentials=True)

@app.on_event("startup")
def setup() -> None:
    Base.metadata.create_all(engine)
    migrate_legacy_database()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with SessionLocal() as db:
        seed(db)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/api/auth/login")
def login(data: LoginIn, db: Session = Depends(get_db)) -> dict:
    staff = db.get(Staff, data.staff_id)
    if not staff or not staff.is_active or not verify_pin(data.pin, staff.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "職員IDまたはPINが正しくありません")
    expires = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_MINUTES)
    token = jwt.encode({"sub": str(staff.id), "org": staff.organization_id, "role": staff.role, "exp": expires}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    audit(db, staff, "auth.login", "staff", staff.id); db.commit()
    return {"access_token": token, "token_type": "bearer", "staff": {"id": staff.id, "name": staff.name, "role": staff.role}, "expires_at": expires}

@app.post("/api/admin-recovery/reset-pin")
def reset_admin_pin(data: AdminPinRecoveryIn, x_admin_recovery_token: str | None = Header(default=None), db: Session = Depends(get_db)) -> dict:
    """One-time emergency recovery. Enable only with a Render secret, then remove it."""
    configured_token = os.getenv("ADMIN_PIN_RECOVERY_TOKEN")
    if not configured_token or not x_admin_recovery_token or not hmac.compare_digest(configured_token, x_admin_recovery_token):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "管理者PIN復旧は許可されていません")
    token_hash = sha256(configured_token.encode()).hexdigest()
    if db.get(AdminPinRecovery, token_hash):
        raise HTTPException(status.HTTP_409_CONFLICT, "この復旧トークンは使用済みです。Renderから削除してください")
    staff = db.get(Staff, data.staff_id)
    if not staff or staff.role != "admin":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "管理者アカウントが見つかりません")
    staff.password_hash, staff.is_active = hash_pin(data.new_pin), True
    db.add(AdminPinRecovery(token_hash=token_hash, staff_id=staff.id))
    audit(db, staff, "auth.admin_pin_recovery", "staff", staff.id, {"method": "one_time_recovery_token"})
    db.commit()
    return {"staff_id": staff.id, "status": "pin_reset"}

@app.get("/api/auth/me")
def me(actor: Staff = Depends(current_staff)) -> dict:
    return {"id": actor.id, "name": actor.name, "role": actor.role, "organization_id": actor.organization_id}

@app.get("/api/dashboard")
def dashboard(actor: Staff = Depends(current_staff), db: Session = Depends(get_db)) -> dict:
    organization = db.get(Organization, actor.organization_id)
    now = datetime.now(timezone.utc)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    trips = db.query(BusTrip).filter(BusTrip.organization_id == actor.organization_id, BusTrip.started_at >= day_start, BusTrip.started_at < day_end).order_by(BusTrip.started_at.desc()).all()
    summaries = [trip_summary(db, trip) for trip in trips]
    return {
        "organization_name": organization.name if organization else "園",
        "date": day_start.date().isoformat(),
        "today_trip_count": len(trips),
        "active_trip_count": sum(1 for trip in trips if trip.status == "運行中"),
        "completed_trip_count": sum(1 for trip in trips if trip.status == "完了"),
        "unconfirmed_count": sum(summary["unconfirmed"] for summary in summaries),
        "recent_trips": [{"trip_id": trip.id, "status": trip.status, "direction": trip.direction, "started_at": trip.started_at, "unconfirmed": summary["unconfirmed"]} for trip, summary in zip(trips[:5], summaries[:5])],
    }
@app.get("/api/bootstrap")
def bootstrap(actor: Staff = Depends(current_staff), db: Session = Depends(get_db)) -> dict:
    oid = actor.organization_id
    children = db.query(Child).filter_by(organization_id=oid).order_by(Child.name).all()
    staff = db.query(Staff).filter_by(organization_id=oid).order_by(Staff.name).all()
    vehicles = db.query(Vehicle).filter_by(organization_id=oid).order_by(Vehicle.name).all()
    routes = db.query(BusRoute).filter_by(organization_id=oid).order_by(BusRoute.name).all()
    return {
        "children": [{"id": item.id, "name": item.name, "class_name": item.class_name, "qr_token": item.qr_token} for item in children],
        "staff": [{"id": item.id, "name": item.name, "role": item.role, "is_active": item.is_active} for item in staff],
        "vehicles": [{"id": item.id, "name": item.name, "plate_number": item.plate_number} for item in vehicles],
        "routes": [{"id": item.id, "name": item.name, "direction": item.direction, "vehicle_id": item.vehicle_id} for item in routes],
    }

def staff_public(item: Staff) -> dict:
    return {"id": item.id, "name": item.name, "role": item.role, "is_active": item.is_active}

@app.get("/api/organization")
def current_organization(actor: Staff = Depends(current_staff), db: Session = Depends(get_db)) -> dict:
    item = db.get(Organization, actor.organization_id)
    if not item: raise HTTPException(status.HTTP_404_NOT_FOUND, "園情報が見つかりません")
    return {"id": item.id, "name": item.name, "created_at": item.created_at}
@app.put("/api/organization")
def update_organization(data: OrganizationUpdate, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> dict:
    item = db.get(Organization, actor.organization_id)
    if not item: raise HTTPException(status.HTTP_404_NOT_FOUND, "園情報が見つかりません")
    duplicate = db.query(Organization).filter(Organization.name == data.name, Organization.id != item.id).first()
    if duplicate: raise HTTPException(status.HTTP_409_CONFLICT, "この園名は登録済みです")
    item.name = data.name; audit(db, actor, "organization.update", "organization", item.id, {"name": item.name}); db.commit()
    return {"id": item.id, "name": item.name, "created_at": item.created_at}

@app.get("/api/children")
def list_children(actor: Staff = Depends(current_staff), db: Session = Depends(get_db)):
    return db.query(Child).filter_by(organization_id=actor.organization_id).order_by(Child.name).all()
@app.post("/api/children", status_code=status.HTTP_201_CREATED)
def create_child(data: ChildCreate, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    if db.query(Child).filter_by(organization_id=actor.organization_id, qr_token=data.qr_token).first(): raise HTTPException(status.HTTP_409_CONFLICT, "このQRコードは登録済みです")
    item = Child(organization_id=actor.organization_id, **data.model_dump()); db.add(item); db.flush(); audit(db, actor, "child.create", "child", item.id); db.commit(); db.refresh(item); return item
@app.put("/api/children/{child_id}")
def update_child(child_id: int, data: ChildUpdate, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    item = db.query(Child).filter_by(id=child_id, organization_id=actor.organization_id).first()
    if not item: raise HTTPException(status.HTTP_404_NOT_FOUND, "園児が見つかりません")
    values = data.model_dump(exclude_unset=True)
    if values.get("qr_token") and db.query(Child).filter(Child.organization_id == actor.organization_id, Child.qr_token == values["qr_token"], Child.id != item.id).first(): raise HTTPException(status.HTTP_409_CONFLICT, "このQRコードは登録済みです")
    for key, value in values.items(): setattr(item, key, value)
    audit(db, actor, "child.update", "child", item.id, values); db.commit(); return item

@app.get("/api/staff")
def list_staff(actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return [staff_public(item) for item in db.query(Staff).filter_by(organization_id=actor.organization_id).order_by(Staff.name).all()]
@app.post("/api/staff", status_code=status.HTTP_201_CREATED)
def create_staff(data: StaffCreate, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    item = Staff(organization_id=actor.organization_id, name=data.name, role=data.role, password_hash=hash_pin(data.pin)); db.add(item); db.flush(); audit(db, actor, "staff.create", "staff", item.id); db.commit(); return staff_public(item)
@app.put("/api/staff/{staff_id}")
def update_staff(staff_id: int, data: StaffUpdate, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    item = db.query(Staff).filter_by(id=staff_id, organization_id=actor.organization_id).first()
    if not item: raise HTTPException(status.HTTP_404_NOT_FOUND, "職員が見つかりません")
    values = data.model_dump(exclude_unset=True)
    removes_admin = item.role == "admin" and (values.get("role") not in (None, "admin") or values.get("is_active") is False)
    if removes_admin and db.query(Staff).filter_by(organization_id=actor.organization_id, role="admin", is_active=True).count() <= 1: raise HTTPException(status.HTTP_409_CONFLICT, "最後の管理者は変更・無効化できません")
    if item.id == actor.id and values.get("is_active") is False: raise HTTPException(status.HTTP_409_CONFLICT, "自分自身は無効化できません")
    if "pin" in values: item.password_hash = hash_pin(values.pop("pin"))
    for key, value in values.items(): setattr(item, key, value)
    audit(db, actor, "staff.update", "staff", item.id, {key: value for key, value in values.items() if key != "pin"}); db.commit(); return staff_public(item)

@app.get("/api/vehicles")
def list_vehicles(actor: Staff = Depends(current_staff), db: Session = Depends(get_db)):
    return db.query(Vehicle).filter_by(organization_id=actor.organization_id).order_by(Vehicle.name).all()
@app.post("/api/vehicles", status_code=status.HTTP_201_CREATED)
def create_vehicle(data: VehicleCreate, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    item = Vehicle(organization_id=actor.organization_id, **data.model_dump()); db.add(item); db.flush(); audit(db, actor, "vehicle.create", "vehicle", item.id); db.commit(); return item
@app.put("/api/vehicles/{vehicle_id}")
def update_vehicle(vehicle_id: int, data: VehicleUpdate, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    item = db.query(Vehicle).filter_by(id=vehicle_id, organization_id=actor.organization_id).first()
    if not item: raise HTTPException(status.HTTP_404_NOT_FOUND, "車両が見つかりません")
    values=data.model_dump(exclude_unset=True)
    for key, value in values.items(): setattr(item, key, value)
    audit(db, actor, "vehicle.update", "vehicle", item.id, values); db.commit(); return item

@app.get("/api/routes")
def list_routes(actor: Staff = Depends(current_staff), db: Session = Depends(get_db)):
    return db.query(BusRoute).filter_by(organization_id=actor.organization_id).order_by(BusRoute.name).all()
@app.post("/api/routes", status_code=status.HTTP_201_CREATED)
def create_route(data: RouteCreate, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    if data.vehicle_id and not db.query(Vehicle).filter_by(id=data.vehicle_id, organization_id=actor.organization_id).first(): raise HTTPException(status.HTTP_404_NOT_FOUND, "車両が見つかりません")
    item = BusRoute(organization_id=actor.organization_id, **data.model_dump()); db.add(item); db.flush(); audit(db, actor, "route.create", "route", item.id); db.commit(); return item
@app.put("/api/routes/{route_id}")
def update_route(route_id: int, data: RouteUpdate, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    item = db.query(BusRoute).filter_by(id=route_id, organization_id=actor.organization_id).first()
    if not item: raise HTTPException(status.HTTP_404_NOT_FOUND, "便が見つかりません")
    values=data.model_dump(exclude_unset=True)
    if values.get("vehicle_id") and not db.query(Vehicle).filter_by(id=values["vehicle_id"], organization_id=actor.organization_id).first(): raise HTTPException(status.HTTP_404_NOT_FOUND, "車両が見つかりません")
    for key, value in values.items(): setattr(item, key, value)
    audit(db, actor, "route.update", "route", item.id, values); db.commit(); return item

@app.post("/api/trips", status_code=status.HTTP_201_CREATED)
def create_trip(data: TripCreate, actor: Staff = Depends(current_staff), db: Session = Depends(get_db)):
    if data.route_id and not db.query(BusRoute).filter_by(id=data.route_id, organization_id=actor.organization_id).first(): raise HTTPException(404, "便が見つかりません")
    if data.vehicle_id and not db.query(Vehicle).filter_by(id=data.vehicle_id, organization_id=actor.organization_id).first(): raise HTTPException(404, "車両が見つかりません")
    trip = BusTrip(organization_id=actor.organization_id, **data.model_dump()); db.add(trip); db.flush(); audit(db, actor, "trip.create", "trip", trip.id); db.commit(); db.refresh(trip); return trip

@app.get("/api/trips")
def list_trips(from_at: datetime | None = None, to_at: datetime | None = None, status_filter: str | None = None, actor: Staff = Depends(current_staff), db: Session = Depends(get_db)):
    query = db.query(BusTrip).filter_by(organization_id=actor.organization_id)
    if from_at: query = query.filter(BusTrip.started_at >= from_at)
    if to_at: query = query.filter(BusTrip.started_at <= to_at)
    if status_filter: query = query.filter(BusTrip.status == status_filter)
    return [trip_summary(db, trip) | {"started_at": trip.started_at, "completed_at": trip.completed_at, "direction": trip.direction} for trip in query.order_by(BusTrip.started_at.desc()).limit(200)]

@app.post("/api/trips/{trip_id}/scans")
def trip_scan(trip_id: int, data: TripScanIn, actor: Staff = Depends(current_staff), db: Session = Depends(get_db)):
    result = scan_trip(db, actor, trip_id, data.qr_token, data.event_type); db.commit(); return result
@app.get("/api/trips/{trip_id}/status")
def trip_status(trip_id: int, actor: Staff = Depends(current_staff), db: Session = Depends(get_db)):
    return trip_summary(db, trip_for_org(db, trip_id, actor))

@app.get("/api/trips/{trip_id}/record")
def trip_record(trip_id: int, actor: Staff = Depends(current_staff), db: Session = Depends(get_db)) -> dict:
    """Return the complete, tenant-scoped evidence for one trip."""
    trip = trip_for_org(db, trip_id, actor)
    route = db.query(BusRoute).filter_by(id=trip.route_id, organization_id=actor.organization_id).first() if trip.route_id else None
    vehicle = db.query(Vehicle).filter_by(id=trip.vehicle_id, organization_id=actor.organization_id).first() if trip.vehicle_id else None
    attendance = db.query(TripAttendance, Child).join(Child, Child.id == TripAttendance.child_id).filter(TripAttendance.trip_id == trip.id).order_by(TripAttendance.boarded_at.asc()).all()
    checks = db.query(VehicleSafetyCheck).filter_by(organization_id=actor.organization_id, trip_id=trip.id).order_by(VehicleSafetyCheck.created_at.asc()).all()
    return {
        "trip": trip_summary(db, trip) | {
            "route_name": route.name if route else "便名未設定",
            "vehicle_name": vehicle.name if vehicle else "車両未設定",
            "direction": trip.direction,
            "started_at": trip.started_at,
            "completed_at": trip.completed_at,
        },
        "attendance": [{
            "child_id": child.id, "name": child.name, "class_name": child.class_name,
            "boarded_at": item.boarded_at, "boarded_by": item.boarded_by,
            "alighted_at": item.alighted_at, "alighted_by": item.alighted_by,
        } for item, child in attendance],
        "safety_checks": [{
            "id": item.id, "check_type": item.check_type, "staff_name": item.staff_name,
            "latitude": item.latitude, "longitude": item.longitude, "created_at": item.created_at,
        } for item in checks],
    }

@app.post("/api/trips/{trip_id}/third-party-approval")
def third_party_approval(trip_id: int, data: ThirdApprovalIn, actor: Staff = Depends(current_staff), db: Session = Depends(get_db)):
    trip = trip_for_org(db, trip_id, actor)
    verifier = db.query(Staff).filter_by(id=data.staff_id, organization_id=actor.organization_id, is_active=True).first()
    if not verifier or verifier.role not in {"verifier", "admin"} or not verify_pin(data.pin, verifier.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "第三者確認者の認証に失敗しました")
    driver_names = {row[0] for row in db.query(TripAttendance.boarded_by).filter_by(trip_id=trip.id).all() if row[0]}
    if verifier.name in driver_names:
        raise HTTPException(status.HTTP_409_CONFLICT, "運転担当者本人は第三者確認できません")
    item = VehicleSafetyCheck(organization_id=actor.organization_id, trip_id=trip.id, check_type="third_party", staff_id=verifier.id, staff_name=verifier.name, qr_token="third-party-confirmed")
    db.add(item); db.flush(); audit(db, verifier, "trip.third_party_approval", "trip", trip.id, {"requested_by": actor.id}); db.commit()
    return {"id": item.id, "verifier": verifier.name, "recorded_at": item.created_at}
@app.post("/api/trips/{trip_id}/complete")
def complete_trip(trip_id: int, actor: Staff = Depends(require_roles("operator", "admin")), db: Session = Depends(get_db)):
    trip = trip_for_org(db, trip_id, actor); summary = trip_summary(db, trip)
    if summary["unconfirmed"]: raise HTTPException(status.HTTP_409_CONFLICT, "未降車の園児がいるため完了できません")
    checks = db.query(VehicleSafetyCheck).filter_by(organization_id=actor.organization_id, trip_id=trip.id, check_type="tail_qr").count()
    if not checks: raise HTTPException(status.HTTP_409_CONFLICT, "最後尾確認が必要です")
    approvals = db.query(VehicleSafetyCheck).filter_by(organization_id=actor.organization_id, trip_id=trip.id, check_type="third_party").count()
    if not approvals: raise HTTPException(status.HTTP_409_CONFLICT, "第三者確認が必要です")
    trip.status = "完了"; trip.completed_at = datetime.now(timezone.utc); audit(db, actor, "trip.complete", "trip", trip.id); db.commit(); return {"status": "完了"}

@app.post("/api/vehicle-checks", status_code=status.HTTP_201_CREATED)
def vehicle_check(data: VehicleCheckIn, actor: Staff = Depends(current_staff), db: Session = Depends(get_db)):
    if data.trip_id: trip_for_org(db, data.trip_id, actor)
    item = VehicleSafetyCheck(organization_id=actor.organization_id, staff_id=actor.id, staff_name=actor.name, **data.model_dump()); db.add(item); db.flush(); audit(db, actor, "vehicle_check.create", "vehicle_check", item.id); db.commit(); return {"id": item.id, "recorded_at": item.created_at}

@app.post("/api/notifications", status_code=status.HTTP_201_CREATED)
def queue_notification(data: NotificationIn, actor: Staff = Depends(require_roles("admin", "operator")), db: Session = Depends(get_db)):
    item = NotificationQueue(organization_id=actor.organization_id, **data.model_dump()); db.add(item); db.flush(); audit(db, actor, "notification.queue", "notification", item.id); db.commit(); return {"id": item.id, "status": item.status}
@app.get("/api/notifications")
def list_notifications(actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return db.query(NotificationQueue).filter_by(organization_id=actor.organization_id).order_by(NotificationQueue.created_at.desc()).limit(100).all()
def dispatch_line(item: NotificationQueue) -> str:
    if not LINE_CHANNEL_ACCESS_TOKEN:
        raise RuntimeError("LINE_CHANNEL_ACCESS_TOKEN が未設定です")
    payload = {"to": item.recipient, "messages": [{"type": "text", "text": item.message}]}
    request = UrlRequest(
        "https://api.line.me/v2/bot/message/push",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}", "X-Line-Retry-Key": str(uuid5(NAMESPACE_URL, f"mamoru-notification:{item.id}"))},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        return f"LINE HTTP {response.status}"

@app.post("/api/notifications/{notification_id}/dispatch")
def dispatch_notification(notification_id: int, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    item = db.query(NotificationQueue).filter_by(id=notification_id, organization_id=actor.organization_id).first()
    if not item: raise HTTPException(404, "通知が見つかりません")
    try:
        if item.channel == "line":
            item.provider_response = dispatch_line(item)
        else:
            url = os.getenv("NOTIFICATION_WEBHOOK_URL")
            if not url: raise RuntimeError("NOTIFICATION_WEBHOOK_URL が未設定です")
            request = UrlRequest(url, data=json.dumps({"recipient": item.recipient, "message": item.message, "channel": item.channel}).encode(), headers={"Content-Type": "application/json"}, method="POST")
            with urlopen(request, timeout=10) as response: item.provider_response = f"HTTP {response.status}"
        item.status, item.sent_at = "sent", datetime.now(timezone.utc)
    except (URLError, OSError, RuntimeError) as exc:
        item.status, item.provider_response = "failed", str(exc)[:1000]
    audit(db, actor, "notification.dispatch", "notification", item.id, {"status": item.status, "channel": item.channel}); db.commit(); return {"id": item.id, "status": item.status}

@app.post("/api/integrations/line/webhook", status_code=status.HTTP_200_OK)
async def line_webhook(request: Request, db: Session = Depends(get_db)) -> None:
    if not LINE_CHANNEL_SECRET or not LINE_ORGANIZATION_ID:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "LINE連携が未設定です")
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")
    expected = base64.b64encode(hmac.new(LINE_CHANNEL_SECRET.encode(), body, sha256).digest()).decode()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "LINE署名が不正です")
    for event in json.loads(body.decode("utf-8")).get("events", []):
        user_id = event.get("source", {}).get("userId")
        if not user_id: continue
        contact = db.query(LineContact).filter_by(organization_id=LINE_ORGANIZATION_ID, line_user_id=user_id).first()
        if event.get("type") == "unfollow":
            if contact: contact.is_active = False
            continue
        if not contact:
            db.add(LineContact(organization_id=LINE_ORGANIZATION_ID, line_user_id=user_id))
        else:
            contact.is_active = True
    db.commit()

@app.get("/api/integrations/line/contacts")
def list_line_contacts(actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return db.query(LineContact).filter_by(organization_id=actor.organization_id, is_active=True).order_by(LineContact.created_at.desc()).all()
@app.get("/api/audit-logs")
def audit_logs(action: str | None = None, resource_type: str | None = None, resource_id: str | None = None, query_text: str | None = None, from_at: datetime | None = None, to_at: datetime | None = None, limit: int = 100, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    query = db.query(AuditLog).filter_by(organization_id=actor.organization_id)
    if action: query = query.filter(AuditLog.action == action)
    if resource_type: query = query.filter(AuditLog.resource_type == resource_type)
    if resource_id: query = query.filter(AuditLog.resource_id == resource_id)
    if from_at: query = query.filter(AuditLog.created_at >= from_at)
    if to_at: query = query.filter(AuditLog.created_at <= to_at)
    if query_text:
        escaped = query_text.strip().replace("%", "\\%").replace("_", "\\_")
        if escaped:
            term = f"%{escaped}%"
            query = query.filter(or_(AuditLog.action.ilike(term), AuditLog.resource_type.ilike(term), AuditLog.resource_id.ilike(term), AuditLog.detail.ilike(term)))
    return query.order_by(AuditLog.created_at.desc()).limit(min(limit, 500)).all()

@app.post("/api/sync")
def sync(data: SyncIn, actor: Staff = Depends(current_staff), db: Session = Depends(get_db)):
    results = []
    for event in data.events:
        prior = db.query(SyncEvent).filter_by(organization_id=actor.organization_id, client_event_id=event.client_event_id).first()
        if prior:
            results.append({"client_event_id": event.client_event_id, "outcome": "already_processed"}); continue
        try:
            scan_trip(db, actor, event.trip_id, event.qr_token, event.event_type)
            outcome = "applied"
        except HTTPException as exc:
            outcome = f"rejected:{exc.detail}"
        db.add(SyncEvent(organization_id=actor.organization_id, client_event_id=event.client_event_id, outcome=outcome)); results.append({"client_event_id": event.client_event_id, "outcome": outcome})
    db.commit(); return {"results": results}

@app.post("/api/trips/{trip_id}/videos", status_code=status.HTTP_201_CREATED)
async def upload_video(trip_id: int, file: UploadFile = File(...), actor: Staff = Depends(current_staff), db: Session = Depends(get_db)):
    trip_for_org(db, trip_id, actor)
    if not (file.content_type or "").startswith("video/"): raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "動画ファイルを指定してください")
    suffix = Path(file.filename or "video.mp4").suffix[:10] or ".mp4"
    key = f"{actor.organization_id}/{uuid4()}{suffix}"
    target = UPLOAD_DIR / key; target.parent.mkdir(parents=True, exist_ok=True)
    size = 0
    with target.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > 100 * 1024 * 1024: out.close(); target.unlink(missing_ok=True); raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "動画は100MB以下にしてください")
            out.write(chunk)
    item = VideoEvidence(organization_id=actor.organization_id, trip_id=trip_id, uploaded_by=actor.id, file_name=file.filename or "video", storage_key=key, content_type=file.content_type or "video/mp4")
    db.add(item); db.flush(); audit(db, actor, "video.upload", "video", item.id, {"size": size}); db.commit(); return {"id": item.id, "ai_status": item.ai_status}

@app.post("/api/videos/{video_id}/analyze")
def analyze_video(video_id: int, actor: Staff = Depends(require_roles("admin", "verifier")), db: Session = Depends(get_db)):
    item = db.query(VideoEvidence).filter_by(id=video_id, organization_id=actor.organization_id).first()
    if not item: raise HTTPException(404, "動画が見つかりません")
    item.ai_status, item.ai_result = "pending_provider", "AIプロバイダー未接続: 人による目視確認が必要です"
    audit(db, actor, "video.analyze.request", "video", item.id); db.commit(); return {"id": item.id, "ai_status": item.ai_status, "ai_result": item.ai_result}