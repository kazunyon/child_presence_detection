"""MAMORU BUS API — tenant-scoped safety record backend."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import pbkdf2_hmac, sha256
from io import BytesIO
import base64
import hmac
import json
import os
from pathlib import Path
import secrets
from typing import Generator, Literal
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request as UrlRequest, urlopen
from uuid import NAMESPACE_URL, uuid4, uuid5

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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
JST = timezone(timedelta(hours=9), name="JST")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads")).resolve()
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_ORGANIZATION_ID = int(os.getenv("LINE_ORGANIZATION_ID", "0"))
LINE_BASIC_ID = os.getenv("LINE_BASIC_ID", "@408mrkbk")
LINE_OFFICIAL_ACCOUNT_NAME = os.getenv("LINE_OFFICIAL_ACCOUNT_NAME", "バナナ幼稚園")
LINE_LINK_TOKEN_PEPPER = os.getenv("LINE_LINK_TOKEN_PEPPER", JWT_SECRET)
LINE_LINK_EXPIRE_HOURS = int(os.getenv("LINE_LINK_EXPIRE_HOURS", "24"))
EMAIL_WEBHOOK_URL = os.getenv("EMAIL_WEBHOOK_URL") or os.getenv("NOTIFICATION_WEBHOOK_URL")
EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS")
NOTIFICATION_FEATURE_ENABLED = os.getenv("NOTIFICATION_FEATURE_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
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
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class BusRoute(Base):
    __tablename__ = "bus_routes"
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    direction: Mapped[str] = mapped_column(String(20), default="往路")
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Child(Base):
    __tablename__ = "children"
    __table_args__ = (UniqueConstraint("organization_id", "qr_token", name="uq_child_org_qr"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    class_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    qr_token: Mapped[str] = mapped_column(String(100))


class RouteChild(Base):
    """The normal passenger roster for one bus/route."""
    __tablename__ = "route_children"
    __table_args__ = (UniqueConstraint("route_id", "child_id", name="uq_route_child"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("bus_routes.id"), index=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id"), index=True)


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


class GuardianContact(Base):
    __tablename__ = "guardian_contacts"
    __table_args__ = (UniqueConstraint("organization_id", "email_normalized", name="uq_guardian_contact_org_email"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str] = mapped_column(String(254))
    email_normalized: Mapped[str] = mapped_column(String(254))
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    line_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    line_status: Mapped[str] = mapped_column(String(30), default="not_requested")
    consented_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    consented_by: Mapped[int | None] = mapped_column(ForeignKey("staff.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ChildGuardian(Base):
    __tablename__ = "child_guardians"
    __table_args__ = (UniqueConstraint("organization_id", "child_id", "guardian_contact_id", name="uq_child_guardian"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id"), index=True)
    guardian_contact_id: Mapped[int] = mapped_column(ForeignKey("guardian_contacts.id"), index=True)
    relationship: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notify_alighted: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class LineLinkRequest(Base):
    __tablename__ = "line_link_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    guardian_contact_id: Mapped[int] = mapped_column(ForeignKey("guardian_contacts.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    requested_by: Mapped[int] = mapped_column(ForeignKey("staff.id"))
    email_notification_id: Mapped[int | None] = mapped_column(ForeignKey("notification_queue.id"), nullable=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class NotificationQueue(Base):
    __tablename__ = "notification_queue"
    __table_args__ = (UniqueConstraint("event_key", "guardian_contact_id", "channel", name="uq_notification_event_guardian_channel"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    guardian_contact_id: Mapped[int | None] = mapped_column(ForeignKey("guardian_contacts.id"), nullable=True, index=True)
    child_id: Mapped[int | None] = mapped_column(ForeignKey("children.id"), nullable=True, index=True)
    recipient_type: Mapped[str] = mapped_column(String(30))
    recipient: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(String(500))
    channel: Mapped[str] = mapped_column(String(30), default="webhook")
    event_key: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    template_key: Mapped[str | None] = mapped_column(String(60), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="queued")
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(60), nullable=True)
    provider_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class LineContact(Base):
    __tablename__ = "line_contacts"
    __table_args__ = (UniqueConstraint("organization_id", "line_user_id", name="uq_line_contact_org_user"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    guardian_contact_id: Mapped[int | None] = mapped_column(ForeignKey("guardian_contacts.id"), nullable=True, index=True)
    line_user_id: Mapped[str] = mapped_column(String(100))
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_webhook_event_id: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    last_event_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
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
    child_ids: list[int] = Field(default_factory=list)
class RouteRosterUpdate(BaseModel):
    child_ids: list[int] = Field(default_factory=list)

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
    child_ids: list[int] | None = None
class TripCreate(BaseModel):
    route_id: int | None = None
    vehicle_id: int | None = None
    direction: str = "帰り"
class TripScanIn(BaseModel):
    qr_token: str
    event_type: Literal["乗車", "降車"]
class ManualAttendanceIn(BaseModel):
    child_id: int
    event_type: Literal['乗車', '降車']
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
class GuardianContactIn(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    email_enabled: bool = True
    line_enabled: bool = False
    consent: bool = False
    child_ids: list[int] = Field(default_factory=list)
    relationship: str | None = Field(default=None, max_length=50)
    notify_alighted: bool = True

class GuardianContactUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, min_length=3, max_length=254)
    email_enabled: bool | None = None
    line_enabled: bool | None = None
    consent: bool | None = None
    child_ids: list[int] | None = None
    relationship: str | None = Field(default=None, max_length=50)
    notify_alighted: bool | None = None
    is_active: bool | None = None

class NotificationEventIn(BaseModel):
    trip_id: int
    child_id: int
    event_type: Literal["child.alighted"] = "child.alighted"
    occurred_at: datetime | None = None
class ThirdApprovalIn(BaseModel):
    staff_id: int
    pin: str = Field(min_length=4, max_length=128)

class AdminPinRecoveryIn(BaseModel):
    # Emergency recovery is deliberately limited to the documented admin account.
    staff_id: Literal[3] = 3
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


def audit(db: Session, actor: Staff | None, action: str, resource_type: str, resource_id: int | str, detail: dict | None = None, organization_id: int | None = None) -> None:
    db.add(AuditLog(organization_id=actor.organization_id if actor else int(organization_id or 0), actor_id=actor.id if actor else None, action=action, resource_type=resource_type, resource_id=str(resource_id), detail=json.dumps(detail or {}, ensure_ascii=False)))


def utc_now() -> datetime:
    """Return naive UTC for the existing timezone-neutral DateTime columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def normalize_email(value: str) -> str:
    normalized = value.strip().lower()
    local, separator, domain = normalized.rpartition("@")
    if not separator or not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "メールアドレスの形式を確認してください")
    return normalized


def line_link_token_hash(raw_token: str) -> str:
    return sha256(f"{raw_token}:{LINE_LINK_TOKEN_PEPPER}".encode()).hexdigest()


def line_talk_url(raw_token: str) -> str:
    basic_id = LINE_BASIC_ID if LINE_BASIC_ID.startswith("@") else f"@{LINE_BASIC_ID}"
    return f"https://line.me/R/oaMessage/{basic_id}/?{quote(f'連携 {raw_token}', safe='')}"


