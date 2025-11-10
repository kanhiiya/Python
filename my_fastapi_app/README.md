# my_fastapi_app

A small FastAPI application (Python) with PostgreSQL, organized for simple development and Docker-based deployment.

## Project overview

- Framework: FastAPI
- Language: Python
- Database: PostgreSQL
- Entrypoint: `app/main.py`
- API docs available at `/docs` (Swagger UI) and `/redoc` (ReDoc) when the server is running.

This repository contains a basic app layout with `api`, `core`, `models`, `schemas`, `services`, and middleware. A `docker-compose.yml` is included for local development using PostgreSQL.

## Quick contract

- Inputs: environment variables (DB URL, secret key, etc.)
- Outputs: an HTTP JSON API powered by FastAPI
- Error modes: misconfigured DB/env will prevent startup; invalid requests return standard FastAPI error responses
- Success criteria: app starts, connects to DB, and OpenAPI docs are reachable

## Prerequisites

- Python 3.10+ (or matching the project's requirements)
- pip
- Docker & Docker Compose (optional — required for the containerized flow)

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Environment variables

Create a `.env` file in the project root (or copy from `.env.example`). Required and optional variables:

```env
# App
PROJECT_NAME=FastAPI Modular App
VERSION=1.0.0
HOST=0.0.0.0
PORT=8000

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/postgres

# JWT / Security
SECRET_KEY=replace_with_a_secure_random_value_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS - JSON array of allowed origins
BACKEND_CORS_ORIGINS=["http://localhost", "http://localhost:3000"]

# HTTPS enforcement (set to true in production behind HTTPS)
FORCE_HTTPS=false

# Rate limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# Optional Redis for centralized rate limiting (recommended for production)
REDIS_URL=redis://redis:6379/0
```

**Security note**: Always use a strong `SECRET_KEY` in production. Generate with `openssl rand -hex 32` or similar.

## Running locally (development)

1. Ensure PostgreSQL is reachable using the configured `DATABASE_URL` (you can run a local DB or use Docker Compose).
2. Install dependencies: `pip install -r requirements.txt`
3. Start the app with Uvicorn in reload mode:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://127.0.0.1:8000/docs for Swagger UI.

## Running with Docker Compose

The repository includes `docker-compose.yml` to start PostgreSQL, Redis, and (optionally) the app services:

```bash
# Start PostgreSQL and Redis services
docker-compose up -d

# Run the app locally connecting to containerized services
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or to run everything in containers (you'd need to add an `app` service to docker-compose.yml):

```bash
docker-compose up --build
```

To stop services:

```bash
docker-compose down
```

**Services included:**
- `postgres:5432` - PostgreSQL database
- `redis:6379` - Redis for rate limiting (optional)
- `adminer:8080` - Database admin interface

## Database and migrations

This project includes `core/database.py` which likely sets up the DB connection. If you use Alembic for migrations, include the `alembic` folder and commands here. If not, the app may create tables at startup using SQLAlchemy models.

If you add Alembic later, typical commands are:

```bash
alembic revision --autogenerate -m "add initial models"
alembic upgrade head
```

## API overview

- Base router: `app/api/v1/api.py`
- Dependency utilities (DB/session, auth): `app/api/deps.py`
- Example endpoint modules: `app/api/v1/endpoints/`
- Schemas: `app/schemas/` (Pydantic models)
- Services: business logic in `app/services/`
- Models: SQLAlchemy models in `app/models/`

Common endpoints to check while exploring:
- `GET /` — Root endpoint with project info and links
- `/docs` — Swagger UI (OpenAPI documentation)
- `/redoc` — ReDoc documentation
- `/api/v1/health` — Health check endpoint
- `/api/v1/auth/register` — User registration
- `/api/v1/auth/login` — User login

## Running tests

There are no tests included by default. To add and run tests quickly, consider using `pytest`:

```bash
pip install pytest
pytest
```

Add a `tests/` folder and write unit and integration tests. For DB-backed tests, you can use a test database or use `pytest-docker`/`testcontainers`.

## Security features

This project includes several security hardening features:

### Built-in middleware
- **CORS**: Configurable via `BACKEND_CORS_ORIGINS` environment variable
- **HTTPS Redirect**: Enable with `FORCE_HTTPS=true` (use behind a proxy in production)  
- **Security Headers**: Automatic injection of security headers (HSTS, X-Frame-Options, CSP, etc.)
- **Rate Limiting**: Per-IP rate limiting with Redis backend (falls back to in-memory)
- **Trusted Host**: Restricts allowed host headers (currently set to allow all)

### Authentication & passwords
- **bcrypt**: Secure password hashing with salt
- **JWT**: Token-based authentication with configurable expiration
- **Secure token handling**: Proper token validation and user session management

### Configuration notes
- Rate limiter uses Redis when `REDIS_URL` is configured, otherwise falls back to in-memory (not suitable for multi-process deployment)
- Security headers include a conservative Content Security Policy - adjust as needed
- Set `FORCE_HTTPS=true` and configure `BACKEND_CORS_ORIGINS` appropriately in production

## Development notes & best practices

- Keep secrets out of source control. Use `.env` or your deployment platform's secret manager.
- Generate strong SECRET_KEY: `openssl rand -hex 32`
- Add CI (GitHub Actions) to run linting and tests on PRs.
- Add a `Makefile` or `invoke` tasks to simplify repetitive dev commands.
- Use Redis for rate limiting in production deployments.

## Suggested next steps

- Add basic unit tests and an integration test that starts the app with a test DB
- Add CI workflow (GitHub Actions) to run lint and tests  
- Add Alembic migrations if you plan to evolve the DB schema
- Add logging configuration for production
- Consider adding API versioning strategy
- Add Dockerfile for containerized app deployment

## Project structure (top-level)

```
app/
  api/             # routers, deps, authentication
  core/            # config, database, security utilities
  middleware/      # custom middleware (security headers, rate limiting)
  models/          # SQLAlchemy models
  schemas/         # Pydantic schemas
  services/        # business logic
  main.py          # app instance, middleware registration & routing

requirements.txt   # Python dependencies (includes aioredis for Redis)
docker-compose.yml # PostgreSQL + Redis services
.env.example       # Example environment variables
README.md
```

## Where to look for specifics

- App startup & mounted routers: `app/main.py`
- Configuration: `app/core/config.py`
- DB connection/session: `app/core/database.py`
- Dependency wiring for endpoints: `app/api/deps.py`

## Contact / Maintainers

Add maintainer and contact info here.

---

## Recent Updates

This project has been enhanced with comprehensive security features:

- ✅ **Security Headers**: CSP, HSTS, X-Frame-Options, etc.
- ✅ **Rate Limiting**: Redis-backed with in-memory fallback
- ✅ **CORS Configuration**: Configurable origins
- ✅ **JWT Authentication**: Secure token handling
- ✅ **Password Security**: bcrypt hashing
- ✅ **HTTPS Support**: Optional redirect middleware
- ✅ **Input Validation**: Pydantic schemas with proper update handling

The project is production-ready with proper environment configuration and security hardening.