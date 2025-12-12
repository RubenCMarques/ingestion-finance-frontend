Here is the **same full documentation** rewritten in **pure Markdown**, **no emojis**, and **no GPT-style annotations**.
Clean, professional, production-ready.

---

# Personal Finance Ingestion Platform — Full Documentation

This document explains every file, what it does, and how to modify it.
The goal is for you to fully understand the architecture so you can extend it freely.

---

# Project Structure

```
personal-finance-ingestion/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── templates/
│   │   └── index.html
│   └── static/
├── db/
│   └── init.sql
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

# High-Level Overview

The platform consists of:

### 1) A FastAPI ingestion app

* Receives transactions via `/transactions/`
* Serves a frontend HTML form at `/`
* Connects to a Postgres database

### 2) A PostgreSQL database

* Stores expense/income records
* Runs in a separate Docker container

### 3) A Docker Compose setup

* Spins up `app` + `db`
* Handles environment variables
* Creates a persistent database volume

---

# docker-compose.yml — Service Orchestration

### Purpose

Defines and manages the two containers: Postgres (`db`) and FastAPI (`app`).

### Key Features

* Creates a private Docker network
* Allows the app to connect to db using `DB_HOST=db`
* Persists data in `db_data`

### Common Modifications

* Change exposed ports
* Change DB credentials
* Add new services (dashboards, background workers, schedulers)

---

# Dockerfile — Building the FastAPI App Image

### Purpose

Defines how the FastAPI application container is built.

### Steps Performed

* Uses lightweight `python:3.12-slim`
* Installs system dependencies for PostgreSQL
* Installs Python requirements
* Copies the app source code
* Runs the app using `uvicorn`

### Modifications

* Add system-level dependencies if needed
* Change Python version
* Change the startup command if reorganizing the application

---

# requirements.txt — Python Dependencies

### Packages

* fastapi
* uvicorn[standard]
* SQLAlchemy
* psycopg2-binary
* python-dotenv
* jinja2
* python-multipart

### Modify When

* Adding new API features
* Using authentication or email validation
* Using database migration tools like Alembic

---

# app/database.py — Database Engine and Sessions

### Purpose

Creates:

* The database engine
* The session factory
* SQLAlchemy Base for model inheritance

### Key Behaviors

* Reads DB settings from environment variables
* Provides `get_db()` dependency to route handlers
* Controls connection lifecycle

### Safe Modifications

* Set `echo=True` to see SQL logs
* Change default DB settings
* Migrate to a new database system by adjusting `DATABASE_URL`

---

# app/models.py — SQLAlchemy ORM Models

### Purpose

Defines the database tables.

### Main Model: Transaction

Fields:

* id
* created_at
* type
* amount
* currency
* category
* sub_category
* payment_method
* source
* notes

### Modify When

* Adding new fields
* Changing column types or lengths
* Adding unique constraints or index definitions
* Renaming the table

If the database already has data, changes may require Alembic migrations.

---

# app/schemas.py — Pydantic Validation Models

### Purpose

Defines request and response schemas for validation.

### Schemas

#### TransactionBase

Shared attributes such as type, amount, category, etc.

#### TransactionCreate

Used for POST `/transactions/`.

#### TransactionRead

Returned when reading from the database, includes fields like `id` and `created_at`.

### Modify When

* Adding new request fields
* Changing validation rules
* Matching new database columns

---

# app/main.py — FastAPI Application and Routing

### Purpose

The central application entry point.

### Responsibilities

* Initialize FastAPI
* Auto-create tables on startup
* Configure Jinja2 template rendering
* Mount static files
* Define API routes

### Main Routes

#### GET `/`

Serves the HTML form.

#### GET `/health`

Health check.

#### POST `/transactions/`

Creates a new transaction.

#### GET `/transactions/`

Returns all transactions stored in the database.

### Modify When

* Adding filtering, editing, deleting
* Adding authentication
* Splitting routers into modules

---

# app/templates/index.html — Web UI

### Purpose

Simple HTML interface for manually inserting expenses or income.

### Features

* Form with all transaction fields
* JavaScript POST submission
* Responsive layout

### Modify When

* Adding UI fields
* Improving layout with Tailwind, Bootstrap, etc.
* Adding charts or summary pages

---

# app/static/ — Static Assets

Currently empty.
Place CSS, JS, or images here.

---

# db/init.sql — Initial Database Script

### Purpose

Executed only on the first startup of the database container.

Useful for:

* Creating predefined categories
* Creating seed tables
* Adding indexes not managed by SQLAlchemy
* Adding constraints

Note: SQLAlchemy already creates your main table automatically.

---

# How Everything Works Together

### Flow of Submitting a Transaction

1. User opens `http://localhost:8000`
2. Fills form and clicks Save
3. JavaScript sends POST to `/transactions/`
4. FastAPI validates via `TransactionCreate`
5. SQLAlchemy inserts into Postgres
6. Database commits
7. API returns a TransactionRead JSON
8. Records are viewable via GET `/transactions/`

---

# Development Workflow

### Build and Run

```
docker compose build
docker compose up
```

### View Logs

```
docker compose logs app
docker compose logs db
```

### Rebuild After Code Changes

```
docker compose build
docker compose up
```

---

# Future Extensions

### Security

* API keys or tokens
* Basic Authentication
* OAuth2

### Data Ingestion

* CSV upload
* Email parsing
* Scheduled ingestion
* Bank API imports

### Database Improvements

* Alembic migrations
* New tables (budgets, limits, merchants)

### Dashboards

* Metabase container
* Superset container
* Streamlit dashboard
* Cloud-hosted BI solutions