def qr_png_data_url(value: str) -> str:
    try:
        import qrcode
    except ImportError as exc:
        raise RuntimeError("QR生成ライブラリが未導入です") from exc
    image = qrcode.make(value)
    output = BytesIO()
    image.save(output, format="PNG")
    return "data:image/png;base64," + base64.b64encode(output.getvalue()).decode()


def guardian_public(db: Session, item: GuardianContact) -> dict:
    links = db.query(ChildGuardian, Child).join(Child, Child.id == ChildGuardian.child_id).filter(
        ChildGuardian.guardian_contact_id == item.id,
        ChildGuardian.organization_id == item.organization_id,
    ).order_by(Child.name).all()
    line_contact = db.query(LineContact).filter_by(
        organization_id=item.organization_id,
        guardian_contact_id=item.id,
        is_active=True,
    ).first()
    return {
        "id": item.id,
        "name": item.name,
        "email": item.email,
        "email_enabled": item.email_enabled,
        "line_enabled": item.line_enabled,
        "line_status": item.line_status,
        "consented_at": item.consented_at,
        "is_active": item.is_active,
        "children": [{
            "id": child.id,
            "name": child.name,
            "relationship": link.relationship,
            "notify_alighted": link.notify_alighted,
        } for link, child in links],
        "line_contact_active": bool(line_contact),
    }


def replace_guardian_children(db: Session, actor: Staff, guardian: GuardianContact, child_ids: list[int], relationship: str | None, notify_alighted: bool) -> None:
    wanted = list(dict.fromkeys(child_ids))
    valid = {child.id for child in db.query(Child).filter(
        Child.organization_id == actor.organization_id,
        Child.id.in_(wanted),
    ).all()} if wanted else set()
    if valid != set(wanted):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "園児が見つかりません")
    db.query(ChildGuardian).filter_by(
        organization_id=actor.organization_id,
        guardian_contact_id=guardian.id,
    ).delete()
    db.add_all([
        ChildGuardian(
            organization_id=actor.organization_id,
            child_id=child_id,
            guardian_contact_id=guardian.id,
            relationship=relationship,
            notify_alighted=notify_alighted,
        ) for child_id in wanted
    ])


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


def route_children(db: Session, route_id: int) -> list[Child]:
    return db.query(Child).join(RouteChild, RouteChild.child_id == Child.id).filter(RouteChild.route_id == route_id).order_by(Child.name).all()


def route_public(db: Session, route: BusRoute) -> dict:
    return {"id": route.id, "name": route.name, "direction": route.direction, "vehicle_id": route.vehicle_id,
            "children": [{"id": child.id, "name": child.name, "class_name": child.class_name} for child in route_children(db, route.id)]}


def validate_video_duration(duration_seconds: int | None) -> None:
    if duration_seconds is not None and not 5 <= duration_seconds <= 30:
        raise HTTPException(422, "車内動画は5秒以上30秒以内で撮影してください")


def replace_route_roster(db: Session, actor: Staff, route: BusRoute, child_ids: list[int]) -> None:
    wanted = list(dict.fromkeys(child_ids))
    valid = {child.id for child in db.query(Child).filter(Child.organization_id == actor.organization_id, Child.id.in_(wanted)).all()} if wanted else set()
    if valid != set(wanted):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "園児が見つかりません")
    db.query(RouteChild).filter_by(route_id=route.id).delete()
    db.add_all([RouteChild(route_id=route.id, child_id=child_id) for child_id in wanted])


def scan_trip(db: Session, actor: Staff, trip_id: int, qr_token: str, event_type: str) -> dict:
    trip = trip_for_org(db, trip_id, actor)
    if trip.status != "運行中":
        raise HTTPException(status.HTTP_409_CONFLICT, "この送迎は完了しています")
    child = db.query(Child).filter_by(organization_id=actor.organization_id, qr_token=qr_token).first()
    if not child:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "QRコードが登録されていません")
    attendance = db.query(TripAttendance).filter_by(trip_id=trip.id, child_id=child.id).first()
    if not attendance:
        raise HTTPException(status.HTTP_409_CONFLICT, "この園児は通常名簿にいません。当日の園児変更で追加してください")
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
    if event_type == "降車":
        queue_alighted_notifications(db, actor.organization_id, trip.id, child, now, actor)
    return {"child": child.name, "event_type": event_type, "trip_id": trip.id}


