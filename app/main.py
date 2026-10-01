from fastapi import FastAPI
from app.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sabala Clinic Booking System")

@app.get("/")
def read_root():
    return {"message": "Clinic Booking System API is running"}