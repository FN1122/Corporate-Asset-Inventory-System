# CAIMS — Corporate Asset & Inventory Management System

A role-based web application for tracking physical assets (laptops, vehicles)
and consumable inventory across an organisation. Built as a semester project.

**Stack:** Python · Django · PostgreSQL · Celery · Redis · Django Templates

---

## Features

- **Four roles** with role-gated access enforced server-side:
  - **Admin** — system configuration and user management
  - **Asset Manager** — manages assets/inventory, approves requests
  - **Employee** — requests assets, returns assets assigned to them
  - **Auditor** — read-only access to the audit trail
- **Asset management** — categories, status lifecycle (Available → Assigned →
  Maintenance → Scrapped), per-asset **QR codes** generated on creation
- **Inventory** — consumable stock tracking with reorder-level alerts
- **Request workflow** — Employee submits → Manager approves/rejects → asset
  is assigned → later returned. Business rules enforced in code and at the
  database level:
  - A user cannot approve their own request
  - The same asset cannot be assigned to two people at once
    (DB-level partial unique constraint)
  - Inventory quantity cannot go negative (DB `CheckConstraint`)
- **Depreciation logic** — straight-line depreciation with a default 5-year
  useful life; the current value is shown on every asset's detail page
- **Audit trail** — every significant action writes an append-only
  `AuditLog` entry; the log is read-only even through the admin
- **Background tasks** (Celery + Redis):
  - Daily low-stock report
  - Automated reminders for unreturned (overdue) assets

---

## Project Layout

```
caims/                  Django project (settings, root urls, celery app)
accounts/               Custom User model with role field + auth views
assets/                 Asset, AssetCategory, DepreciationRecord, QR generator
inventory/              Consumable inventory items
requests_app/           Request/approval/assignment/return workflow + services
audit/                  Append-only audit log + read-only viewer
tasks/                  Celery background tasks (low-stock report, reminders)
templates/              Shared templates (base, dashboard, login)
```

---

## How to Run the Project

There are two situations: setting it up on a machine for the first time, and
running it day-to-day once it's already set up. Pick the section you need.

> **Note:** all commands below use **PowerShell on Windows**. On macOS/Linux
> the only differences are forward-slash paths and `source venv/bin/activate`
> instead of `venv\Scripts\Activate.ps1`.

### A. First-time setup (fresh machine)

#### 1. Install the prerequisites

| Tool         | Notes                                                |
| ------------ | ---------------------------------------------------- |
| Python 3.10+ | <https://www.python.org/>                            |
| PostgreSQL   | <https://www.postgresql.org/download/> (15+)         |
| Redis        | On Windows use **Memurai** — <https://www.memurai.com/get-memurai> |
| Git          | <https://git-scm.com/>                               |

Verify they're all available:

```powershell
python --version
psql --version
memurai-cli ping       # should reply: PONG  (use `redis-cli ping` on Mac/Linux)
git --version
```

#### 2. Clone the repository and create a virtual environment

```powershell
git clone https://github.com/FN1122/Corporate-Asset-Inventory-System.git
cd Corporate-Asset-Inventory-System

python -m venv venv
venv\Scripts\Activate.ps1
```

You should now see `(venv)` at the start of the prompt.

#### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

#### 4. Create the PostgreSQL database

Open the Postgres shell (enter your `postgres` superuser password when prompted):

```powershell
psql -U postgres
```

Then at the `postgres=#` prompt, run:

```sql
CREATE DATABASE caims_db;
CREATE USER caims_user WITH PASSWORD 'your_password_here';
GRANT ALL PRIVILEGES ON DATABASE caims_db TO caims_user;
\c caims_db
GRANT ALL ON SCHEMA public TO caims_user;
ALTER DATABASE caims_db OWNER TO caims_user;
ALTER USER caims_user CREATEDB;     -- only needed if you want to run the test suite
\q
```

#### 5. Create the `.env` file

Create a file named `.env` in the project root (it's already in `.gitignore`,
so it never gets committed):

```env
SECRET_KEY=any-long-random-string
DEBUG=True
DB_NAME=caims_db
DB_USER=caims_user
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
```

#### 6. Run migrations and load demo data

```powershell
python manage.py migrate
python manage.py createsuperuser     # optional — for the Django admin
python manage.py seed_data
```

