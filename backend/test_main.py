import unittest
from datetime import datetime, timezone

from fastapi import HTTPException

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
    list_vehicles,
    trip_summary,
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

    def test_complete_requires_vehicle_video(self) -> None:
        with self.assertRaises(HTTPException) as context:
            complete_trip(self.trip.id, actor=self.actor, db=self.db)

        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(context.exception.detail, "30秒の車内撮影が必要です")
        self.assertEqual(self.trip.status, "運行中")

if __name__ == "__main__":
    unittest.main()


