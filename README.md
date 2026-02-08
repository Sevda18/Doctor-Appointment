# Doctor Appointment Booking API
 
A FastAPI-based REST API for managing doctor appointments, built with SQLAlchemy and SQLite.
 
## Features
 
- **User Authentication**: Register and login for clients, doctors, and admins
- **Doctor Management**: Doctor profiles with specialties, availability slots
- **Appointment Booking**: Patients can book, view, and cancel appointments
- **Reviews & Ratings**: Patients can review doctors
- **Favorites**: Save favorite doctors
- **Notifications**: In-app notifications for appointment updates
- **Admin Panel**: User and doctor management, specialty management
 
## Project Structure
 
```
Doctor-Appointment/
├── app/
│   ├── core/           # Authentication, security, dependencies
│   ├── models/         # SQLAlchemy models
│   ├── routers/        # API endpoints
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic (notifications)
│   ├── main.py         # FastAPI application
│   ├── db.py           # Database configuration
│   ├── config.py       # Settings
│   ├── seed.py         # Database seeding functions
│   └── startup.py      # Auto-seed on startup
├── alembic/            # Database migrations
├── tests/              # Unit tests
├── alembic.ini         # Alembic configuration
└── pyproject.toml      # Project dependencies
```
 
## Requirements
 
- Python 3.10+
- pip
 
## Installation
 
1. **Clone the repository**
 
   ```bash
   git clone https://github.com/Sevda18/Doctor-Appointment.git
   cd Doctor-Appointment
   ```
 
2. **Create a virtual environment**
 
   ```bash
   python -m venv venv
   ```
 
3. **Activate the virtual environment**
 
   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```
 
4. **Install dependencies**
 
   ```bash
   pip install -e .
   ```
 
   Or install dependencies directly:
 
   ```bash
   pip install fastapi uvicorn sqlalchemy alembic pydantic pydantic-settings python-jose passlib bcrypt python-multipart pytest pytest-cov httpx
   ```
 
## Configuration
 
Create a `.env` file in the project root (optional):
 
```env
DATABASE_URL=sqlite:///./app.db
AUTO_SEED=1
```
 
- `DATABASE_URL`: Database connection string (default: SQLite)
- `AUTO_SEED`: Set to `1` to auto-seed admin user and specialties on startup
 
## Database Setup
 
1. **Run database migrations**
 
   ```bash
   alembic upgrade head
   ```
 
2. **Seed initial data (optional)**
 
   If `AUTO_SEED=1` is set, the database will be seeded automatically on first run.
 
   Alternatively, run the seed scripts manually:
 
   ```bash
   # Seed admin user (admin@local / admin123)
   python seed_admin.py
 
   # Seed medical specialties
   python seed_specialties.py
   ```
 
## Running the Application
 
**Start the development server:**
 
```bash
uvicorn app.main:app --reload
```
 
The API will be available at: **http://127.0.0.1:8000**
 
**API Documentation:**
 
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
 
## Default Admin Credentials
 
After seeding, you can log in with:
 
- **Email:** `admin@local`
- **Password:** `admin123`
 
## API Endpoints Overview
 
| Endpoint                        | Method | Description                      | Auth Required |
| ------------------------------- | ------ | -------------------------------- | ------------- |
| `/auth/register-client`         | POST   | Register as a patient            | No            |
| `/auth/register-doctor`         | POST   | Register as a doctor             | No            |
| `/auth/login`                   | POST   | Login (email/username + password)| No            |
| `/me`                           | GET    | Get current user profile         | Yes           |
| `/doctors`                      | GET    | List all doctors                 | No            |
| `/doctors/{id}`                 | GET    | Get doctor details               | No            |
| `/doctors/{id}/slots`           | GET    | Get doctor's available slots     | No            |
| `/doctors/{id}/reviews`         | GET    | Get doctor reviews               | No            |
| `/appointments`                 | POST   | Book an appointment              | Yes (USER)    |
| `/appointments/mine`            | GET    | Get my appointments              | Yes (USER)    |
| `/doctor/me`                    | GET    | Get my doctor profile            | Yes (DOCTOR)  |
| `/doctor/slots`                 | GET/POST| Manage doctor slots             | Yes (DOCTOR)  |
| `/doctor/appointments`          | GET    | View received appointments       | Yes (DOCTOR)  |
| `/admin/users`                  | GET    | List all users                   | Yes (ADMIN)   |
| `/specialties`                  | GET    | List all specialties             | No            |
| `/health`                       | GET    | Health check                     | No            |
 
## Running Tests
 
**Run all tests:**
 
```bash
pytest
```
 
**Run tests with coverage:**
 
```bash
pytest --cov=app --cov-report=html
```
 
Coverage report will be generated in the `htmlcov/` directory.
 
**Run specific test file:**
 
```bash
pytest tests/test_auth.py -v
```
 
## User Roles
 
| Role   | Description                                      |
| ------ | ------------------------------------------------ |
| USER   | Patient - can book appointments, write reviews   |
| DOCTOR | Doctor - can manage slots, view/manage appointments |
| ADMIN  | Administrator - full access to all resources     |
 
## Tech Stack
 
- **Framework:** FastAPI
- **Database:** SQLAlchemy + SQLite (can be swapped for PostgreSQL/MySQL)
- **Migrations:** Alembic
- **Authentication:** JWT (python-jose) + OAuth2
- **Password Hashing:** bcrypt (passlib)
- **Validation:** Pydantic v2
- **Testing:** pytest + httpx
 
## License
 
This project is for educational purposes.