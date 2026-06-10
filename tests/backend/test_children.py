import pytest
from database import Child, Doctor

def test_register_child_success(client, db_session):
    """Test successful child registration."""
    # Seed doctor first to prevent validation failure
    doc = Doctor(id="doc_123", name="Dr. Smith", email="smith@example.com")
    db_session.add(doc)
    db_session.commit()

    payload = {
        "name": "Arjun Kumar",
        "age_months": 28,
        "gender": "male",
        "language": "hi",
        "doctor_id": "doc_123"
    }
    response = client.post("/children", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Arjun Kumar"
    assert data["age_months"] == 28
    assert data["gender"] == "male"
    assert data["language"] == "hi"
    assert "id" in data
    assert "created_at" in data

    # Verify database state
    child_db = db_session.query(Child).filter(Child.id == data["id"]).first()
    assert child_db is not None
    assert child_db.name == "Arjun Kumar"
    assert child_db.doctor_id == "doc_123"


def test_register_child_invalid_doctor(client, db_session):
    """Test child registration fails with 400 if doctor_id does not exist."""
    payload = {
        "name": "Arjun Kumar",
        "age_months": 28,
        "gender": "male",
        "language": "hi",
        "doctor_id": "nonexistent_doc"
    }
    response = client.post("/children", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Doctor not found"


def test_register_child_null_doctor(client, db_session):
    """Test child registration succeeds with null doctor_id."""
    payload = {
        "name": "Arjun Kumar",
        "age_months": 28,
        "gender": "male",
        "language": "hi",
        "doctor_id": None
    }
    response = client.post("/children", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Arjun Kumar"

    child_db = db_session.query(Child).filter(Child.id == data["id"]).first()
    assert child_db is not None
    assert child_db.doctor_id is None


def test_register_child_existing_id(client, db_session):
    """Test registering a child with a pre-existing ID returns the existing record."""
    child_id = "test-custom-id-999"
    # Seed child first
    child = Child(id=child_id, name="First Name", age_months=36, gender="other", language="en")
    db_session.add(child)
    db_session.commit()

    payload = {
        "id": child_id,
        "name": "Second Name",
        "age_months": 40,
        "gender": "female",
        "language": "hi"
    }
    response = client.post("/children", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Should return original seeded child record
    assert data["id"] == child_id
    assert data["name"] == "First Name"


def test_register_child_missing_fields(client):
    """Test validation errors for missing fields."""
    payload = {
        "age_months": 24,
        "gender": "female"
    }
    response = client.post("/children", json=payload)
    # Fastapi returns 422 for missing required fields (name)
    assert response.status_code == 422


def test_get_child_success(client, db_session):
    """Test retrieving child by ID."""
    child_id = "child-abc-123"
    child = Child(id=child_id, name="Pooja Sharma", age_months=20, gender="female", language="en")
    db_session.add(child)
    db_session.commit()

    response = client.get(f"/children/{child_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == child_id
    assert data["name"] == "Pooja Sharma"


def test_get_child_not_found(client):
    """Test non-existent child returns 404."""
    response = client.get("/children/non-existent-id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Child not found"


def test_register_child_negative_age(client):
    """Test registering a child with a negative age returns 422."""
    payload = {
        "name": "Arjun Kumar",
        "age_months": -5,
        "gender": "male",
        "language": "hi"
    }
    response = client.post("/children", json=payload)
    assert response.status_code == 422


def test_register_child_huge_age(client):
    """Test registering a child with an age exceeding maximum screening limit returns 422."""
    payload = {
        "name": "Arjun Kumar",
        "age_months": 150,
        "gender": "male",
        "language": "hi"
    }
    response = client.post("/children", json=payload)
    assert response.status_code == 422


def test_register_child_invalid_language(client):
    """Test registering a child with an unsupported language returns 422."""
    payload = {
        "name": "Arjun Kumar",
        "age_months": 24,
        "gender": "male",
        "language": "fr"
    }
    response = client.post("/children", json=payload)
    assert response.status_code == 422


def test_register_child_empty_name(client):
    """Test registering a child with an empty name returns 422."""
    payload = {
        "name": "",
        "age_months": 24,
        "gender": "male",
        "language": "en"
    }
    response = client.post("/children", json=payload)
    assert response.status_code == 422


def test_register_child_whitespace_name(client):
    """Test registering a child with a whitespace-only name returns 422."""
    payload = {
        "name": "    ",
        "age_months": 24,
        "gender": "male",
        "language": "en"
    }
    response = client.post("/children", json=payload)
    assert response.status_code == 422
