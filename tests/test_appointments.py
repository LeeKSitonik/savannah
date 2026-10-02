import pytest
from datetime import time
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app import models

# Set up an isolated in-memory SQLite database for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override database dependency in FastAPI
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Re-create database tables and seed baseline doctor & patient before each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    doctor = models.Doctor(
        id=1,
        name="Dr. Wanjiku Kamau",
        work_start_time=time(9, 0),
        work_end_time=time(17, 0)
    )
    patient = models.Patient(
        id=1,
        name="John Doe",
        email="johndoe@example.com"
    )
    db.add(doctor)
    db.add(patient)
    db.commit()

    yield  # Run test

    Base.metadata.drop_all(bind=engine)


# --- AVAILABILITY TESTS ---

def test_get_doctor_availability_success():
    """Verify available 30-minute slots are generated correctly for a doctor."""
    response = client.get("/doctors/1/availability?appointment_date=2026-10-05")
    assert response.status_code == 200
    slots = response.json()
    assert len(slots) == 16  # 8 working hours (09:00 - 17:00) = 16 thirty-minute slots


def test_get_doctor_availability_doctor_not_found():
    """Verify 404 is returned when requesting availability for a non-existent doctor."""
    response = client.get("/doctors/999/availability?appointment_date=2026-10-05")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# --- BOOKING TESTS ---

def test_create_appointment_success():
    """Verify an appointment can be successfully booked."""
    payload = {
        "doctor_id": 1,
        "patient_id": 1,
        "start_time": "2026-10-05T09:00:00"
    }
    response = client.post("/appointments/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["doctor_id"] == 1
    assert data["patient_id"] == 1
    assert data["status"] == "BOOKED"
    assert "2026-10-05T09:30:00" in data["end_time"]


def test_create_appointment_double_booking_fails():
    """Verify double-booking the exact same slot returns a 400 error."""
    payload = {
        "doctor_id": 1,
        "patient_id": 1,
        "start_time": "2026-10-05T09:00:00"
    }
    # Initial booking
    res1 = client.post("/appointments/", json=payload)
    assert res1.status_code == 201

    # Conflict booking
    res2 = client.post("/appointments/", json=payload)
    assert res2.status_code == 400
    assert "already booked" in res2.json()["detail"].lower()


def test_create_appointment_outside_working_hours_fails():
    """Verify booking before doctor working hours (e.g., 08:00 AM) fails."""
    payload = {
        "doctor_id": 1,
        "patient_id": 1,
        "start_time": "2026-10-05T08:00:00"
    }
    response = client.post("/appointments/", json=payload)
    assert response.status_code == 400
    assert "outside" in response.json()["detail"].lower()


# --- CANCELLATION TESTS ---

def test_cancel_appointment_success():
    """Verify an active booking can be cancelled and slot freed."""
    book_resp = client.post("/appointments/", json={
        "doctor_id": 1,
        "patient_id": 1,
        "start_time": "2026-10-05T10:00:00"
    })
    appointment_id = book_resp.json()["id"]

    cancel_resp = client.patch(f"/appointments/{appointment_id}/cancel", json={
        "cancellation_reason": "Patient requested cancellation"
    })
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"


# --- RESCHEDULING TESTS ---

def test_reschedule_appointment_success():
    """Verify an existing appointment can be moved to a new slot."""
    book_resp = client.post("/appointments/", json={
        "doctor_id": 1,
        "patient_id": 1,
        "start_time": "2026-10-05T10:00:00"
    })
    appointment_id = book_resp.json()["id"]

    reschedule_resp = client.patch(f"/appointments/{appointment_id}/reschedule", json={
        "new_start_time": "2026-10-05T11:00:00"
    })
    assert reschedule_resp.status_code == 200
    assert "2026-10-05T11:00:00" in reschedule_resp.json()["start_time"]