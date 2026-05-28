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

## Running it locally

Full setup steps are in [`Deployment_Plan.md`](Deployment_Plan.md). Short version:

1. Install **Python 3.10+**, **PostgreSQL**, and **Redis** (Memurai on Windows).
2. Clone the repo, create a venv, and `pip install -r requirements.txt`.
3. Create a PostgreSQL database `caims_db` with a user `caims_user`.
4. Create a `.env` file in the project root (see "Environment variables" below).
5. Run the migrations and load demo data:
   ```bash
   python manage.py migrate
   python manage.py seed_data
   ```
6. Start three processes in three terminals (all with the venv activated):
   ```bash
   python manage.py runserver
   celery -A caims worker -l info --pool=solo
   celery -A caims beat -l info
   ```
7. Open <http://127.0.0.1:8000/> and log in.

### Environment variables (`.env`)

```
SECRET_KEY=<any long random string>
DEBUG=True
DB_NAME=caims_db
DB_USER=caims_user
DB_PASSWORD=<your password>
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
```

### Demo logins (created by `seed_data`)

All use the password **`demopass123`**:

| Username        | Role           |
|-----------------|----------------|
| `demo_admin`    | Admin          |
| `demo_manager`  | Asset Manager  |
| `demo_auditor`  | Auditor        |
| `demo_employee` | Employee       |

---

## Running the tests

```bash
python manage.py test
```

The tests cover the core business rules (self-approval block, double-assignment
prevention, depreciation math, inventory non-negative, return flow).

---

## Notes

- Emails use Django's **console email backend** in development, so the
  background-task emails print to the Celery worker terminal — no SMTP needed.
- QR codes are generated with the `qrcode` library and saved under `media/`.
- The audit log is append-only by design: even the Django admin disallows
  edits and deletes.

---

## Out of scope

In line with the project brief, the following are intentionally not
implemented: mobile app, external ERP/financial integrations, AI/analytics,
IoT tracking, production deployment (cloud hosting, load balancing, HSTS, etc.).