def trip_summary(db: Session, trip: BusTrip) -> dict:
    route = db.query(BusRoute).filter_by(id=trip.route_id, organization_id=trip.organization_id).first() if trip.route_id else None
    vehicle = db.query(Vehicle).filter_by(id=trip.vehicle_id, organization_id=trip.organization_id).first() if trip.vehicle_id else None
    rows = db.query(TripAttendance, Child).join(Child, Child.id == TripAttendance.child_id).filter(TripAttendance.trip_id == trip.id).all()
    children = [{"child_id": c.id, "name": c.name, "boarded_at": a.boarded_at, "alighted_at": a.alighted_at, "boarded_manually": bool(a.boarded_by and "（QRなし）" in a.boarded_by), "alighted_manually": bool(a.alighted_by and "（QRなし）" in a.alighted_by)} for a, c in rows]
    boarded = sum(x["boarded_at"] is not None for x in children)
    alighted = sum(x["alighted_at"] is not None for x in children)
    check_types = {row[0] for row in db.query(VehicleSafetyCheck.check_type).filter_by(organization_id=trip.organization_id, trip_id=trip.id).all()}
    videos = db.query(VideoEvidence).filter_by(organization_id=trip.organization_id, trip_id=trip.id).order_by(VideoEvidence.created_at.desc()).all()
    latest_video = videos[0] if videos else None
    return {
        "trip_id": trip.id,
        "status": trip.status,
        "direction": trip.direction,
        "route_name": route.name if route else "バス名未設定",
        "vehicle_name": vehicle.name if vehicle else "号車未設定",
        "boarded": boarded,
        "alighted": alighted,
        "unconfirmed": boarded - alighted,
        "tail_confirmed": "tail_qr" in check_types,
        "third_party_confirmed": "third_party" in check_types,
        "video_evidence_count": len(videos),
        "latest_video_id": latest_video.id if latest_video else None,
        "latest_video_ai_status": latest_video.ai_status if latest_video else None,
        "latest_video_ai_result": latest_video.ai_result if latest_video else None,
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
    route = BusRoute(organization_id=org.id, name="ひまわり園 送迎便", direction="帰り", vehicle_id=vehicle.id)
    db.add(route); db.flush()
    db.add_all([RouteChild(route_id=route.id, child_id=child.id) for child in db.query(Child).filter_by(organization_id=org.id).all()])
    db.commit()


def migrate_legacy_database() -> None:
    """Upgrade the original single-kindergarten schema without deleting its records."""
    legacy_columns = {
        "staff": {"organization_id": "INTEGER", "password_hash": "VARCHAR(256)", "is_active": "BOOLEAN DEFAULT TRUE"},
        "vehicles": {"organization_id": "INTEGER", "is_active": "BOOLEAN DEFAULT TRUE"},
        "bus_routes": {"organization_id": "INTEGER", "is_active": "BOOLEAN DEFAULT TRUE"},
        "children": {"organization_id": "INTEGER"},
        "bus_trips": {"organization_id": "INTEGER"},
        "vehicle_safety_checks": {"organization_id": "INTEGER", "trip_id": "INTEGER"},
        "notification_queue": {
            "organization_id": "INTEGER", "guardian_contact_id": "INTEGER", "child_id": "INTEGER",
            "channel": "VARCHAR(30) DEFAULT 'webhook'", "event_key": "VARCHAR(160)",
            "template_key": "VARCHAR(60)", "subject": "VARCHAR(200)", "attempt_count": "INTEGER DEFAULT 0",
            "next_attempt_at": "TIMESTAMP", "provider_message_id": "VARCHAR(200)", "error_code": "VARCHAR(60)",
            "provider_response": "TEXT", "sent_at": "TIMESTAMP",
        },
        "line_contacts": {
            "guardian_contact_id": "INTEGER", "last_webhook_event_id": "VARCHAR(160)", "last_event_at": "TIMESTAMP",
        },
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
        if "notification_queue" in tables:
            connection.execute(text("UPDATE notification_queue SET attempt_count = 0 WHERE attempt_count IS NULL"))

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
        # Existing installations had no per-bus roster. Initialise each such bus
        # with the organisation's current children once; later edits are explicit.
        for route in db.query(BusRoute).all():
            if not db.query(RouteChild).filter_by(route_id=route.id).first():
                db.add_all([RouteChild(route_id=route.id, child_id=child.id) for child in db.query(Child).filter_by(organization_id=route.organization_id).all()])
                changed = True
        if changed:
            db.commit()
app = FastAPI(title="まもるバス API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174").split(","), allow_methods=["*"], allow_headers=["*"], allow_credentials=True)

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
    if not staff:
        # Older production databases can contain the two operating accounts
        # but lack the originally documented ID 3 administrator. A valid
        # one-time recovery token authorizes restoring only that fixed account.
        organization = db.query(Organization).order_by(Organization.id).first()
        if not organization:
            raise HTTPException(status.HTTP_409_CONFLICT, "復旧先の園情報が見つかりません")
        # Legacy Render staff tables can retain a required pin column.
        # Use it only when it exists; authentication uses password_hash.
        password_hash = hash_pin(data.new_pin)
        legacy_columns = {column["name"] for column in inspect(engine).get_columns("staff")}
        legacy_pin_column = next((name for name in ("pin_hash", "pin") if name in legacy_columns), None)
        if legacy_pin_column:
            db.execute(text(f"INSERT INTO staff (id, organization_id, name, role, password_hash, is_active, {legacy_pin_column}) VALUES (:id, :organization_id, :name, :role, :password_hash, :is_active, :legacy_pin)"), {"id": 3, "organization_id": organization.id, "name": "管理者", "role": "admin", "password_hash": password_hash, "is_active": True, "legacy_pin": sha256(data.new_pin.encode()).hexdigest()})
            staff = db.get(Staff, 3)
        else:
            staff = Staff(id=3, organization_id=organization.id, name="管理者", role="admin", password_hash=password_hash, is_active=True)
            db.add(staff)
            db.flush()
    else:
        staff.role = "admin"
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
    now_jst = datetime.now(JST)
    day_start_jst = now_jst.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end_jst = day_start_jst + timedelta(days=1)
    # Datetimes are stored as UTC in the database.  Convert the JST calendar-day
    # boundaries to naive UTC because the existing DateTime columns are timezone
    # neutral in both SQLite and PostgreSQL.
    day_start_utc = day_start_jst.astimezone(timezone.utc).replace(tzinfo=None)
    day_end_utc = day_end_jst.astimezone(timezone.utc).replace(tzinfo=None)
    trips = db.query(BusTrip).filter(
        BusTrip.organization_id == actor.organization_id,
        BusTrip.started_at >= day_start_utc,
        BusTrip.started_at < day_end_utc,
        BusTrip.status != "中止",
    ).order_by(BusTrip.started_at.desc()).all()
    summaries = [trip_summary(db, trip) for trip in trips]
    return {
        "organization_name": organization.name if organization else "園",
        "date": day_start_jst.date().isoformat(),
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
    vehicles = db.query(Vehicle).filter_by(organization_id=oid, is_active=True).order_by(Vehicle.name).all()
    routes = db.query(BusRoute).filter_by(organization_id=oid, is_active=True).order_by(BusRoute.name).all()
    return {
        "children": [{"id": item.id, "name": item.name, "class_name": item.class_name, "qr_token": item.qr_token} for item in children],
        "staff": [{"id": item.id, "name": item.name, "role": item.role, "is_active": item.is_active} for item in staff],
        "vehicles": [{"id": item.id, "name": item.name, "plate_number": item.plate_number} for item in vehicles],
        "routes": [route_public(db, item) for item in routes],
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
    return db.query(Vehicle).filter_by(organization_id=actor.organization_id, is_active=True).order_by(Vehicle.name).all()
@app.post("/api/vehicles", status_code=status.HTTP_201_CREATED)
def create_vehicle(data: VehicleCreate, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    inactive = db.query(Vehicle).filter_by(
        organization_id=actor.organization_id,
        name=data.name,
        is_active=False,
    ).first()
    if inactive:
        inactive.plate_number = data.plate_number
        inactive.is_active = True
        audit(db, actor, "vehicle.restore", "vehicle", inactive.id)
        db.commit()
        db.refresh(inactive)
        return inactive
    item = Vehicle(organization_id=actor.organization_id, **data.model_dump()); db.add(item); db.flush(); audit(db, actor, "vehicle.create", "vehicle", item.id); db.commit(); return item
@app.put("/api/vehicles/{vehicle_id}")
def update_vehicle(vehicle_id: int, data: VehicleUpdate, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    item = db.query(Vehicle).filter_by(id=vehicle_id, organization_id=actor.organization_id, is_active=True).first()
    if not item: raise HTTPException(status.HTTP_404_NOT_FOUND, "車両が見つかりません")
    values=data.model_dump(exclude_unset=True)
    for key, value in values.items(): setattr(item, key, value)
    audit(db, actor, "vehicle.update", "vehicle", item.id, values); db.commit(); return item
@app.delete("/api/vehicles/{vehicle_id}")
def delete_vehicle(vehicle_id: int, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    """Hide a vehicle from master data while preserving historical trip evidence."""
    item = db.query(Vehicle).filter_by(
        id=vehicle_id,
        organization_id=actor.organization_id,
        is_active=True,
    ).first()
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "車両が見つかりません")
    routes = db.query(BusRoute).filter_by(
        organization_id=actor.organization_id,
        vehicle_id=item.id,
    ).all()
    for route in routes:
        route.vehicle_id = None
    item.is_active = False
    audit(db, actor, "vehicle.delete", "vehicle", item.id, {
        "name": item.name,
        "detached_route_ids": [route.id for route in routes],
    })
    db.commit()
    return {"status": "deleted", "detached_route_count": len(routes)}

@app.get("/api/bus-routes")
@app.get("/api/routes")
def list_routes(actor: Staff = Depends(current_staff), db: Session = Depends(get_db)):
    return [route_public(db, item) for item in db.query(BusRoute).filter_by(organization_id=actor.organization_id, is_active=True).order_by(BusRoute.name).all()]
@app.post("/api/bus-routes", status_code=status.HTTP_201_CREATED)
@app.post("/api/routes", status_code=status.HTTP_201_CREATED)
def create_route(data: RouteCreate, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    if data.vehicle_id and not db.query(Vehicle).filter_by(id=data.vehicle_id, organization_id=actor.organization_id, is_active=True).first(): raise HTTPException(status.HTTP_404_NOT_FOUND, "車両が見つかりません")
    values = data.model_dump(exclude={"child_ids"})
    item = BusRoute(organization_id=actor.organization_id, **values); db.add(item); db.flush()
    replace_route_roster(db, actor, item, data.child_ids)
    audit(db, actor, "route.create", "route", item.id, {"child_ids": data.child_ids}); db.commit(); return route_public(db, item)
@app.put("/api/bus-routes/{route_id}")
@app.put("/api/routes/{route_id}")
def update_route(route_id: int, data: RouteUpdate, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    item = db.query(BusRoute).filter_by(id=route_id, organization_id=actor.organization_id, is_active=True).first()
    if not item: raise HTTPException(status.HTTP_404_NOT_FOUND, "バスが見つかりません")
    values=data.model_dump(exclude_unset=True)
    if values.get("vehicle_id") and not db.query(Vehicle).filter_by(id=values["vehicle_id"], organization_id=actor.organization_id, is_active=True).first(): raise HTTPException(status.HTTP_404_NOT_FOUND, "車両が見つかりません")
    child_ids = values.pop("child_ids", None)
    for key, value in values.items(): setattr(item, key, value)
    if child_ids is not None: replace_route_roster(db, actor, item, child_ids)
    audit(db, actor, "route.update", "route", item.id, values | ({"child_ids": child_ids} if child_ids is not None else {})); db.commit(); return route_public(db, item)
@app.delete("/api/bus-routes/{route_id}")
@app.delete("/api/routes/{route_id}")
def delete_route(route_id: int, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    """Hide a route from master data while preserving historical trip evidence."""
    item = db.query(BusRoute).filter_by(
        id=route_id,
        organization_id=actor.organization_id,
        is_active=True,
    ).first()
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "便が見つかりません")
    roster_count = db.query(RouteChild).filter_by(route_id=item.id).delete()
    item.is_active = False
    audit(db, actor, "route.delete", "route", item.id, {
        "name": item.name,
        "direction": item.direction,
        "removed_roster_count": roster_count,
    })
    db.commit()
    return {"status": "deleted", "removed_roster_count": roster_count}

@app.post("/api/trips", status_code=status.HTTP_201_CREATED)
def create_trip(data: TripCreate, actor: Staff = Depends(current_staff), db: Session = Depends(get_db)):
    route = db.query(BusRoute).filter_by(id=data.route_id, organization_id=actor.organization_id, is_active=True).first() if data.route_id else None
    if data.route_id and not route: raise HTTPException(404, "バスが見つかりません")
    if data.vehicle_id and not db.query(Vehicle).filter_by(id=data.vehicle_id, organization_id=actor.organization_id, is_active=True).first(): raise HTTPException(404, "車両が見つかりません")
    trip = BusTrip(organization_id=actor.organization_id, **data.model_dump()); db.add(trip); db.flush()
    if route:
        # On the return leg, the usual roster is expected to be on board. A child
        # who is absent must be removed explicitly via the daily exception screen.
        expected_boarded_at = trip.started_at if data.direction == "帰り" else None
        db.add_all([TripAttendance(trip_id=trip.id, child_id=child.id, boarded_at=expected_boarded_at, boarded_by="通常名簿" if expected_boarded_at else None) for child in route_children(db, route.id)])
    audit(db, actor, "trip.create", "trip", trip.id, {"route_id": data.route_id}); db.commit(); db.refresh(trip); return trip

@app.put("/api/trips/{trip_id}/roster")
def update_trip_roster(trip_id: int, data: RouteRosterUpdate, actor: Staff = Depends(require_roles("operator", "admin")), db: Session = Depends(get_db)):
    trip = trip_for_org(db, trip_id, actor)
    if trip.status != "運行中": raise HTTPException(status.HTTP_409_CONFLICT, "完了した送迎の名簿は変更できません")
    wanted = list(dict.fromkeys(data.child_ids))
    valid = {child.id for child in db.query(Child).filter(Child.organization_id == actor.organization_id, Child.id.in_(wanted)).all()} if wanted else set()
    if valid != set(wanted): raise HTTPException(status.HTTP_404_NOT_FOUND, "園児が見つかりません")
    current = {row.child_id: row for row in db.query(TripAttendance).filter_by(trip_id=trip.id).all()}
    changed = set(current) ^ set(wanted)
    if any(current[child_id].boarded_at or current[child_id].alighted_at for child_id in changed if child_id in current):
        raise HTTPException(status.HTTP_409_CONFLICT, "確認済みの園児は名簿から外せません")
    for child_id in set(current) - set(wanted): db.delete(current[child_id])
    db.add_all([TripAttendance(trip_id=trip.id, child_id=child_id) for child_id in set(wanted) - set(current)])
    audit(db, actor, "trip.roster.update", "trip", trip.id, {"child_ids": wanted}); db.commit()
    return trip_summary(db, trip)

@app.get("/api/trips")
def list_trips(from_at: datetime | None = None, to_at: datetime | None = None, status_filter: str | None = None, actor: Staff = Depends(current_staff), db: Session = Depends(get_db)):
    query = db.query(BusTrip).filter(
        BusTrip.organization_id == actor.organization_id,
        BusTrip.status != "中止",
    )
    if from_at: query = query.filter(BusTrip.started_at >= from_at)
    if to_at: query = query.filter(BusTrip.started_at <= to_at)
    if status_filter: query = query.filter(BusTrip.status == status_filter)
    return [trip_summary(db, trip) | {"started_at": trip.started_at, "completed_at": trip.completed_at} for trip in query.order_by(BusTrip.started_at.desc()).limit(200)]

@app.post("/api/trips/{trip_id}/scans")
def trip_scan(trip_id: int, data: TripScanIn, actor: Staff = Depends(current_staff), db: Session = Depends(get_db)):
    result = scan_trip(db, actor, trip_id, data.qr_token, data.event_type); db.commit(); return result
@app.post("/api/trips/{trip_id}/manual-attendance")
def manual_trip_attendance(trip_id: int, data: ManualAttendanceIn, actor: Staff = Depends(require_roles("operator", "admin")), db: Session = Depends(get_db)):
    """Record a witnessed boarding/alighting when the child's QR code is unavailable."""
    trip = trip_for_org(db, trip_id, actor)
    if trip.status != "運行中":
        raise HTTPException(status.HTTP_409_CONFLICT, "この送迎は完了しています")
    attendance = db.query(TripAttendance).filter_by(trip_id=trip.id, child_id=data.child_id).first()
    child = db.query(Child).filter_by(id=data.child_id, organization_id=actor.organization_id).first()
    if not attendance or not child:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "この園児は当日の名簿にいません")
    now = datetime.now(timezone.utc)
    if data.event_type == "乗車":
        if attendance.boarded_at:
            raise HTTPException(status.HTTP_409_CONFLICT, "この園児はすでに乗車済みです")
        attendance.boarded_at, attendance.boarded_by = now, f"{actor.name}（QRなし）"
    else:
        if not attendance.boarded_at:
            raise HTTPException(status.HTTP_409_CONFLICT, "乗車記録がないため降車できません")
        if attendance.alighted_at:
            raise HTTPException(status.HTTP_409_CONFLICT, "この園児はすでに降車済みです")
        attendance.alighted_at, attendance.alighted_by = now, f"{actor.name}（QRなし）"
    audit(db, actor, f"trip.manual_{data.event_type}", "trip", trip.id, {"child_id": child.id, "child_name": child.name, "reason": "qr_unavailable"})
    if data.event_type == "降車":
        queue_alighted_notifications(db, actor.organization_id, trip.id, child, now, actor)
    db.commit()
    return trip_summary(db, trip)
@app.post("/api/trips/{trip_id}/cancel")
def cancel_unstarted_trip(trip_id: int, actor: Staff = Depends(require_roles("operator", "admin")), db: Session = Depends(get_db)):
    """Cancel a mistakenly selected route only before any actual safety record exists."""
    trip = trip_for_org(db, trip_id, actor)
    if trip.status != "運行中":
        raise HTTPException(status.HTTP_409_CONFLICT, "この送迎は運行中ではありません")
    attendance = db.query(TripAttendance).filter_by(trip_id=trip.id).all()
    has_actual_attendance = any(
        item.alighted_at or (item.boarded_by and item.boarded_by != "通常名簿")
        for item in attendance
    )
    has_safety_checks = db.query(VehicleSafetyCheck).filter_by(organization_id=actor.organization_id, trip_id=trip.id).count() > 0
    if has_actual_attendance or has_safety_checks:
        raise HTTPException(status.HTTP_409_CONFLICT, "乗降または安全確認を記録した送迎は中止できません。送迎を再開して完了してください")
    trip.status = "中止"
    trip.completed_at = datetime.now(timezone.utc)
    audit(db, actor, "trip.cancel", "trip", trip.id, {"reason": "vehicle_reselection"})
    db.commit()
    return {"status": "中止"}
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
    videos = db.query(VideoEvidence).filter_by(organization_id=actor.organization_id, trip_id=trip.id).order_by(VideoEvidence.created_at.asc()).all()
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
        "videos": [{
            "id": item.id, "file_name": item.file_name,
            "storage_key": item.storage_key,
            "storage_path": str(UPLOAD_DIR / item.storage_key),
            "content_type": item.content_type,
            "ai_status": item.ai_status,
            "ai_result": item.ai_result, "created_at": item.created_at,
        } for item in videos],
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
    videos = db.query(VideoEvidence).filter_by(organization_id=actor.organization_id, trip_id=trip.id).count()
    if not videos: raise HTTPException(status.HTTP_409_CONFLICT, "5秒以上の車内撮影が必要です")
    approvals = db.query(VehicleSafetyCheck).filter_by(organization_id=actor.organization_id, trip_id=trip.id, check_type="third_party").count()
    if not approvals: raise HTTPException(status.HTTP_409_CONFLICT, "第三者確認が必要です")
    trip.status = "完了"; trip.completed_at = datetime.now(timezone.utc); audit(db, actor, "trip.complete", "trip", trip.id); db.commit(); return {"status": "完了"}
@app.post("/api/trips/{trip_id}/force-complete")
def force_complete_trip(trip_id: int, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    """Administratively close a stranded trip while preserving an audit trail."""
    trip = trip_for_org(db, trip_id, actor)
    if trip.status == "完了":
        raise HTTPException(status.HTTP_409_CONFLICT, "この送迎はすでに完了しています")
    summary = trip_summary(db, trip)
    trip.status = "完了"
    trip.completed_at = datetime.now(timezone.utc)
    audit(db, actor, "trip.force_complete", "trip", trip.id, {
        "unconfirmed": summary["unconfirmed"],
        "boarded": summary["boarded"],
        "alighted": summary["alighted"],
    })
    db.commit()
    return {"status": "完了", "forced": True}

@app.post("/api/vehicle-checks", status_code=status.HTTP_201_CREATED)
def vehicle_check(data: VehicleCheckIn, actor: Staff = Depends(current_staff), db: Session = Depends(get_db)):
    if data.trip_id: trip_for_org(db, data.trip_id, actor)
    item = VehicleSafetyCheck(organization_id=actor.organization_id, staff_id=actor.id, staff_name=actor.name, **data.model_dump()); db.add(item); db.flush(); audit(db, actor, "vehicle_check.create", "vehicle_check", item.id); db.commit(); return {"id": item.id, "recorded_at": item.created_at}

def validate_guardian_settings(email: str, email_enabled: bool, line_enabled: bool, consent: bool) -> str:
    normalized = normalize_email(email)
    if (email_enabled or line_enabled) and not consent:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "通知同意を確認してください")
    if line_enabled and (not normalized or not email_enabled):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "LINE通知を希望する場合はメール通知も有効にしてください")
    return normalized


@app.get("/api/guardian-contacts")
def list_guardian_contacts(actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> list[dict]:
    items = db.query(GuardianContact).filter_by(organization_id=actor.organization_id).order_by(GuardianContact.created_at.desc()).all()
    return [guardian_public(db, item) for item in items]


@app.post("/api/guardian-contacts", status_code=status.HTTP_201_CREATED)
def create_guardian_contact(data: GuardianContactIn, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> dict:
    if not data.child_ids:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "対象園児を1人以上選択してください")
    normalized = validate_guardian_settings(data.email, data.email_enabled, data.line_enabled, data.consent)
    if db.query(GuardianContact).filter_by(organization_id=actor.organization_id, email_normalized=normalized).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "このメールアドレスは登録済みです")
    item = GuardianContact(
        organization_id=actor.organization_id,
        name=data.name.strip() if data.name else None,
        email=data.email.strip(),
        email_normalized=normalized,
        email_enabled=data.email_enabled,
        line_enabled=data.line_enabled,
        line_status="not_requested",
        consented_at=utc_now() if data.consent else None,
        consented_by=actor.id if data.consent else None,
    )
    db.add(item)
    db.flush()
    replace_guardian_children(db, actor, item, data.child_ids, data.relationship, data.notify_alighted)
    audit(db, actor, "guardian_contact.create", "guardian_contact", item.id, {
        "child_ids": data.child_ids, "email_enabled": data.email_enabled,
        "line_enabled": data.line_enabled, "consent": data.consent,
    })
    db.commit()
    return guardian_public(db, item)


@app.put("/api/guardian-contacts/{guardian_id}")
def update_guardian_contact(guardian_id: int, data: GuardianContactUpdate, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> dict:
    item = db.query(GuardianContact).filter_by(id=guardian_id, organization_id=actor.organization_id).first()
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "保護者連絡先が見つかりません")
    values = data.model_dump(exclude_unset=True)
    email = values.get("email", item.email)
    email_enabled = values.get("email_enabled", item.email_enabled)
    line_enabled = values.get("line_enabled", item.line_enabled)
    consent = values.get("consent", item.consented_at is not None)
    if consent:
        normalized = validate_guardian_settings(email, email_enabled, line_enabled, consent)
    else:
        normalized = normalize_email(email)
        email_enabled, line_enabled = False, False
    duplicate = db.query(GuardianContact).filter(
        GuardianContact.organization_id == actor.organization_id,
        GuardianContact.email_normalized == normalized,
        GuardianContact.id != item.id,
    ).first()
    if duplicate:
        raise HTTPException(status.HTTP_409_CONFLICT, "このメールアドレスは登録済みです")
    if "name" in values:
        item.name = values["name"].strip() if values["name"] else None
    if "email" in values:
        item.email, item.email_normalized = email.strip(), normalized
    item.email_enabled, item.line_enabled = email_enabled, line_enabled
    if "is_active" in values:
        item.is_active = values["is_active"]
    if consent:
        if not item.consented_at:
            item.consented_at, item.consented_by = utc_now(), actor.id
    else:
        item.consented_at, item.consented_by = None, None
        item.email_enabled, item.line_enabled = False, False
        item.line_status = "revoked"
        db.query(LineLinkRequest).filter_by(organization_id=actor.organization_id, guardian_contact_id=item.id, status="pending").update({"status": "revoked"})
        db.query(LineContact).filter_by(organization_id=actor.organization_id, guardian_contact_id=item.id).update({"guardian_contact_id": None})
    if values.get("line_enabled") is False and item.line_status == "linked":
        item.line_status = "revoked"
        db.query(LineContact).filter_by(organization_id=actor.organization_id, guardian_contact_id=item.id).update({"guardian_contact_id": None})
    if "child_ids" in values:
        if not values["child_ids"]:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "対象園児を1人以上選択してください")
        replace_guardian_children(
            db, actor, item, values["child_ids"], values.get("relationship"),
            values.get("notify_alighted", True),
        )
    elif "relationship" in values or "notify_alighted" in values:
        links = db.query(ChildGuardian).filter_by(organization_id=actor.organization_id, guardian_contact_id=item.id).all()
        for link in links:
            if "relationship" in values:
                link.relationship = values["relationship"]
            if "notify_alighted" in values:
                link.notify_alighted = values["notify_alighted"]
    item.updated_at = utc_now()
    audit(db, actor, "guardian_contact.update", "guardian_contact", item.id, {
        key: value for key, value in values.items() if key != "email"
    })
    db.commit()
    return guardian_public(db, item)


def dispatch_webhook_payload(item: NotificationQueue, payload_override: dict | None = None) -> tuple[str, str | None]:
    url = EMAIL_WEBHOOK_URL if item.channel == "email" else os.getenv("NOTIFICATION_WEBHOOK_URL")
    if not url:
        setting = "EMAIL_WEBHOOK_URL" if item.channel == "email" else "NOTIFICATION_WEBHOOK_URL"
        raise RuntimeError(f"{setting} が未設定です")
    payload = {
        "recipient": item.recipient, "message": item.message, "channel": item.channel,
        "subject": item.subject, "from": EMAIL_FROM_ADDRESS,
    }
    if payload_override:
        payload.update(payload_override)
    request = UrlRequest(url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=10) as response:
        response_body = response.read(4096).decode("utf-8", errors="replace")
        provider_id = None
        if response_body:
            try:
                parsed = json.loads(response_body)
                provider_id = str(parsed.get("id") or parsed.get("message_id") or "") or None
            except (json.JSONDecodeError, AttributeError):
                pass
        return f"HTTP {response.status}", provider_id


def dispatch_queue_item(item: NotificationQueue, payload_override: dict | None = None) -> str:
    item.attempt_count = int(item.attempt_count or 0) + 1
    item.status = "sending"
    try:
        if item.channel == "line":
            item.provider_response = dispatch_line(item)
        else:
            item.provider_response, item.provider_message_id = dispatch_webhook_payload(item, payload_override)
        item.status, item.sent_at = "sent", utc_now()
        item.error_code, item.next_attempt_at = None, None
    except (URLError, OSError, RuntimeError) as exc:
        item.status, item.provider_response = "failed", str(exc)[:1000]
        item.error_code = "configuration" if isinstance(exc, RuntimeError) else "transport"
        retry_minutes = (1, 5, 30)
        item.next_attempt_at = utc_now() + timedelta(minutes=retry_minutes[min(item.attempt_count - 1, 2)]) if item.attempt_count < 3 else None
    return item.status


def issue_line_link_request_for_guardian(guardian: GuardianContact, actor: Staff, db: Session) -> dict:
    if not guardian.is_active or not guardian.line_enabled:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "LINE通知を有効にしてください")
    if not guardian.consented_at:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "通知同意を確認してください")
    normalize_email(guardian.email)
    db.query(LineLinkRequest).filter_by(
        organization_id=actor.organization_id,
        guardian_contact_id=guardian.id,
        status="pending",
    ).update({"status": "revoked"})
    raw_token = secrets.token_urlsafe(32)
    expires_at = utc_now() + timedelta(hours=LINE_LINK_EXPIRE_HOURS)
    link_request = LineLinkRequest(
        organization_id=actor.organization_id,
        guardian_contact_id=guardian.id,
        token_hash=line_link_token_hash(raw_token),
        expires_at=expires_at,
        requested_by=actor.id,
    )
    db.add(link_request)
    db.flush()
    talk_url = line_talk_url(raw_token)
    qr_data_url = qr_png_data_url(talk_url)
    email_item = NotificationQueue(
        organization_id=actor.organization_id,
        guardian_contact_id=guardian.id,
        recipient_type="guardian",
        recipient=guardian.email,
        message=f"{LINE_OFFICIAL_ACCOUNT_NAME}のLINE通知連携案内を送信しました。期限は{LINE_LINK_EXPIRE_HOURS}時間です。",
        channel="email",
        event_key=f"line-link:{link_request.id}",
        template_key="line.link.v1",
        subject=f"【まもるバス】{LINE_OFFICIAL_ACCOUNT_NAME}のLINE通知連携をお願いします",
    )
    db.add(email_item)
    db.flush()
    link_request.email_notification_id = email_item.id
    guardian.line_status, guardian.updated_at = "pending", utc_now()
    dispatch_queue_item(email_item, {
        "template_key": "line.link.v1",
        "guardian_name": guardian.name or "保護者",
        "official_account_name": LINE_OFFICIAL_ACCOUNT_NAME,
        "line_basic_id": LINE_BASIC_ID,
        "link_url": talk_url,
        "qr_png_data_url": qr_data_url,
        "expires_at": expires_at.isoformat() + "Z",
    })
    audit(db, actor, "line.link.request.issue", "line_link_request", link_request.id, {
        "guardian_contact_id": guardian.id,
        "expires_at": expires_at.isoformat(),
        "email_notification_id": email_item.id,
        "email_status": email_item.status,
    })
    db.commit()
    return {
        "request_id": link_request.id,
        "status": link_request.status,
        "expires_at": expires_at,
        "email_delivery_status": email_item.status,
        "official_account_name": LINE_OFFICIAL_ACCOUNT_NAME,
        "line_basic_id": LINE_BASIC_ID,
        "line_link_url": talk_url,
        "qr_png_data_url": qr_data_url,
    }


@app.post("/api/guardian-contacts/{guardian_id}/line-link-requests", status_code=status.HTTP_202_ACCEPTED)
def issue_line_link_request(guardian_id: int, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> dict:
    guardian = db.query(GuardianContact).filter_by(id=guardian_id, organization_id=actor.organization_id).first()
    if not guardian:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "保護者連絡先が見つかりません")
    return issue_line_link_request_for_guardian(guardian, actor, db)


@app.get("/api/guardian-contacts/{guardian_id}/line-link-status")
def line_link_status(guardian_id: int, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> dict:
    guardian = db.query(GuardianContact).filter_by(id=guardian_id, organization_id=actor.organization_id).first()
    if not guardian:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "保護者連絡先が見つかりません")
    latest = db.query(LineLinkRequest).filter_by(organization_id=actor.organization_id, guardian_contact_id=guardian.id).order_by(LineLinkRequest.created_at.desc()).first()
    return {
        "guardian_contact_id": guardian.id,
        "line_status": guardian.line_status,
        "request_status": latest.status if latest else None,
        "expires_at": latest.expires_at if latest else None,
    }


@app.delete("/api/guardian-contacts/{guardian_id}/line-link")
def unlink_guardian_line(guardian_id: int, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> dict:
    guardian = db.query(GuardianContact).filter_by(id=guardian_id, organization_id=actor.organization_id).first()
    if not guardian:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "保護者連絡先が見つかりません")
    db.query(LineContact).filter_by(organization_id=actor.organization_id, guardian_contact_id=guardian.id).update({"guardian_contact_id": None})
    db.query(LineLinkRequest).filter_by(organization_id=actor.organization_id, guardian_contact_id=guardian.id, status="pending").update({"status": "revoked"})
    guardian.line_status, guardian.updated_at = "revoked", utc_now()
    audit(db, actor, "line.contact.unlink", "guardian_contact", guardian.id)
    db.commit()
    return {"guardian_contact_id": guardian.id, "line_status": guardian.line_status}

@app.post("/api/notifications", status_code=status.HTTP_201_CREATED)
def queue_notification(data: NotificationIn, actor: Staff = Depends(require_roles("admin", "operator")), db: Session = Depends(get_db)):
    item = NotificationQueue(organization_id=actor.organization_id, **data.model_dump())
    db.add(item); db.flush(); audit(db, actor, "notification.queue", "notification", item.id); db.commit()
    return {"id": item.id, "status": item.status}


def notification_public(db: Session, item: NotificationQueue) -> dict:
    guardian = db.get(GuardianContact, item.guardian_contact_id) if item.guardian_contact_id else None
    return {
        "id": item.id, "guardian_contact_id": item.guardian_contact_id,
        "guardian_name": guardian.name if guardian else None,
        "child_id": item.child_id, "recipient": item.recipient,
        "message": item.message, "subject": item.subject, "channel": item.channel,
        "event_key": item.event_key, "template_key": item.template_key,
        "status": item.status, "attempt_count": item.attempt_count,
        "next_attempt_at": item.next_attempt_at, "provider_response": item.provider_response,
        "error_code": item.error_code, "created_at": item.created_at, "sent_at": item.sent_at,
    }


@app.get("/api/notifications")
def list_notifications(actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> list[dict]:
    items = db.query(NotificationQueue).filter_by(organization_id=actor.organization_id).order_by(NotificationQueue.created_at.desc()).limit(100).all()
    return [notification_public(db, item) for item in items]


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


def dispatch_line_reply(reply_token: str, message: str) -> None:
    if not LINE_CHANNEL_ACCESS_TOKEN or not reply_token:
        return
    request = UrlRequest(
        "https://api.line.me/v2/bot/message/reply",
        data=json.dumps({"replyToken": reply_token, "messages": [{"type": "text", "text": message}]}, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10):
            pass
    except (URLError, OSError):
        pass


def queue_alighted_notifications(db: Session, organization_id: int, trip_id: int, child: Child, occurred_at: datetime, actor: Staff | None = None) -> list[NotificationQueue]:
    value = occurred_at if occurred_at.tzinfo else occurred_at.replace(tzinfo=timezone.utc)
    occurred_at_jst = value.astimezone(JST).strftime("%Y/%m/%d %H:%M")
    event_key = f"org:{organization_id}:trip:{trip_id}:child:{child.id}:alighted"
    message = f"まもるバスからのお知らせです。{child.name}さんの降車記録を{occurred_at_jst}に受け付けました。※本通知は記録のお知らせであり、安全確認の最終判断を代替するものではありません。"
    subject = "【まもるバス】降車記録のお知らせ"
    rows = db.query(ChildGuardian, GuardianContact).join(
        GuardianContact, GuardianContact.id == ChildGuardian.guardian_contact_id,
    ).filter(
        ChildGuardian.organization_id == organization_id,
        ChildGuardian.child_id == child.id,
        ChildGuardian.notify_alighted.is_(True),
        GuardianContact.organization_id == organization_id,
        GuardianContact.is_active.is_(True),
        GuardianContact.consented_at.is_not(None),
    ).all()
    created: list[NotificationQueue] = []
    for link, guardian in rows:
        channels: list[tuple[str, str]] = []
        if guardian.email_enabled:
            channels.append(("email", guardian.email))
        if guardian.line_enabled and guardian.line_status == "linked":
            line_contact = db.query(LineContact).filter_by(
                organization_id=organization_id,
                guardian_contact_id=guardian.id,
                is_active=True,
            ).first()
            if line_contact:
                channels.append(("line", line_contact.line_user_id))
        for channel, recipient in channels:
            existing = db.query(NotificationQueue).filter_by(
                event_key=event_key, guardian_contact_id=guardian.id, channel=channel,
            ).first()
            if existing:
                continue
            item = NotificationQueue(
                organization_id=organization_id,
                guardian_contact_id=guardian.id,
                child_id=child.id,
                recipient_type="guardian",
                recipient=recipient,
                message=message,
                subject=subject if channel == "email" else None,
                channel=channel,
                event_key=event_key,
                template_key="child.alighted.v1",
            )
            db.add(item); db.flush(); created.append(item)
            if NOTIFICATION_FEATURE_ENABLED:
                dispatch_queue_item(item)
    audit(db, actor, "notification.event.create", "trip", trip_id, {
        "event_key": event_key, "child_id": child.id,
        "created": len(created), "channels": [item.channel for item in created],
    }, organization_id=organization_id)
    return created


@app.post("/api/notification-events", status_code=status.HTTP_201_CREATED)
def create_notification_event(data: NotificationEventIn, actor: Staff = Depends(require_roles("admin", "operator")), db: Session = Depends(get_db)) -> dict:
    trip = trip_for_org(db, data.trip_id, actor)
    child = db.query(Child).filter_by(id=data.child_id, organization_id=actor.organization_id).first()
    if not child or not db.query(TripAttendance).filter_by(trip_id=trip.id, child_id=child.id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "園児または運行記録が見つかりません")
    items = queue_alighted_notifications(db, actor.organization_id, trip.id, child, data.occurred_at or utc_now(), actor)
    db.commit()
    return {"event_key": f"org:{actor.organization_id}:trip:{trip.id}:child:{child.id}:alighted", "created": len(items), "notification_ids": [item.id for item in items]}


@app.post("/api/notifications/{notification_id}/dispatch")
@app.post("/api/notifications/{notification_id}/retry")
def dispatch_notification(notification_id: int, actor: Staff = Depends(require_roles("admin")), db: Session = Depends(get_db)) -> dict:
    item = db.query(NotificationQueue).filter_by(id=notification_id, organization_id=actor.organization_id).first()
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "通知が見つかりません")
    if item.template_key == "line.link.v1":
        raise HTTPException(status.HTTP_409_CONFLICT, "LINE連携案内は機密リンクを保存しないため、保護者画面から再発行してください")
    if item.status == "sent":
        raise HTTPException(status.HTTP_409_CONFLICT, "送信済み通知は再送できません")
    dispatch_queue_item(item)
    audit(db, actor, "notification.dispatch", "notification", item.id, {
        "status": item.status, "channel": item.channel, "attempt_count": item.attempt_count,
    })
    db.commit()
    return notification_public(db, item)


@app.post("/api/integrations/line/webhook", status_code=status.HTTP_200_OK)
async def line_webhook(request: Request, db: Session = Depends(get_db)) -> None:
    if not LINE_CHANNEL_SECRET or not LINE_ORGANIZATION_ID:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "LINE連携が未設定です")
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")
    expected = base64.b64encode(hmac.new(LINE_CHANNEL_SECRET.encode(), body, sha256).digest()).decode()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "LINE署名が不正です")
    try:
        events = json.loads(body.decode("utf-8")).get("events", [])
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "LINE Webhook JSONが不正です")
    for event in events:
        user_id = event.get("source", {}).get("userId")
        if not user_id:
            continue
        webhook_event_id = event.get("webhookEventId")
        contact = db.query(LineContact).filter_by(organization_id=LINE_ORGANIZATION_ID, line_user_id=user_id).first()
        if contact and webhook_event_id and contact.last_webhook_event_id == webhook_event_id:
            continue
        if not contact:
            contact = LineContact(organization_id=LINE_ORGANIZATION_ID, line_user_id=user_id)
            db.add(contact); db.flush()
        contact.last_webhook_event_id, contact.last_event_at = webhook_event_id, utc_now()
        event_type = event.get("type")
        if event_type == "unfollow":
            contact.is_active = False
            if contact.guardian_contact_id:
                guardian = db.get(GuardianContact, contact.guardian_contact_id)
                if guardian and guardian.organization_id == LINE_ORGANIZATION_ID:
                    guardian.line_status, guardian.updated_at = "unfollowed", utc_now()
            audit(db, None, "line.contact.unfollow", "line_contact", contact.id, organization_id=LINE_ORGANIZATION_ID)
            continue
        contact.is_active = True
        if event_type != "message" or event.get("message", {}).get("type") != "text":
            continue
        text_message = event.get("message", {}).get("text", "").strip()
        if not text_message.startswith("連携 "):
            continue
        raw_token = text_message[3:].strip()
        link_request = db.query(LineLinkRequest).filter_by(token_hash=line_link_token_hash(raw_token)).first()
        reply = "連携情報を確認できませんでした。園へQR案内の再発行をご依頼ください。"
        if link_request and link_request.organization_id == LINE_ORGANIZATION_ID:
            guardian = db.query(GuardianContact).filter_by(id=link_request.guardian_contact_id, organization_id=LINE_ORGANIZATION_ID).first()
            if link_request.status == "pending" and link_request.expires_at < utc_now():
                link_request.status = "expired"
                if guardian:
                    guardian.line_status, guardian.updated_at = "expired", utc_now()
                reply = "連携期限が切れています。園へQR案内の再発行をご依頼ください。"
            elif link_request.status == "pending" and guardian and guardian.is_active and guardian.line_enabled and guardian.consented_at:
                existing = db.query(LineContact).filter(
                    LineContact.organization_id == LINE_ORGANIZATION_ID,
                    LineContact.guardian_contact_id == guardian.id,
                    LineContact.id != contact.id,
                ).first()
                if existing:
                    reply = "別のLINEアカウントが連携済みです。変更する場合は園へご連絡ください。"
                elif contact.guardian_contact_id and contact.guardian_contact_id != guardian.id:
                    reply = "このLINEアカウントは別の保護者連絡先に連携済みです。園へご連絡ください。"
                else:
                    contact.guardian_contact_id = guardian.id
                    link_request.status, link_request.used_at = "used", utc_now()
                    guardian.line_status, guardian.updated_at = "linked", utc_now()
                    reply = f"{LINE_OFFICIAL_ACCOUNT_NAME}のLINE通知連携が完了しました。"
                    audit(db, None, "line.contact.link", "guardian_contact", guardian.id, {
                        "line_contact_id": contact.id, "line_link_request_id": link_request.id,
                    }, organization_id=LINE_ORGANIZATION_ID)
        dispatch_line_reply(event.get("replyToken", ""), reply)
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
async def upload_video(trip_id: int, file: UploadFile = File(...), duration_seconds: int | None = Form(None), actor: Staff = Depends(current_staff), db: Session = Depends(get_db)):
    trip_for_org(db, trip_id, actor)
    if not (file.content_type or "").startswith("video/"): raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "動画ファイルを指定してください")
    validate_video_duration(duration_seconds)
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
    db.add(item); db.flush(); audit(db, actor, "video.upload", "video", item.id, {"size": size, "duration_seconds": duration_seconds}); db.commit(); return {"id": item.id, "ai_status": item.ai_status}

