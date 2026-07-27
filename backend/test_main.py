import asyncio
import base64
import hashlib
import hmac
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException, Request

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.main as main_module

from backend.main import (
    AuditLog,
    BusRoute,
    RouteChild,
    Vehicle,
    VehicleSafetyCheck,
    VideoEvidence,
    TripCreate,
    VehicleCreate,
    create_trip,
    create_vehicle,
    delete_route,
    delete_vehicle,
    download_video,
    list_vehicles,
    trip_record,
    trip_summary,
    validate_video_duration,
    Base,
    BusTrip,
    Child,
    Organization,
    Staff,
    TripAttendance,
    cancel_unstarted_trip,
    complete_trip,
    dashboard,
    hash_pin,
    list_routes,
    list_trips,
)


class CancelledTripVisibilityTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()

        organization = Organization(name="テスト園")
        self.db.add(organization)
        self.db.flush()
        self.actor = Staff(
            organization_id=organization.id,
            name="管理者",
            role="admin",
            password_hash=hash_pin("test-pin"),
        )
        child = Child(
            organization_id=organization.id,
            name="園児",
            qr_token="test-child",
        )
        self.db.add_all([self.actor, child])
        self.db.flush()

        started_at = datetime.now(timezone.utc)
        self.active_trip = BusTrip(
            organization_id=organization.id,
            direction="帰り",
            status="運行中",
            started_at=started_at,
        )
        self.completed_trip = BusTrip(
            organization_id=organization.id,
            direction="帰り",
            status="完了",
            started_at=started_at,
            completed_at=started_at,
        )
        self.cancelled_trip = BusTrip(
            organization_id=organization.id,
            direction="帰り",
            status="中止",
            started_at=started_at,
            completed_at=started_at,
        )
        self.db.add_all([
            self.active_trip,
            self.completed_trip,
            self.cancelled_trip,
        ])
        self.db.flush()
        self.db.add_all([
            TripAttendance(
                trip_id=self.active_trip.id,
                child_id=child.id,
                boarded_at=started_at,
                boarded_by="通常名簿",
            ),
            TripAttendance(
                trip_id=self.cancelled_trip.id,
                child_id=child.id,
                boarded_at=started_at,
            ),
        ])
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()

    def test_dashboard_excludes_cancelled_trips_and_their_unconfirmed_count(self) -> None:
        result = dashboard(actor=self.actor, db=self.db)

        self.assertEqual(result["today_trip_count"], 2)
        self.assertEqual(result["active_trip_count"], 1)
        self.assertEqual(result["completed_trip_count"], 1)
        self.assertEqual(result["unconfirmed_count"], 1)
        self.assertNotIn(
            self.cancelled_trip.id,
            [trip["trip_id"] for trip in result["recent_trips"]],
        )

    def test_trip_history_excludes_cancelled_trips(self) -> None:
        result = list_trips(actor=self.actor, db=self.db)

        self.assertEqual(
            {trip["trip_id"] for trip in result},
            {self.active_trip.id, self.completed_trip.id},
        )


    def test_return_trip_with_normal_roster_boarding_can_be_cancelled(self) -> None:
        result = cancel_unstarted_trip(
            self.active_trip.id,
            actor=self.actor,
            db=self.db,
        )

        self.assertEqual(result, {"status": "中止"})
        self.assertEqual(self.active_trip.status, "中止")
        self.assertIsNotNone(self.active_trip.completed_at)

    def test_trip_with_actual_alighting_cannot_be_cancelled(self) -> None:
        attendance = self.db.query(TripAttendance).filter_by(
            trip_id=self.active_trip.id,
        ).one()
        attendance.alighted_at = datetime.now(timezone.utc)
        attendance.alighted_by = self.actor.name
        self.db.commit()

        with self.assertRaises(HTTPException) as context:
            cancel_unstarted_trip(
                self.active_trip.id,
                actor=self.actor,
                db=self.db,
            )

        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(self.active_trip.status, "運行中")



class RouteDeletionTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()

        organization = Organization(name="テスト園")
        self.db.add(organization)
        self.db.flush()
        self.actor = Staff(
            organization_id=organization.id,
            name="管理者",
            role="admin",
            password_hash=hash_pin("test-pin"),
        )
        self.child = Child(
            organization_id=organization.id,
            name="園児",
            qr_token="test-child",
        )
        self.vehicle = Vehicle(
            organization_id=organization.id,
            name="1号車",
            plate_number="品川 500 い 2222",
        )
        self.db.add_all([self.actor, self.child, self.vehicle])
        self.db.flush()
        self.route = BusRoute(
            organization_id=organization.id,
            name="1号車・往路",
            direction="往路",
            vehicle_id=self.vehicle.id,
        )
        self.db.add(self.route)
        self.db.flush()
        self.db.add(RouteChild(route_id=self.route.id, child_id=self.child.id))
        self.trip = BusTrip(
            organization_id=organization.id,
            route_id=self.route.id,
            vehicle_id=self.vehicle.id,
            direction="往路",
            status="完了",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )
        self.db.add(self.trip)
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()

    def test_delete_hides_route_removes_roster_and_preserves_trip_history(self) -> None:
        result = delete_route(self.route.id, actor=self.actor, db=self.db)

        self.assertEqual(result, {"status": "deleted", "removed_roster_count": 1})
        self.assertFalse(self.route.is_active)
        self.assertEqual(list_routes(actor=self.actor, db=self.db), [])
        self.assertEqual(trip_summary(self.db, self.trip)["route_name"], "1号車・往路")
        self.assertEqual(self.db.query(RouteChild).filter_by(route_id=self.route.id).count(), 0)
        audit_log = self.db.query(AuditLog).filter_by(action="route.delete").one()
        self.assertEqual(audit_log.resource_id, str(self.route.id))

    def test_deleted_route_cannot_be_started(self) -> None:
        delete_route(self.route.id, actor=self.actor, db=self.db)

        with self.assertRaises(HTTPException) as context:
            create_trip(
                TripCreate(route_id=self.route.id, vehicle_id=self.vehicle.id, direction="往路"),
                actor=self.actor,
                db=self.db,
            )

        self.assertEqual(context.exception.status_code, 404)
class VehicleDeletionTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()

        organization = Organization(name="テスト園")
        self.db.add(organization)
        self.db.flush()
        self.actor = Staff(
            organization_id=organization.id,
            name="管理者",
            role="admin",
            password_hash=hash_pin("test-pin"),
        )
        self.vehicle = Vehicle(
            organization_id=organization.id,
            name="1号車",
            plate_number="品川 500 い 2222",
        )
        self.db.add_all([self.actor, self.vehicle])
        self.db.flush()
        self.route = BusRoute(
            organization_id=organization.id,
            name="1号車・往路",
            direction="往路",
            vehicle_id=self.vehicle.id,
        )
        self.trip = BusTrip(
            organization_id=organization.id,
            route_id=None,
            vehicle_id=self.vehicle.id,
            direction="往路",
            status="完了",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )
        self.db.add_all([self.route, self.trip])
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()

    def test_delete_hides_vehicle_detaches_route_and_preserves_trip_history(self) -> None:
        result = delete_vehicle(self.vehicle.id, actor=self.actor, db=self.db)

        self.assertEqual(result, {"status": "deleted", "detached_route_count": 1})
        self.assertFalse(self.vehicle.is_active)
        self.assertIsNone(self.route.vehicle_id)
        self.assertEqual(self.trip.vehicle_id, self.vehicle.id)
        self.assertEqual(list_vehicles(actor=self.actor, db=self.db), [])
        self.assertEqual(trip_summary(self.db, self.trip)["vehicle_name"], "1号車")
        audit_log = self.db.query(AuditLog).filter_by(action="vehicle.delete").one()
        self.assertEqual(audit_log.resource_id, str(self.vehicle.id))

    def test_registering_same_name_restores_deleted_vehicle(self) -> None:
        delete_vehicle(self.vehicle.id, actor=self.actor, db=self.db)

        restored = create_vehicle(
            VehicleCreate(name="1号車", plate_number="品川 500 い 3333"),
            actor=self.actor,
            db=self.db,
        )

        self.assertEqual(restored.id, self.vehicle.id)
        self.assertTrue(restored.is_active)
        self.assertEqual(restored.plate_number, "品川 500 い 3333")
        self.assertEqual(
            [item.id for item in list_vehicles(actor=self.actor, db=self.db)],
            [self.vehicle.id],
        )



class VehicleVideoEvidenceTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()

        organization = Organization(name="テスト園")
        self.db.add(organization)
        self.db.flush()
        self.actor = Staff(
            organization_id=organization.id,
            name="管理者",
            role="admin",
            password_hash=hash_pin("test-pin"),
        )
        child = Child(
            organization_id=organization.id,
            name="園児",
            qr_token="test-child",
        )
        self.db.add_all([self.actor, child])
        self.db.flush()
        now = datetime.now(timezone.utc)
        self.trip = BusTrip(
            organization_id=organization.id,
            direction="帰り",
            status="運行中",
            started_at=now,
        )
        self.db.add(self.trip)
        self.db.flush()
        self.db.add_all([
            TripAttendance(
                trip_id=self.trip.id,
                child_id=child.id,
                boarded_at=now,
                alighted_at=now,
                boarded_by="通常名簿",
                alighted_by=self.actor.name,
            ),
            VehicleSafetyCheck(
                organization_id=organization.id,
                trip_id=self.trip.id,
                check_type="tail_qr",
                staff_id=self.actor.id,
                staff_name=self.actor.name,
                qr_token="bus-tail-2",
            ),
            VehicleSafetyCheck(
                organization_id=organization.id,
                trip_id=self.trip.id,
                check_type="third_party",
                staff_id=self.actor.id,
                staff_name=self.actor.name,
                qr_token="third-party-confirmed",
            ),
        ])
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()

    def test_trip_summary_includes_latest_video_ai_status(self) -> None:
        self.db.add(VideoEvidence(
            organization_id=self.actor.organization_id,
            trip_id=self.trip.id,
            uploaded_by=self.actor.id,
            file_name="vehicle.webm",
            storage_key="1/video.webm",
            content_type="video/webm",
            ai_status="needs_human_review",
            ai_result="再確認してください",
        ))
        self.db.commit()

        result = trip_summary(self.db, self.trip)

        self.assertEqual(result["video_evidence_count"], 1)
        self.assertEqual(result["latest_video_ai_status"], "needs_human_review")
        self.assertEqual(result["latest_video_ai_result"], "再確認してください")

    def test_trip_record_includes_video_storage_location(self) -> None:
        self.db.add(VideoEvidence(
            organization_id=self.actor.organization_id,
            trip_id=self.trip.id,
            uploaded_by=self.actor.id,
            file_name="vehicle.webm",
            storage_key="1/video.webm",
            content_type="video/webm",
            ai_status="needs_human_review",
            ai_result="再確認してください",
        ))
        self.db.commit()

        result = trip_record(self.trip.id, actor=self.actor, db=self.db)
        video = result["videos"][0]

        self.assertEqual(video["id"], 1)
        self.assertEqual(video["storage_key"], "1/video.webm")
        self.assertTrue(
            video["storage_path"].endswith("uploads\\1\\video.webm")
            or video["storage_path"].endswith("uploads/1/video.webm")
        )
        self.assertEqual(video["content_type"], "video/webm")
    def test_download_video_returns_same_org_file_response(self) -> None:
        video = VideoEvidence(
            organization_id=self.actor.organization_id,
            trip_id=self.trip.id,
            uploaded_by=self.actor.id,
            file_name="vehicle.webm",
            storage_key="1/video.webm",
            content_type="video/webm",
        )
        self.db.add(video)
        self.db.commit()
        self.db.refresh(video)

        original_upload_dir = main_module.UPLOAD_DIR
        with tempfile.TemporaryDirectory() as temp_dir:
            main_module.UPLOAD_DIR = Path(temp_dir).resolve()
            target = main_module.UPLOAD_DIR / video.storage_key
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"video-bytes")
            try:
                response = download_video(video.id, actor=self.actor, db=self.db)
            finally:
                main_module.UPLOAD_DIR = original_upload_dir

        self.assertEqual(str(response.path), str(target))
        self.assertEqual(response.media_type, "video/webm")
    def test_complete_requires_vehicle_video(self) -> None:
        with self.assertRaises(HTTPException) as context:
            complete_trip(self.trip.id, actor=self.actor, db=self.db)

        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(context.exception.detail, "5秒以上の車内撮影が必要です")
        self.assertEqual(self.trip.status, "運行中")

    def test_video_duration_allows_5_to_30_seconds(self) -> None:
        validate_video_duration(5)
        validate_video_duration(30)

    def test_video_duration_rejects_less_than_5_or_over_30_seconds(self) -> None:
        for duration in (4, 31):
            with self.subTest(duration=duration):
                with self.assertRaises(HTTPException) as context:
                    validate_video_duration(duration)
                self.assertEqual(context.exception.status_code, 422)

class LineGuardianNotificationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.organization = Organization(name="バナナ幼稚園")
        self.db.add(self.organization); self.db.flush()
        self.actor = Staff(
            organization_id=self.organization.id,
            name="管理者", role="admin", password_hash=hash_pin("test-pin"),
        )
        self.child = Child(
            organization_id=self.organization.id,
            name="園児A", qr_token="child-a",
        )
        self.db.add_all([self.actor, self.child]); self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def create_guardian(self):
        return main_module.create_guardian_contact(
            main_module.GuardianContactIn(
                name="保護者A", email=" Parent@Example.JP ", email_enabled=True,
                line_enabled=True, consent=True, child_ids=[self.child.id], relationship="母",
            ),
            actor=self.actor, db=self.db,
        )

    def test_guardian_registration_normalizes_email_and_links_child(self) -> None:
        result = self.create_guardian()
        guardian = self.db.get(main_module.GuardianContact, result["id"])

        self.assertEqual(guardian.email_normalized, "parent@example.jp")
        self.assertTrue(guardian.consented_at)
        self.assertEqual(result["children"][0]["id"], self.child.id)
        self.assertEqual(result["line_status"], "not_requested")

    def test_line_requires_email_channel_and_consent_can_be_withdrawn(self) -> None:
        with self.assertRaises(HTTPException) as context:
            main_module.create_guardian_contact(
                main_module.GuardianContactIn(
                    email="parent@example.jp", email_enabled=False, line_enabled=True,
                    consent=True, child_ids=[self.child.id],
                ), actor=self.actor, db=self.db,
            )
        self.assertEqual(context.exception.status_code, 422)
        self.db.rollback()

        result = self.create_guardian()
        updated = main_module.update_guardian_contact(
            result["id"], main_module.GuardianContactUpdate(consent=False),
            actor=self.actor, db=self.db,
        )
        self.assertIsNone(updated["consented_at"])
        self.assertFalse(updated["email_enabled"])
        self.assertFalse(updated["line_enabled"])
        self.assertEqual(updated["line_status"], "revoked")
    def test_line_link_issue_returns_banana_account_qr_without_storing_raw_link(self) -> None:
        result = self.create_guardian()
        guardian = self.db.get(main_module.GuardianContact, result["id"])

        class FakeResponse:
            status = 202
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, _limit): return b'{"message_id":"mail-1"}'

        with patch.object(main_module, "EMAIL_WEBHOOK_URL", "https://mail.example.test/send"), patch.object(main_module, "urlopen", return_value=FakeResponse()):
            issued = main_module.issue_line_link_request_for_guardian(guardian, self.actor, self.db)

        self.assertEqual(issued["official_account_name"], "バナナ幼稚園")
        self.assertEqual(issued["line_basic_id"], "@408mrkbk")
        self.assertIn("/oaMessage/@408mrkbk/", issued["line_link_url"])
        self.assertTrue(issued["qr_png_data_url"].startswith("data:image/png;base64,"))
        request_row = self.db.get(main_module.LineLinkRequest, issued["request_id"])
        notification = self.db.get(main_module.NotificationQueue, request_row.email_notification_id)
        self.assertEqual(notification.status, "sent")
        self.assertNotIn("line.me", notification.message)
        self.assertEqual(len(request_row.token_hash), 64)

    def test_signed_webhook_links_guardian_once(self) -> None:
        result = self.create_guardian()
        guardian = self.db.get(main_module.GuardianContact, result["id"])
        guardian.line_status = "pending"
        request_row = main_module.LineLinkRequest(
            organization_id=self.organization.id,
            guardian_contact_id=guardian.id,
            token_hash=main_module.line_link_token_hash("known-token"),
            expires_at=main_module.utc_now() + main_module.timedelta(hours=1),
            requested_by=self.actor.id,
        )
        self.db.add(request_row); self.db.commit()
        payload = {"events": [{
            "type": "message", "webhookEventId": "evt-1", "replyToken": "reply-1",
            "source": {"userId": "U123"},
            "message": {"type": "text", "text": "連携 known-token"},
        }]}
        body = json.dumps(payload, ensure_ascii=False).encode()
        secret = "line-secret"
        signature = base64.b64encode(hmac.new(secret.encode(), body, hashlib.sha256).digest()).decode()
        delivered = False
        async def receive():
            nonlocal delivered
            if delivered:
                return {"type": "http.request", "body": b"", "more_body": False}
            delivered = True
            return {"type": "http.request", "body": body, "more_body": False}
        request = Request({"type": "http", "method": "POST", "path": "/api/integrations/line/webhook", "headers": [(b"x-line-signature", signature.encode())]}, receive)

        with patch.object(main_module, "LINE_CHANNEL_SECRET", secret), patch.object(main_module, "LINE_ORGANIZATION_ID", self.organization.id), patch.object(main_module, "LINE_CHANNEL_ACCESS_TOKEN", None):
            asyncio.run(main_module.line_webhook(request, self.db))

        self.db.refresh(guardian); self.db.refresh(request_row)
        contact = self.db.query(main_module.LineContact).filter_by(line_user_id="U123").one()
        self.assertEqual(guardian.line_status, "linked")
        self.assertEqual(request_row.status, "used")
        self.assertEqual(contact.guardian_contact_id, guardian.id)
        self.assertEqual(self.db.query(main_module.LineContact).count(), 1)

    def test_alighted_event_creates_line_and_email_once(self) -> None:
        result = self.create_guardian()
        guardian = self.db.get(main_module.GuardianContact, result["id"])
        guardian.line_status = "linked"
        self.db.add(main_module.LineContact(
            organization_id=self.organization.id,
            guardian_contact_id=guardian.id,
            line_user_id="U123", is_active=True,
        ))
        trip = BusTrip(
            organization_id=self.organization.id, direction="帰り", status="運行中",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(trip); self.db.flush()
        self.db.add(TripAttendance(
            trip_id=trip.id, child_id=self.child.id,
            boarded_at=datetime.now(timezone.utc), alighted_at=datetime.now(timezone.utc),
        )); self.db.commit()

        with patch.object(main_module, "NOTIFICATION_FEATURE_ENABLED", False):
            first = main_module.queue_alighted_notifications(
                self.db, self.organization.id, trip.id, self.child,
                datetime.now(timezone.utc), self.actor,
            )
            second = main_module.queue_alighted_notifications(
                self.db, self.organization.id, trip.id, self.child,
                datetime.now(timezone.utc), self.actor,
            )
            self.db.commit()

        self.assertEqual({item.channel for item in first}, {"line", "email"})
        self.assertEqual(second, [])
        self.assertEqual(self.db.query(main_module.NotificationQueue).count(), 2)
if __name__ == "__main__":
    unittest.main()

