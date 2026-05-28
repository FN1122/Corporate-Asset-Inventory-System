# CAIMS — Implementation Plan (Semester Project)

**Project:** Corporate Asset & Inventory Management System (CAIMS)
**Stack:** Python · Django · PostgreSQL · Celery · Redis · Django Templates
**Architecture:** Three-tier (Presentation / Application / Data)
**Scope:** Semester assignment — keep it focused, working, and demonstrable.

---

## 1. What This Project Must Do (Assignment Requirements)

A system for a large organisation to track physical assets (laptops, vehicles) and consumable inventory.

1. **Four roles:** Admin (system config), Asset Manager (approvals), Employee (requests), Auditor (view only).
2. **Enterprise complexity features:** depreciation logic, audit trails for asset movement, barcode/QR code generation.
3. **Background tasks:** daily report on low stock; automated emails for unreturned assets.

Everything in this plan maps back to one of those three points. Anything beyond them is intentionally left out to stay in scope (see §9).

---

## 2. Approach & Timeline

Built in **7 small phases**. Each phase leaves you with something that runs and can be shown in a demo. Build the data model and login/roles first (everything depends on them), then the features, then the two background tasks last.

| Phase | Focus | Est. Time |
|-------|-------|-----------|
| 0 | Project setup | 1 day |
| 1 | Data model & migrations | 2 days |
| 2 | Authentication & roles (4 roles) | 2 days |
| 3 | Asset & inventory management + QR codes | 3 days |
| 4 | Request / approval / assignment / return | 3 days |
| 5 | Depreciation + audit trail | 2 days |
| 6 | Celery + Redis background tasks | 2 days |
| 7 | Testing, polish, documentation | 2 days |

**Total estimate:** ~2.5–3 weeks of part-time work.

---

## 3. Phase 0 — Project Setup

**Goal:** A Django project that runs locally and is on GitHub.

Tasks:
1. Create a Git repo; add a `.gitignore` for Python/Django/venv/`.env`.
2. Create a virtual environment and a `requirements.txt`:
   - `Django`, `psycopg2-binary`, `celery`, `redis`, `qrcode`, `Pillow`.
3. Create the Django project and the apps you need:
   `accounts` (users + roles + auth), `assets`, `inventory`, `requests`, `audit`, `tasks`.
4. Connect Django to PostgreSQL; set the Redis URL for Celery.

**Deliverable:** `python manage.py runserver` works; DB connects.

---

## 4. Phase 1 — Data Model & Migrations

**Goal:** The database schema with sensible relationships.

Models:
- **User** — extend Django's built-in user; add a `role` field (Admin / Asset Manager / Employee / Auditor). Django handles password hashing for you.
- **AssetCategory** — `name`, `description`.
- **Asset** — `name`, `category` (FK), `purchase_date`, `purchase_cost`, `status` (Available / Assigned / Maintenance / Scrapped), `qr_code` image field. (`purchase_cost` is needed so depreciation can be calculated.)
- **Inventory** — `item_name`, `quantity_available`, `reorder_level`.
- **AssetRequest** — `employee` (FK User), `asset` (FK), `request_date`, `status` (Pending / Approved / Rejected).
- **AssetAssignment** — `asset` (FK), `employee` (FK), `assigned_date`, `return_date` (nullable). Tracks who has what and whether it's been returned.
- **DepreciationRecord** — `asset` (FK), `value`, `date_recorded`.
- **AuditLog** — `user` (FK, nullable), `action` (text), `timestamp`.

Tasks:
1. Write the models with foreign keys.
2. Run migrations; create a superuser; add a few sample categories/assets via the Django admin or a fixture.

**Deliverable:** All tables created; everything visible in Django admin.

---

## 5. Phase 2 — Authentication & Roles

**Goal:** Login that works, with the four roles controlling what each user can do.

Tasks:
1. Login / logout using Django's built-in auth views and templates.
2. Add a simple role check (a decorator or mixin like `@role_required("Admin")`) used on the views.
3. Map each role to what it can do:
   - **Admin:** manage users, categories, system config.
   - **Asset Manager:** approve/reject requests, manage inventory.
   - **Employee:** submit requests, view own assigned assets, return assets.
   - **Auditor:** view-only access to logs and reports.
4. Redirect users who aren't logged in; block users whose role isn't allowed.

**Deliverable:** Each role logs in and sees/does only what it should.

