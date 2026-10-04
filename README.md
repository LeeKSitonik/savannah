# Savannah Clinic Booking System

**GitHub repository:**
(https://github.com/leesitonik/savannah.git)

**Fly.io Deployment:**
* **Live API:** (https://savannah.fly.dev)  
* **Documentation:** (https://savannah.fly.dev/docs)

**Render Deployment:**
* **Live API:** (https://savannah-9ijk.onrender.com)  
* **Documentation:** (https://savannah-9ijk.onrender.com/docs)
* **Storage Note:** Non-persistent database storage (ephemeral filesystem; database resets on container restarts).

A robust FastAPI microservice for managing appointment scheduling, doctor availability, cancellations, and rescheduling with persistent SQLite storage. Designed for containerized deployment and local development via Docker Compose.

---

## Section 1: System Design & Key Decisions

In designing the backend for the clinic, I prioritized simplicity, data integrity, and ease of deployment for a small-scale operation (5 doctors) while ensuring the architecture remains clean enough to scale later.

### Database Choice: SQLite
I opted for **SQLite** managed via SQLAlchemy. 
* **Reasoning:** For a starting clinic with only 5 doctors, spinning up a heavy, managed RDBMS like PostgreSQL introduces unnecessary cost and infrastructure overhead. SQLite is serverless, fast, and handles our expected read/write volume perfectly.
* **Trade-off:** The main drawback of SQLite in the cloud is that standard containers are temporary, meaning the database resets on every deployment. To solve this without migrating to a remote database, I mounted a **Fly.io Persistent Volume** (`/var/data`). This requires a slightly more complex deployment configuration but keeps the infrastructure light and completely free.

### Working-Hours & Slot Strategy
* **Slot Logic:** The prompt requires 30-minute slots. Instead of pre-generating thousands of "available slot" records in the database (which causes database bloat), I calculate availability dynamically. The system takes the doctor's working hours, generates all possible 30-minute blocks, queries the database for existing active appointments, and subtracts them to return the remaining free slots.
* **Working Hours Validation:** Doctors are mapped to standard clinic hours (e.g., 08:00 AM to 05:00 PM). The `POST /appointments` endpoint actively validates that requested times fall exactly on 30-minute boundaries (e.g., 09:00 or 09:30, never 09:15), are strictly within working hours, and are not in the past.
* **Cancellation Handling:** Cancelled appointments are flagged with a `STATUS_CANCELLED` state rather than hard-deleted. This preserves historical records but instantly frees up the time slot for new patient bookings.

### General Architectural Trade-Offs
* **Modular Monolith vs. Microservices:** I chose a modular monolith approach using FastAPI's `APIRouter`. Splitting this into microservices right now would be premature optimization. By keeping routes (`doctors.py`, `appointments.py`), schemas, and models isolated in their own files, the codebase stays organized and is easy to decouple in the future if the clinic grows rapidly.

---

## API Endpoints Summary

Below is an overview of the primary REST API endpoints available in the system. Full interactive documentation and schema definitions are available via the Swagger UI linked above.

### Doctors (`/doctors`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/doctors` | List all doctors and their metadata |
| `POST` | `/doctors` | Register a new doctor |
| `GET` | `/doctors/{doctor_id}/availability` | Get available 30-minute booking slots for a specific doctor |

### Appointments (`/appointments`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/appointments` | Retrieve all appointments (supports filtering by doctor, patient, or date) |
| `POST` | `/appointments` | Book a slot (validates working hours, past dates, and overlaps) |
| `GET` | `/appointments/{appointment_id}` | Fetch details of a specific appointment |
| `PUT` / `PATCH` | `/appointments/{appointment_id}/reschedule` | Reschedule an appointment to a new validated slot |
| `PATCH` | `/appointments/{appointment_id}/cancel` | Cancel an appointment with a reason and liberate the slot |

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

## Double-Booking Mitigation Strategy

To maintain absolute appointment integrity and prevent scheduling conflicts:
1. **Overlap Logic:** Before creating or rescheduling an appointment, the system evaluates active existing appointments for the requested doctor using strict boundary checking:
   `Overlap = (NewStart < ExistingEnd) AND (NewEnd > ExistingStart)`
2. **Atomic Status Check:** Cancelled appointments (`STATUS_CANCELLED`) are filtered out during conflict checking to ensure previously reserved time slots are freed immediately.

---

## Local Development & Quickstart

### Option 1: Running with Docker Compose.

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
       git clone https://github.com/leesitonik/savannah.git
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

Since standard cloud containers feature temporary storage, local SQLite databases are usually reset upon container restarts. To solve this, the application is configured to store data securely on a **Fly.io Persistent Volume**.

### Storage Configuration
* **Mount Path:** `/var/data`
* **Database Target:** `/var/data/clinic.db`
* **Environment Variable:** `DATA_DIR=/var/data`

---

## Continuous Integration & Continuous Deployment (CI/CD)

### What the Pipeline Does
The automated GitHub Actions workflow (`.github/workflows/ci.yml`) acts as an automated quality gate and deployment manager for the application:
1. **Checks out** the latest application codebase.
2. **Sets up** an isolated Python 3.11 environment.
3. **Installs** all project dependencies listed in `requirements.txt`.
4. **Executes** the full automated test suite (`pytest -v`).
5. **Deploys** the containerized application to Fly.io using the official `superfly/flyctl-actions` if all automated tests pass successfully.

### Deployment Trigger & Mechanisms
* **Trigger Branch:** The **`main`** branch.
* **How Deployment is Triggered:**
  * **Direct Pushes:** Any code pushed directly to the `main` branch automatically triggers the workflow, runs the test suite, and executes a production deployment to Fly.io.
  * **Pull Requests / Merges:** Opening a Pull Request targeting `main` triggers the CI test suite to verify changes. Once approved and merged into `main`, the pipeline runs and automatically triggers the production deployment using the `FLY_API_TOKEN` configured in GitHub Repository Secrets.

---

## Section 4: AI Reflection

### 1. What did you use AI for across the four sections?
* **Section 1 (System Design):** Brainstorming trade-offs between pre-generating 30-minute time slot records versus calculating availability dynamically on the fly.
* **Section 2 (API Implementation):** Generating boilerplate Pydantic validation schemas and Pytest test cases for boundary conditions (e.g., verifying past date rejection).
* **Section 3 (Deployment & CI/CD):** Writing the initial GitHub Actions `.github/workflows/ci.yml` syntax and mapping persistent volumes in Docker Compose.

### 2. Example of an AI suggestion that improved my work
One area where AI significantly improved my work was configuring the deployment environment so that my SQLite database wouldn't be wiped out. Because standard cloud containers have temporary file systems, my database was resetting every time the Fly.io container restarted. I understood the concept of persistent volumes but wasn't sure how to seamlessly map them in both Fly.io and a local Docker environment.

**Prompt:** *"I am deploying a FastAPI app using SQLite to Fly.io via a Dockerfile. How do I configure it so the database isn't erased on restart, and how can I turn this into a Docker Compose setup that mirrors the persistent storage locally?"*

**Outcome:** The AI provided the exact `[mounts]` configuration for my `fly.toml` to map to `/var/data`, and generated a `docker-compose.yml` file mounting a local `./data` folder to `/var/data`. This gave me a local environment mirroring production, saving hours of deployment trial-and-error.

### 3. Example where AI output was wrong/incomplete and how I caught it
When setting up the appointment overlap logic for rescheduling (`PATCH /appointments/{id}/reschedule`), the AI generated a basic query checking if a slot was occupied. However, it forgot to exclude the appointment being modified. As a result, attempting to reschedule an appointment to its existing time slot (or updating its metadata) threw a false-positive double-booking conflict error. 

**How I caught it:** I caught this while writing unit tests for the rescheduling endpoint. I manually fixed the query logic by adding `.filter(Appointment.id != appointment_id)` to ensure the current appointment is ignored during conflict checking.

### 4. Two decisions made without AI (and why I trusted my own judgment)
1. **Choosing SQLite + Fly Volume over PostgreSQL:** AI models almost always recommend PostgreSQL or Managed Cloud SQL for production backends by default. I deliberately chose SQLite with a Fly.io persistent volume to keep the application lightweight, serverless, and completely free of database hosting costs for a 5-doctor system.
2. **Dynamic Slot Generation over Database Row Generation:** Rather than creating a background job that populates thousands of available slot rows in the database for each doctor, I chose to calculate available slots on demand. I relied on my own judgment that this keeps the database clean, prevents state drift, and avoids bloat.