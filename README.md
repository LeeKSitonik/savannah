
# Savannah Clinic Booking System 

A robust, compliant FastAPI microservice for managing appointment scheduling, doctor availability, cancellations, and rescheduling with persistent SQLite storage. Designed for containerized deployment on Fly.io and local development via Docker Compose.

---

##  API Endpoints Summary

Below is an overview of the primary REST API endpoints available in the system. Full interactive documentation and schema definitions are available via Swagger UI at `/docs`.

### Doctors (`/doctors`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/doctors` | List all doctors and their metadata |
| `POST` | `/doctors` | Register a new doctor |
| `GET` | `/doctors/{doctor_id}/availability` | Get available booking slots for a specific doctor |

### Appointments (`/appointments`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/appointments` | Retrieve all appointments (supports filtering by doctor/patient/date) |
| `POST` | `/appointments` | Book a new appointment (validates time slots & prevents overlaps) |
| `GET` | `/appointments/{appointment_id}` | Fetch details of a specific appointment |
| `PUT` | `/appointments/{appointment_id}/reschedule` | Reschedule an existing appointment to a new time slot |
| `PATCH` | `/appointments/{appointment_id}/cancel` | Cancel an appointment and liberate the reserved time slot |

---

##  Tech Stack & Architecture

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11)
* **ORM & Database:** [SQLAlchemy](https://www.sqlalchemy.org/) with [SQLite](https://www.sqlite.org/)
* **Validation & Schemas:** [Pydantic v2](https://docs.pydantic.dev/)
* **Testing:** [Pytest](https://docs.pytest.org/) & `httpx` (using in-memory SQLite `:memory:`)
* **Containerization:** Docker & Docker Compose
* **Hosting & Persistence:** Fly.io with Persistent Volumes mounted at `/var/data`
* **CI/CD:** GitHub Actions (`.github/workflows/ci.yml`)

---

##  System Design & Double-Booking Prevention

### Architecture Strategy
The service follows a modular, layered architecture separating domain entities, API routing, database models, and validation logic:

```text
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

```

### Double-Booking Mitigation Strategy

To maintain absolute appointment integrity and prevent scheduling conflicts:

1. **Overlap Logic:** Before creating or rescheduling an appointment, the system evaluates active existing appointments for the requested doctor:

$$\text{Overlap} \iff (\text{NewStart} < \text{ExistingEnd}) \land (\text{NewEnd} > \text{ExistingStart})$$


2. **Atomic Status Check:** Cancelled appointments (`STATUS_CANCELLED`) are filtered out during conflict checking to allow previously reserved time slots to be freed immediately.

---

## 🚀 Local Development & Quickstart

### Option 1: Running with Docker Compose (Recommended)

Run the full application environment locally in an isolated container matching production:

```bash
docker compose up --build -d

```

* **App Endpoint:** `http://localhost:8080`
* **Swagger API Docs:** `http://localhost:8080/docs`
* **Persistent Data:** Automatically persisted to `./data/clinic.db` in your local project root.

To stop the container:

```bash
docker compose down

```

---

### Option 2: Running locally with Python

1. **Clone the repository:**
```bash
git clone [https://github.com/Simsade/savannah.git](https://github.com/Simsade/savannah.git)
cd savannah

```


2. **Create and activate a virtual environment:**
```bash
python -m venv .venv
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

```


3. **Install dependencies:**
```bash
pip install -r requirements.txt

```


4. **Start the FastAPI development server:**
```bash
uvicorn app.main:app --reload --port 8080

```


5. **Access Interactive Docs:**
Navigate to `http://localhost:8080/docs` in your browser.

---

## 🧪 Running Unit Tests

Unit tests execute against an isolated, fast in-memory SQLite database (`sqlite:///:memory:`).

Run the full test suite locally:

```bash
pytest -v

```

---

## ☁️ Deployment & Persistence Strategy (Fly.io)

Since standard cloud containers feature ephemeral storage, SQLite databases are reset upon container restarts. To address this, the application is configured to store data on a **Fly.io Persistent Volume**.

### Storage Configuration

* **Mount Path:** `/var/data`
* **Database Target:** `/var/data/clinic.db`
* **Environment Variable:** `DATA_DIR=/var/data`

### Deploying to Fly.io

1. **Authenticate with Fly CLI:**
```bash
fly auth login

```


2. **Create a Persistent Storage Volume:**
```bash
fly volumes create clinic_sqlite_data --size 1

```


3. **Deploy the application:**
```bash
fly deploy

```



---

## 🔄 CI/CD Pipeline

The project includes an automated GitHub Actions pipeline (`.github/workflows/ci.yml`) that executes on every `push` and `pull_request` targeting the `main` branch.

**Workflow Steps:**

1. Code checkout.
2. Python environment setup (`3.11`).
3. Dependency installation (`requirements.txt`).
4. Automated test execution (`pytest -v`).

Deployments are only permitted if all automated unit tests pass green.

---

## 📄 License

This project is open-source and available under the [MIT License](https://www.google.com/search?q=LICENSE).

```

```