---

## 6. Phase 3 — Asset & Inventory Management + QR Codes

**Goal:** Register assets, track stock, generate QR codes.

Tasks:
1. Admin/Asset Manager pages to add and edit asset categories and assets.
2. Asset status (Available / Assigned / Maintenance / Scrapped).
3. **QR code generation:** when an asset is created, use the `qrcode` library to generate a QR image encoding the asset ID/name and save it to the asset. Display it on the asset detail page.
4. Inventory pages: add/edit items, update quantities, show which items are at/below their reorder level.

**Deliverable:** Assets created with scannable QR codes; inventory tracked with low-stock visible.

---

## 7. Phase 4 — Request / Approval / Assignment / Return

**Goal:** The core workflow employees and managers use.

Tasks:
1. **Employee** submits an asset request → status Pending.
2. **Asset Manager** approves or rejects. Key rules:
   - A user cannot approve their own request.
   - Only available assets can be approved/assigned.
3. On approval, create an **AssetAssignment** and set the asset's status to Assigned.
4. **Return:** when an asset is returned, record the `return_date` and set the asset back to Available. Keep the assignment record (needed for the unreturned-asset email task).

**Deliverable:** Full request → approve → assign → return flow works end to end.

---

## 8. Phase 5 — Depreciation Logic & Audit Trail

**Goal:** The two "enterprise complexity" features (besides QR codes).

Tasks:
1. **Depreciation logic:** a simple function that calculates an asset's current value from its `purchase_cost`, `purchase_date`, and a depreciation rate (e.g. straight-line over a set number of years). Show the current value on the asset page and store snapshots in `DepreciationRecord`.
2. **Audit trail for asset movement:** write an `AuditLog` entry whenever an asset changes hands or status — created, assigned, returned, sent to maintenance, scrapped. Record who did it and when.
3. A page (visible to Auditors and Admins) listing audit logs and an asset's movement history.

**Deliverable:** Depreciation values shown; every asset movement is logged and viewable.

---

## 9. Phase 6 — Background Tasks (Celery + Redis)

**Goal:** The two required scheduled jobs, running asynchronously.

Tasks:
1. Set up Celery with Redis as the broker; add Celery Beat for scheduling.
2. **Daily low-stock report:** a scheduled task that scans inventory for items at/below reorder level and produces a report (and/or emails it to managers) once a day.
3. **Unreturned-asset emails:** a scheduled task that finds assignments past their expected return (still no `return_date`) and emails a reminder.
4. Configure Django's email backend (console backend is fine for the demo; SMTP if you want real emails).

**Deliverable:** Both tasks run on a schedule without blocking the web app.

---

## 10. Phase 7 — Testing, Polish & Documentation

**Goal:** A clean, demo-ready submission.

Tasks:
1. A handful of tests for the important rules: can't approve own request, asset can't be assigned twice, low-stock detection, depreciation calculation.
2. Tidy up the templates so the dashboards and forms are usable.
3. Write a short **README**: how to set up, run the server, run Celery, and a one-paragraph description of each feature. Include an ER diagram if your course expects one.

**Deliverable:** Tested, documented, ready to submit and demo.

---

## 11. Deliverables Checklist

- [ ] Django project with the four roles working
- [ ] PostgreSQL schema + migrations
- [ ] Asset & inventory management screens
- [ ] QR/barcode generation for assets
- [ ] Request → approve → assign → return workflow
- [ ] Depreciation logic
- [ ] Audit trail for asset movement
- [ ] Daily low-stock report (Celery)
- [ ] Unreturned-asset reminder emails (Celery)
- [ ] README / documentation

---

## 12. Deliberately Out of Scope

To stay within the assignment, this project does **not** include the following (these were in an earlier expanded spec but go beyond what the assignment asks for):

- A full REST API layer / Django REST Framework — plain Django views and templates are enough.
- Production deployment (load balancers, horizontal scaling, AWS, Nginx/Gunicorn config).
- Production security hardening (HSTS, append-only DB roles, etc.) — Django's built-in defaults (password hashing, CSRF protection) are sufficient for a coursework demo.
- Separate dev/prod settings, pre-commit tooling, CI pipelines.
- Mobile app, external ERP/financial integrations, AI/analytics, IoT tracking.

Keeping these out is intentional — they add weeks of work without addressing any stated requirement.
