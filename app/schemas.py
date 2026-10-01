from pydantic import BaseModel
from datetime import datetime

class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    start_time: datetime

class AppointmentCancel(BaseModel):
    cancellation_reason: str

class AppointmentReschedule(BaseModel):
    new_start_time: datetime

class AppointmentResponse(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    start_time: datetime
    end_time: datetime
    status: str
    cancellation_reason: str | None = None

    class Config:
        from_attributes = True