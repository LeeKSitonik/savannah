from datetime import datetime, date, time, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.get("/{id}/availability", response_model=List[str])
def get_doctor_availability(
    id: int,
    appointment_date: date,
    db: Session = Depends(get_db)
):
    """
    Returns a list of available ISO-formatted 30-minute start times 
    for a given doctor on a specific date between working hours (09:00 - 17:00).
    Excludes any slots that already have an active 'BOOKED' appointment.
    """
    # 1. Verify doctor exists
    doctor = db.query(models.Doctor).filter(models.Doctor.id == id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID {id} not found."
        )

    # 2. Fetch all existing active bookings for this doctor on this day
    start_of_day = datetime.combine(appointment_date, time.min)
    end_of_day = datetime.combine(appointment_date, time.max)

    booked_appointments = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == id,
        models.Appointment.status == "BOOKED",
        models.Appointment.start_time >= start_of_day,
        models.Appointment.start_time <= end_of_day
    ).all()

    # Extract start times of booked slots
    booked_times = {app.start_time for app in booked_appointments}

    # 3. Generate all 30-minute slots between work_start_time and work_end_time
    available_slots = []
    current_time = datetime.combine(appointment_date, doctor.work_start_time)
    work_end_dt = datetime.combine(appointment_date, doctor.work_end_time)

    while current_time < work_end_dt:
        if current_time not in booked_times:
            available_slots.append(current_time.isoformat())
        current_time += timedelta(minutes=30)

    return available_slots