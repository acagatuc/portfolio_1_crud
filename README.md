# Task Manager API

A production-ready REST API for managing projects and tasks. Built with FastAPI, PostgreSQL, SQLAlchemy, and JWT authentication.

## What It Is

This API allows users to register, authenticate, create projects, and manage tasks within those projects. It enforces strict user-level data isolation — users can only access and modify their own resources.

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.110+ |
| Database | PostgreSQL 15 |
| ORM | SQLAlchemy 2.0 (sync) |
| Validation | Pydantic v2 |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Testing | pytest + httpx (TestClient) |
| Containers | Docker + docker-compose |

## Project Structure

```
task_manager_api/
├── app/
│   ├── main.py           # FastAPI app, middleware, router registration
│   ├── config.py         # Pydantic-settings configuration
│   ├── database.py       # SQLAlchemy engine, session, Base
│   ├── dependencies.py   # Shared FastAPI dependencies (auth, db)
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic request/response schemas
│   ├── routers/          # Route handlers (thin layer, no business logic)
│   └── services/         # Business logic and DB operations
└── tests/
    ├── conftest.py        # Fixtures: client, auth headers, sample data
    ├── test_auth.py
    ├── test_projects.py
    └── test_tasks.py
```

## Running with Docker

### Prerequisites
- Docker and docker-compose installed

### Start the full stack

```bash
cd task_manager_api
docker-compose up --build
```

The API will be available at `http://localhost:8000`.

Interactive docs: `http://localhost:8000/docs`

### Stop and clean up

```bash
docker-compose down -v
```

## Running Locally (without Docker)

### Prerequisites
- Python 3.11+
- PostgreSQL running locally

### Setup

```bash
cd task_manager_api

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your local database credentials

# Create the database tables
python -c "from app.database import engine; from app.models import User, Project, Task; from app.database import Base; Base.metadata.create_all(bind=engine)"

# Start the development server
uvicorn app.main:app --reload
```

## Running Tests

Tests use a separate test database (`taskmanager_test` by default). Ensure PostgreSQL is running and the test database exists:

```bash
createdb taskmanager_test
```

Then run:

```bash
cd task_manager_api
pytest tests/ -v
```

To run a specific test file:

```bash
pytest tests/test_auth.py -v
pytest tests/test_projects.py -v
pytest tests/test_tasks.py -v
```

## API Endpoints

### Authentication

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login and receive JWT token |

### Projects (require Bearer token)

| Method | Path | Description |
|---|---|---|
| POST | `/projects` | Create a new project |
| GET | `/projects` | List all projects (pagination + status filter) |
| GET | `/projects/{id}` | Get a project with task counts by status |
| PATCH | `/projects/{id}` | Update project fields |
| DELETE | `/projects/{id}` | Delete a project (cascades to tasks) |

### Tasks (require Bearer token)

| Method | Path | Description |
|---|---|---|
| POST | `/projects/{project_id}/tasks` | Create a task in a project |
| GET | `/projects/{project_id}/tasks` | List tasks (pagination, status/priority filters, sort) |
| GET | `/tasks/{id}` | Get a single task |
| PATCH | `/tasks/{id}` | Update task fields |
| DELETE | `/tasks/{id}` | Delete a task |

### Live Swagger Docs

`http://localhost:8000/docs` — Interactive API documentation (available when the server is running)

## Response Format

All responses follow a consistent envelope structure:

**Single resource:**
```json
{
  "data": { ... },
  "message": "success"
}
```

**Paginated list:**
```json
{
  "data": [ ... ],
  "meta": {
    "total": 42,
    "page": 1,
    "per_page": 20,
    "total_pages": 3
  },
  "message": "success"
}
```

**Error:**
```json
{
  "detail": "Error description"
}
```

## Design Decisions

### Project Structure: Layered Architecture
Routers are kept thin — they validate input, call services, and return responses. All database queries and business logic live in the `services/` layer. This makes services independently testable and keeps the codebase easier to reason about as it grows.

### Authentication: Stateless JWT
JWT tokens are issued at login and verified on every protected request. No server-side session storage is required, making the API horizontally scalable. Token expiry is configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`. Passwords are hashed using bcrypt via passlib.

### Authorization: User-Scoped Resources
Every project belongs to a user via `user_id` foreign key. Every task belongs to a project. Before any project or task operation, the API verifies the authenticated user owns the relevant project, returning 403 Forbidden otherwise. This prevents any cross-user data leakage.

### Error Handling
- `401 Unauthorized` — Missing or invalid JWT token
- `403 Forbidden` — Authenticated but accessing another user's resource
- `404 Not Found` — Resource does not exist
- `422 Unprocessable Entity` — Request body validation failure (handled automatically by FastAPI/Pydantic)

### Testing Strategy
Tests use a real PostgreSQL test database (not mocks or SQLite) to ensure behavior matches production. Each test runs inside a transaction that is rolled back after the test, keeping tests isolated without needing to truncate tables. The `get_db` dependency is overridden via FastAPI's dependency injection system to use the test session.

### Cascade Deletes
Configured at the ORM level with `cascade="all, delete-orphan"` on relationships. Deleting a user removes all their projects; deleting a project removes all its tasks.