The `seed_data` command populates the database with sample categories,
assets, inventory items, an active and a returned assignment, and four demo
users (one per role).

---

### B. Everyday use (running the app)

Once setup is done, this is what you do each time you sit down to work.

#### 1. Make sure PostgreSQL and Redis (Memurai) are running

They normally start automatically with the OS. If something seems off, open
**Services** on Windows, find PostgreSQL and Memurai, and start them.

Quick sanity check:

```powershell
memurai-cli ping       # should return PONG
```

#### 2. Open three PowerShell windows

The app needs three processes running at once. In **each** window, first:

```powershell
cd "C:\Users\<your-user>\path\to\CAIMS"
venv\Scripts\Activate.ps1
```

Then run **one** of the following — one per window:

**Window 1 — Web server**

```powershell
python manage.py runserver
```

**Window 2 — Celery worker** (executes background tasks)

```powershell
celery -A caims worker -l info --pool=solo
```

> `--pool=solo` is required on Windows; Celery's default prefork pool doesn't
> work there.

**Window 3 — Celery Beat** (schedules the daily tasks)

```powershell
celery -A caims beat -l info
```

#### 3. Open the app

Go to **<http://127.0.0.1:8000/>** in a browser. You'll be redirected to the
login page.

#### 4. Log in

All demo accounts share the password **`demopass123`**:

| Username        | Role          | What they can do                                   |
| --------------- | ------------- | -------------------------------------------------- |
| `demo_admin`    | Admin         | Manage users, categories, system config            |
| `demo_manager`  | Asset Manager | Manage assets/inventory, approve/reject requests   |
| `demo_employee` | Employee      | Request assets, view & return assigned assets      |
| `demo_auditor`  | Auditor       | Read-only access to the audit log                  |

#### 5. To stop everything

Press `Ctrl + C` in each of the three windows.

---

### C. Triggering a background task manually (for demo)

The scheduled tasks normally run daily at 08:00 and 09:00. To see one fire
now, open a fourth window with the venv activated and run:

```powershell
python manage.py shell
```

Then at the `>>>` prompt:

```python
from tasks.tasks import daily_low_stock_report
daily_low_stock_report.delay()
```

Switch to the Celery worker window — you'll see the task arrive, the email
content print to the terminal (Django's console email backend), and a
"succeeded" line confirming it ran.

Type `exit()` to leave the shell.

---

## Running the tests

```powershell
python manage.py test
```

There are **11 tests** covering the core business rules: the self-approval
block, double-assignment prevention, depreciation math, inventory
non-negative, the return flow, and more.

> If you see *"permission denied to create database"*, run the
> `ALTER USER caims_user CREATEDB;` line from the setup section — Django
> needs to create a temporary test database.

---

## Common Problems

| Problem                                | Likely cause / fix                                                                  |
| -------------------------------------- | ----------------------------------------------------------------------------------- |
| `psycopg2` install fails               | Use `psycopg2-binary` (already in `requirements.txt`)                               |
| Django can't connect to the database   | PostgreSQL not running, or password/`.env` mismatch                                 |
| `Connection refused` from Celery       | Redis/Memurai isn't running — check `memurai-cli ping`                              |
| Celery worker hangs on Windows         | Make sure you used `--pool=solo`                                                    |
| QR image shows broken                  | Confirm `Pillow` is installed and `MEDIA_URL`/`MEDIA_ROOT` are configured           |
| `(venv)` not showing in prompt         | Re-run `venv\Scripts\Activate.ps1` from the project root                            |
| Background-task emails not visible     | They print in the **Celery worker** terminal, not the browser (console email backend) |

---

## Notes

- Emails use Django's **console email backend** in development, so the
  background-task emails print to the Celery worker terminal — no SMTP needed.
- QR codes are generated with the `qrcode` library and saved under `media/`.
- The audit log is append-only by design: even the Django admin disallows
  edits and deletes.
- A more detailed deployment walkthrough is in
  [`Deployment_Plan.md`](Deployment_Plan.md).

---

## Out of scope

In line with the project brief, the following are intentionally not
implemented: mobile app, external ERP/financial integrations, AI/analytics,
IoT tracking, production deployment (cloud hosting, load balancing, HSTS, etc.).
