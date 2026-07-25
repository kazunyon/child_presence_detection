import unittest
from datetime import datetime, timezone

from fastapi import HTTPException

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import (
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

if __name__ == "__main__":
    unittest.main()
