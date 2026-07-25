import unittest
from datetime import datetime, timezone

from fastapi import HTTPException

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import (
    AuditLog,
    BusRoute,
    Vehicle,
    VehicleCreate,
    create_vehicle,
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
    dashboard,
    hash_pin,
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


if __name__ == "__main__":
    unittest.main()
