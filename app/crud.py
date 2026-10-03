from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import Session
from app import models

def get_doctor_availability(db: Session, doctor_id: int, target_date: date):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        return None

    # Get all active (non-cancelled) bookings for this doctor on the target date
    booked_appointments = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == doctor_id,
        models.Appointment.status == "BOOKED",
        models.Appointment.start_time >= datetime.combine(target_date, time.min),
        models.Appointment.start_time <= datetime.combine(target_date, time.max)
    ).all()

    booked_times = {app.start_time for app.query in [booked_appointments]}

    # Generate candidate 30-minute slots between doctor's working hours
    current_slot = datetime.combine(target_date, doctor.work_start_time)
    end_slot = datetime.combine(target_date, doctor.work_end_time)

    available_slots = []
    while current_slot + timedelta(minutes=30) <= end_slot:
        if current_slot not in booked_times:
            available_slots.append(current_slot)
        current_slot += timedelta(minutes=30)

    return available_slots