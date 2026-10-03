# Savannah Clinic Booking System

**Fly.io Deployment:**
* **Live API:** [https://savannah.fly.dev](https://savannah.fly.dev)  
* **Documentation:** [https://savannah.fly.dev/docs](https://savannah.fly.dev/docs)

**Render Deployment:**
* **Live API:** [https://savannah-9ijk.onrender.com](https://savannah-9ijk.onrender.com)  
* **Documentation:** [https://savannah-9ijk.onrender.com/docs](https://savannah-9ijk.onrender.com/docs)

A robust FastAPI microservice for managing appointment scheduling, doctor availability, cancellations, and rescheduling with persistent SQLite storage. Designed for containerized deployment and local development via Docker Compose.

---

## API Endpoints Summary

Below is an overview of the primary REST API endpoints available in the system. Full interactive documentation and schema definitions are available via the Swagger UI linked above.

### Doctors (`/doctors`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/doctors` | List all doctors and their metadata |
| `POST` | `/doctors` | Register a new doctor |
| `GET` | `/doctors/{doctor_id}/availability` | Get available booking slots for a specific doctor |

### Appointments (`/appointments`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/appointments` | Retrieve all appointments (supports filtering by doctor, patient, or date) |
| `POST` | `/appointments` | Book a new appointment (validates time slots & prevents overlaps) |
| `GET` | `/appointments/{appointment_id}` | Fetch details of a specific appointment |
| `PUT` | `/appointments/{appointment_id}/reschedule` | Reschedule an existing appointment to a new time slot |
| `PATCH` | `/appointments/{appointment_id}/cancel` | Cancel an appointment and immediately free the reserved time slot |

---

## Tech Stack & Architecture

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11)
* **ORM & Database:** [SQLAlchemy](https://www.sqlalchemy.org/) with [SQLite](https://www.sqlite.org/)
* **Validation & Schemas:** [Pydantic v2](https://docs.pydantic.dev/)
* **Testing:** [Pytest](https://docs.pytest.org/) & `httpx` (using in-memory SQLite `:memory:`)
* **Containerization:** Docker & Docker Compose
* **Hosting & Persistence:** Fly.io (Persistent Volumes) & Render
* **CI/CD:** GitHub Actions

---

## System Design & Double-Booking Prevention

### Architecture Strategy
The service follows a modular, layered architecture separating domain entities, API routing, database models, and validation logic:

    savannah/
    ├── app/
    │   ├── routers/
    │   │   ├── appointments.py  # Booking, cancellation, and rescheduling logic
    │   │   └── doctors.py       # Doctor availability and registration
    │   ├── database.py          # Dynamic SQLite connection & persistence setup
    │   ├── models.py            # SQLAlchemy database tables
    │   ├── schemas.py           # Pydantic request/response validation models
    │   └── main.py              # App initialization & router mounting
    ├── tests/
    │   └── test_appointments.py # Pytest test suite
    ├── .github/workflows/
    │   └── ci.yml               # Continuous Integration workflow
    ├── Dockerfile               # Production MicroVM container build instructions
    ├── docker-compose.yml       # Local multi-container development environment
    ├── fly.toml                 # Fly.io deployment and volume configurations
    ├── requirements.txt         # Application dependencies
    └── README.md

### Conflict Mitigation Strategy
To maintain absolute appointment integrity and prevent scheduling conflicts:
1. **Overlap Logic:** Before creating or rescheduling an appointment, the system evaluates active existing appointments for the requested doctor using strict boundary checking:
   `Overlap = (NewStart < ExistingEnd) AND (NewEnd > ExistingStart)`
2. **Atomic Status Check:** Cancelled appointments (`STATUS_CANCELLED`) are filtered out during conflict checking to ensure previously reserved time slots are freed immediately.

---

## Local Development & Quickstart

### Option 1: Running with Docker Compose (Recommended)

Run the full application environment locally in an isolated container matching the production environment:

    docker compose up --build -d

* **App Endpoint:** `http://localhost:8080`
* **Swagger API Docs:** `http://localhost:8080/docs`
* **Persistent Data:** Automatically persisted to `./data/clinic.db` in your local project root.

To stop the container:

    docker compose down

---

### Option 2: Running locally with Python

1. **Clone the repository:**
       git clone https://github.com/Simsade/savannah.git
       cd savannah

2. **Create and activate a virtual environment:**
       python -m venv .venv
       # Windows (PowerShell)
       .\.venv\Scripts\Activate.ps1
       # macOS / Linux
       source .venv/bin/activate

3. **Install dependencies:**
       pip install -r requirements.txt

4. **Start the FastAPI development server:**
       uvicorn app.main:app --reload --port 8080

5. **Access Interactive Docs:**
   Navigate to `http://localhost:8080/docs` in your browser.

---

## Running Unit Tests

Unit tests execute against an isolated, fast in-memory SQLite database (`sqlite:///:memory:`).

Run the full test suite locally:

    pytest -v

---

## Deployment & Persistence Strategy (Fly.io)

Since standard cloud containers feature ephemeral storage, local SQLite databases are usually reset upon container restarts. To solve this, the application is configured to store data securely on a **Fly.io Persistent Volume**.

### Storage Configuration
* **Mount Path:** `/var/data`
* **Database Target:** `/var/data/clinic.db`
* **Environment Variable:** `DATA_DIR=/var/data`

### Deploying to Fly.io

1. **Authenticate with Fly CLI:**
       fly auth login

2. **Create a Persistent Storage Volume:**
       fly volumes create clinic_sqlite_data --size 1

3. **Deploy the application:**
       fly deploy

---

## Continuous Integration (CI/CD)

The project includes an automated GitHub Actions pipeline (`.github/workflows/ci.yml`) that executes on every `push` and `pull_request` targeting the `main` branch.

**Workflow Steps:**
1. Code checkout.
2. Python environment setup (`3.11`).
3. Dependency installation (`requirements.txt`).
4. Automated test execution (`pytest -v`).

Deployments and merges are gated to ensure they are only permitted if all automated unit tests pass successfully.