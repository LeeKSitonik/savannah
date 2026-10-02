from datetime import time
from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.database import Base, engine, SessionLocal
from app.models import Doctor
from app.routers import doctors, appointments

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="savannah a Clinic Booking System")

# Register Routers
app.include_router(doctors.router)
app.include_router(appointments.router)


@app.on_event("startup")
def seed_doctors():
    """
    Seed initial 5 doctors with default 09:00 - 17:00 working hours
    if they do not already exist in the database.
    """
    db: Session = SessionLocal()
    try:
        doctor_count = db.query(Doctor).count()
        if doctor_count == 0:
            initial_doctors = [
                Doctor(name="Dr. Wanjiku Kamau", work_start_time=time(9, 0), work_end_time=time(17, 0)),
                Doctor(name="Dr. Ochieng Otieno", work_start_time=time(9, 0), work_end_time=time(17, 0)),
                Doctor(name="Dr. Kipchumba Bett", work_start_time=time(9, 0), work_end_time=time(17, 0)),
                Doctor(name="Dr. Achieng Hassan", work_start_time=time(9, 0), work_end_time=time(17, 0)),
                Doctor(name="Dr. Mutua Musyoka", work_start_time=time(9, 0), work_end_time=time(17, 0)),
            ]
            db.add_all(initial_doctors)
            db.commit()
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "Clinic Booking System API is running"}