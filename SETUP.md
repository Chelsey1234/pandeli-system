# Pandeli Sales & Inventory Management System - Setup Guide

## Prerequisites

- **Python** 3.10 or higher
- **PostgreSQL** 12 or higher
- **pip** (Python package manager)

---

## Step 1: Clone/Extract the Project

```bash
cd c:\pandeli_system
```

---

## Step 2: Create Virtual Environment

```bash
python -m venv venv
```

**Activate the virtual environment:**
- **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`
- **Windows (CMD):** `venv\Scripts\activate.bat`
- **Linux/Mac:** `source venv/bin/activate`

---

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
DB_NAME=pandeli_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=127.0.0.1,localhost
```

---

## Step 5: Create PostgreSQL Database

1. Open PostgreSQL (pgAdmin or psql)
2. Create a new database named `pandeli_db`:

```sql
CREATE DATABASE pandeli_db;
```

Or via command line:
```bash
psql -U postgres -c "CREATE DATABASE pandeli_db;"
```

---

## Step 6: Run Migrations

```bash
python manage.py migrate
```

---

## Step 7: Create Default Admin Accounts

```bash
python manage.py create_default_admins
```

This creates:
- **Main Branch (Owner):** `admin_main` / `Pandeli@2025`
- **Production Admin:** `admin_production` / `Pandeli@2025`

To use a custom password:
```bash
python manage.py create_default_admins --password YourCustomPassword123
```

**Important:** Change these passwords after first login in production!

---

## Step 8: Collect Static Files (for production)

```bash
python manage.py collectstatic --noinput
```

---

## Step 9: Run the Development Server

```bash
python manage.py runserver
```

Open your browser: **http://127.0.0.1:8000/**

---

## Quick Start Summary

| Step | Command |
|------|---------|
| 1 | `cd c:\pandeli_system` |
| 2 | `python -m venv venv` |
| 3 | `.\venv\Scripts\Activate.ps1` (Windows) |
| 4 | `pip install -r requirements.txt` |
| 5 | Create `.env` with DB credentials |
| 6 | Create PostgreSQL database `pandeli_db` |
| 7 | `python manage.py migrate` |
| 8 | `python manage.py create_default_admins` |
| 9 | `python manage.py runserver` |

---

## Production Deployment

1. Set `DEBUG=False` in `.env`
2. Set a strong `SECRET_KEY`
3. Configure `ALLOWED_HOSTS` with your domain
4. Use a production WSGI server (e.g., Gunicorn + Nginx)
5. Serve static files via Nginx or CDN
6. Use HTTPS

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `psycopg2` install fails | Install PostgreSQL dev libraries, or use `psycopg2-binary` |
| Database connection error | Check `.env` DB credentials and that PostgreSQL is running |
| Static files not loading | Run `python manage.py collectstatic` |
| Login redirect loop | Ensure `LOGIN_URL` and `LOGIN_REDIRECT_URL` in settings |
| Prophet/ARIMA import error | Optional - forecasting falls back to moving average if not installed |

---

## Default Login Credentials

- **Main Branch (Owner):** `admin_main` / `Pandeli@2025`
- **Production Admin:** `admin_production` / `Pandeli@2025`
