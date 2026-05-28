# CAIMS — Local Deployment & Run Guide

**Project:** Corporate Asset & Inventory Management System (CAIMS)
**Stack:** Python · Django · PostgreSQL · Celery · Redis
**Goal:** Get the project running on your own machine for development and demo. No hosting.

This guide assumes the project has been built per `Implementation_Plan.md`. Follow the sections in order.

---

## 1. What You Need Installed

Install these on your machine before starting:

| Tool | Why | Notes |
|------|-----|-------|
| **Python 3.10+** | Runs Django | `python --version` to check |
| **PostgreSQL** | The database | Install the server + remember the password you set for the `postgres` user |
| **Redis** | Message broker for Celery background tasks | On Windows, use **Memurai** or run Redis in WSL/Docker (native Redis isn't built for Windows) |
| **Git** | Version control | Optional but expected for the assignment |

Quick checks after installing:
```bash
python --version
psql --version
redis-cli ping     # should reply: PONG
```

---

## 2. Get the Code & Create a Virtual Environment

```bash
# clone your repo (or cd into the project folder)
git clone <your-repo-url> caims
cd caims

# create and activate a virtual environment
python -m venv venv

# activate it:
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate
```

Install the dependencies:
```bash
pip install -r requirements.txt
```

Expected packages: `Django`, `psycopg2-binary`, `celery`, `redis`, `qrcode`, `Pillow`.

---

## 3. Create the PostgreSQL Database

Open the Postgres shell and create a database and user for the project:

```sql
-- log in first:  psql -U postgres

CREATE DATABASE caims_db;
CREATE USER caims_user WITH PASSWORD 'choose_a_password';
GRANT ALL PRIVILEGES ON DATABASE caims_db TO caims_user;
```

(On Postgres 15+, you may also need: `\c caims_db` then `GRANT ALL ON SCHEMA public TO caims_user;`)

---

## 4. Configure the Project Settings

Create a `.env` file in the project root (and make sure it's in `.gitignore` so it's never committed):

```
SECRET_KEY=any-long-random-string-for-dev
DEBUG=True
DB_NAME=caims_db
DB_USER=caims_user
DB_PASSWORD=choose_a_password
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
```

In `settings.py`, the database block should point at these values, for example:
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["DB_NAME"],
        "USER": os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": os.environ["DB_HOST"],
        "PORT": os.environ["DB_PORT"],
    }
}
```

For the demo, use Django's **console email backend** so the unreturned-asset reminder emails print to the terminal instead of needing a real mail server:
```python
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

---

## 5. Set Up the Database Tables & Admin User

```bash
python manage.py migrate          # create all tables
python manage.py createsuperuser  # create an Admin login
```

(Optional) load sample data if you have a fixture:
```bash
python manage.py loaddata sample_data.json
```

---

## 6. Run the Application

You'll need **three terminals**, each with the virtual environment activated. All three must be running for background tasks to work.

**Terminal 1 — the web server:**
```bash
python manage.py runserver
```
Open the app at: `http://127.0.0.1:8000/`
Django admin at: `http://127.0.0.1:8000/admin/`

**Terminal 2 — the Celery worker** (runs the background tasks):
```bash
celery -A caims worker -l info
```
*(On Windows, if the worker misbehaves, add `--pool=solo`.)*

**Terminal 3 — Celery Beat** (the scheduler that triggers the daily jobs):
```bash
celery -A caims beat -l info
```

---

## 7. Quick Start Checklist (every time you work on it)

1. Activate the virtual environment.
2. Make sure **PostgreSQL** is running.
3. Make sure **Redis** is running (`redis-cli ping` → `PONG`).
4. Start the **web server** (Terminal 1).
5. Start the **Celery worker** (Terminal 2).
6. Start **Celery Beat** (Terminal 3).
7. Log in at `http://127.0.0.1:8000/`.

---

## 8. Verifying It Works (for your demo)

| Feature | How to check |
|---------|--------------|
| Roles | Log in as each role; confirm each sees/does only what it should |
| QR codes | Open an asset; the QR image should display |
| Request workflow | As Employee, request an asset; as Asset Manager, approve it; confirm assignment is created |
| Return | Return an assigned asset; status flips back to Available |
| Depreciation | Asset detail page shows a current (depreciated) value |
| Audit trail | Movement actions appear in the audit log (visible to Auditor/Admin) |
| Low-stock task | Drop an item below its reorder level; the daily task reports it (watch the worker terminal) |
| Unreturned-asset email | An overdue assignment triggers a reminder email (printed in the worker terminal with the console backend) |

**Testing background tasks without waiting a day:** temporarily set the Celery Beat schedule to run every minute (or trigger the task by hand from the Django shell) so you can show it live during the demo, then change it back.

---

## 9. Common Problems & Fixes

| Problem | Likely cause / fix |
|---------|--------------------|
| `psycopg2` install fails | Use `psycopg2-binary` in `requirements.txt` |
| Django can't connect to DB | PostgreSQL not running, or wrong password/DB name in `.env` |
| `Connection refused` from Celery | Redis isn't running — start it / check `redis-cli ping` |
| Celery worker does nothing on Windows | Add `--pool=solo` to the worker command |
| QR image doesn't show | Confirm `Pillow` is installed and `MEDIA_URL`/`MEDIA_ROOT` are configured and served in dev |
| Static files (CSS) missing | In dev with `DEBUG=True` Django serves them automatically; if not, run `python manage.py collectstatic` |
| Emails not appearing | With the console backend they print in the terminal running the Celery worker, not the browser |

---

## 10. Stopping Everything

Press `Ctrl + C` in each of the three terminals. Deactivate the virtual environment with `deactivate`. PostgreSQL and Redis can be left running or stopped via your OS service manager.

---

## 11. Note on Scope

This is a **local development/demo setup only**, matching the semester project scope in `Implementation_Plan.md`. Production deployment — cloud/VPS hosting, Nginx + Gunicorn, HTTPS, process managers, scaling — is intentionally not covered, as it's beyond what the assignment requires.
