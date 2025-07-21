# Selene Drive

A FastAPI service for controlling a lunar rover: landing, issuing move/rotate commands, and obstacle handling.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Local Setup](#local-setup)
- [Database Migrations](#database-migrations)
- [Running the Server](#running-the-server)
- [API Documentation](#api-documentation)
- [Testing & Coverage](#testing--coverage)
- [Continuous Integration (GitHub Actions)](#continuous-integration-github-actions)

---

## Prerequisites

- Docker & Docker Compose
- Python 3.13 (if running without Docker)
- Poetry
- Make sure ports **5432** and **8000** are available

---

## Environment Variables

Copy the example and adjust as needed:

```bash
cp .env.local .env
```

Key vars (in `.env` or your shell):

```env
API_V1_STR=/api/v1
START_POSITION=[0,0]
START_DIRECTION=NORTH

POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=database
POSTGRES_PORT=5432
POSTGRES_DB=selene-drive
```

---

## Local Setup

Build and run with Docker Compose:

```bash
docker-compose build
docker-compose up -d
```

This will start:
- PostgreSQL on port 5432
- Selene Drive API on port 8000

---

## Database Migrations

Migrations will apply automatically

---

## Running the Server (without Docker)

Change `.env` file to match local environment

```bash
poetry install
poetry run uvicorn main:app --reload
```

---

## API Documentation

Once the server is running, visit:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Testing & Coverage

Run tests and check coverage locally:

```bash
poetry run pytest --cov=. --cov-report=term-missing --cov-fail-under=75
```

---

## Continuous Integration (GitHub Actions)

Tests are run on each pull request using GitHub Actions.

Key CI steps:
- Linting with Ruff
- Test execution with coverage enforcement
- PostgreSQL containerized service

Workflow file: `.github/workflows/ci.yml`