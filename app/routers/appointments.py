from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("/", response_model=schemas.AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
    payload: schemas.AppointmentCreate,
    db: Session = Depends(get_db)
):
    """
    Book a 30-minute appointment slot.
    Validates doctor existence, working hours, and prevents double-booking.
    """
    # 1. Verify doctor exists
    doctor = db.query(models.Doctor).filter(models.Doctor.id == payload.doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Doctor not found"
        )

    # 2. Check if requested slot falls within working hours
    slot_time = payload.start_time.time()
    if slot_time < doctor.work_start_time or slot_time >= doctor.work_end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Requested time is outside the doctor's working hours"
        )

    # 3. Check for double-booking (active booking on the exact same slot)
    existing_appointment = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == payload.doctor_id,
        models.Appointment.start_time == payload.start_time,
        models.Appointment.status == "BOOKED"
    ).first()

    if existing_appointment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="This slot is already booked for the selected doctor"
        )

    # 4. Create appointment (automatically setting 30-minute duration)
    end_time = payload.start_time + timedelta(minutes=30)
    new_appointment = models.Appointment(
        doctor_id=payload.doctor_id,
        patient_id=payload.patient_id,
        start_time=payload.start_time,
        end_time=end_time,
        status="BOOKED"
    )

    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)
    return new_appointment


@router.patch("/{id}/cancel", response_model=schemas.AppointmentResponse)
def cancel_appointment(
    id: int,
    payload: schemas.AppointmentCancel,
    db: Session = Depends(get_db)
):
    """
    Cancel an active appointment with a reason and make the slot available again.
    """
    appointment = db.query(models.Appointment).filter(models.Appointment.id == id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Appointment not found"
        )

    if appointment.status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Appointment is already cancelled"
        )

    appointment.status = "CANCELLED"
    appointment.cancellation_reason = payload.cancellation_reason

    db.commit()
    db.refresh(appointment)
    return appointment


@router.patch("/{id}/reschedule", response_model=schemas.AppointmentResponse)
def reschedule_appointment(
    id: int,
    payload: schemas.AppointmentReschedule,
    db: Session = Depends(get_db)
):
    """
    Reschedule an existing active appointment to a new available slot.
    """
    appointment = db.query(models.Appointment).filter(models.Appointment.id == id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Appointment not found"
        )

    if appointment.status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Cannot reschedule a cancelled appointment"
        )

    # Check for double booking on the new slot
    conflict = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == appointment.doctor_id,
        models.Appointment.start_time == payload.new_start_time,
        models.Appointment.status == "BOOKED"
    ).first()

    if conflict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="The new slot is already booked"
        )

    appointment.start_time = payload.new_start_time
    appointment.end_time = payload.new_start_time + timedelta(minutes=30)

    db.commit()
    db.refresh(appointment)
    return appointment