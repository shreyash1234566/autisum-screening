import pytest
from datetime import datetime
from database import Child, Session, Doctor

def seed_data(db_session):
    """Utility to seed test children and sessions."""
    child1 = Child(id="child-1", name="Kid One", age_months=24, gender="male", language="en")
    child2 = Child(id="child-2", name="Kid Two", age_months=32, gender="female", language="hi")
    db_session.add(child1)
    db_session.add(child2)
    
    sess1 = Session(
        id="sess-1",
        child_id="child-1",
        started_at=datetime(2026, 6, 10, 10, 0, 0),
        flagged=True,
        processing_status="done",
        risk_level="high",
        combined_risk_score=0.55
    )
    sess2 = Session(
        id="sess-2",
        child_id="child-2",
        started_at=datetime(2026, 6, 10, 11, 0, 0),
        flagged=False,
        processing_status="done",
        risk_level="low",
        combined_risk_score=0.15
    )
    db_session.add(sess1)
    db_session.add(sess2)
    db_session.commit()


def test_get_flagged_sessions(client, db_session):
    """Test retrieving flagged sessions only, sorted by started_at desc."""
    seed_data(db_session)

    response = client.get("/doctor/flagged")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "sess-1"
    assert data[0]["child_name"] == "Kid One"
    assert data[0]["flagged"] is True


def test_get_all_sessions(client, db_session):
    """Test retrieving all sessions with limit checks."""
    seed_data(db_session)

    response = client.get("/doctor/all?limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    # sess-2 was created at 11:00, sess-1 at 10:00. Sorting is desc, so sess-2 should be first.
    assert data[0]["id"] == "sess-2"
    assert data[0]["child_name"] == "Kid Two"


def test_submit_judgment_success(client, db_session):
    """Test successful doctor judgment submission."""
    seed_data(db_session)

    payload = {
        "judgment": "monitoring",
        "notes": "Shows delayed speech, request follow-up."
    }
    response = client.post("/doctor/sess-1/judgment", json=payload)
    assert response.status_code == 200
    assert response.json() == {"ok": True, "judgment": "monitoring"}

    # Verify database updates
    sess = db_session.query(Session).filter(Session.id == "sess-1").first()
    assert sess.doctor_judgment == "monitoring"
    assert sess.doctor_notes == "Shows delayed speech, request follow-up."
    assert sess.doctor_reviewed_at is not None


def test_submit_judgment_invalid_choice(client, db_session):
    """Test that submitting an invalid judgment label returns a validation error."""
    seed_data(db_session)

    payload = {
        "judgment": "invalid_label",
        "notes": "N/A"
    }
    response = client.post("/doctor/sess-1/judgment", json=payload)
    assert response.status_code == 422


def test_submit_judgment_session_not_found(client, db_session):
    """Test judgment submission on a non-existent session yields 404."""
    payload = {
        "judgment": "typical",
        "notes": ""
    }
    response = client.post("/doctor/non-existent-session/judgment", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"
