"""
apps/api/tests/test_alert_concurrency.py
Unit test for AlertEngine concurrency safety (v2.4).
Spawns 10 concurrent threads attempting to generate the same alert on a single village;
verifies that exactly 1 active alert is created without database corruption or duplicate alerts.
"""

import pytest
import threading
from app.database import SessionLocal
from app.models.village import Village
from app.models.alert import Alert
from app.services.alert_engine import alert_engine


def test_alert_concurrency_stress_test(db_session):
    """
    Spawns 10 concurrent worker threads attempting to generate the exact same alert simultaneously.
    Verifies that race conditions are prevented by the unique constraint and exactly 1 active alert exists.
    """
    village = db_session.query(Village).first()
    assert village is not None

    village_id = village.id

    # Clear pre-existing alerts for this village
    db_session.query(Alert).filter(Alert.village_id == village_id).delete()
    db_session.commit()

    created_alerts = []
    errors = []

    def worker_task(thread_id: int):
        thread_db = SessionLocal()
        try:
            # Query village in worker session
            v = thread_db.query(Village).filter(Village.id == village_id).first()
            alert = alert_engine.evaluate_and_create_alert(
                db=thread_db,
                village=v,
                risk_score=85,
                risk_level="CRITICAL",
                prediction_id=None,
                top_contributors=[{"feature": "rainfall_1h_mm", "contribution": 0.8, "direction": "increases_risk"}],
                simulation_substep=1,
            )
            if alert:
                created_alerts.append(alert.id)
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print("\nWORKER EXCEPTION:\n", tb)
            errors.append(tb)
        finally:
            thread_db.close()

    # Launch 10 simultaneous threads
    threads = [threading.Thread(target=worker_task, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Zero uncaught fatal database errors
    assert len(errors) == 0

    # Query database to count active alerts for this dedup key
    dedup_key = f"{village.id}:CRITICAL:1"
    active_count = (
        db_session.query(Alert)
        .filter(
            Alert.village_id == village.id,
            Alert.dedup_key == dedup_key,
            Alert.status == "ACTIVE",
        )
        .count()
    )

    # Concurrency verification: strictly 1 active alert in database
    assert active_count == 1