@app.get("/api/videos/{video_id}/download")
def download_video(video_id: int, actor: Staff = Depends(current_staff), db: Session = Depends(get_db)):
    item = db.query(VideoEvidence).filter_by(id=video_id, organization_id=actor.organization_id).first()
    if not item: raise HTTPException(404, "動画が見つかりません")
    target = (UPLOAD_DIR / item.storage_key).resolve()
    if UPLOAD_DIR not in target.parents:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "動画の保存先が不正です")
    if not target.exists() or not target.is_file():
        raise HTTPException(404, "動画ファイルが見つかりません。再デプロイ等で削除された可能性があります")
    audit(db, actor, "video.download", "video", item.id)
    db.commit()
    return FileResponse(target, media_type=item.content_type, filename=item.file_name)

@app.post("/api/videos/{video_id}/analyze")
def analyze_video(video_id: int, actor: Staff = Depends(require_roles("admin", "operator", "verifier")), db: Session = Depends(get_db)):
    item = db.query(VideoEvidence).filter_by(id=video_id, organization_id=actor.organization_id).first()
    if not item: raise HTTPException(404, "動画が見つかりません")
    item.ai_status, item.ai_result = "needs_human_review", "AI補助: 子どもらしき人影や見えにくい場所の最終判断は未接続です。座席、足元、座席の下、荷物の陰を職員が再確認してください"
    audit(db, actor, "video.analyze.request", "video", item.id); db.commit(); return {"id": item.id, "ai_status": item.ai_status, "ai_result": item.ai_result}







