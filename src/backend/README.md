# Crypto Portfolio Backend

FastAPI-based backend for the Cryptocurrency Portfolio Tracker DeFiers project.

## Tech Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 15+ with async SQLAlchemy 2.0
- **Cache/Sessions**: Redis 7+
- **Task Queue**: Celery 5.3+
- **Auth**: JWT (PyJWT), Passlib, pyotp
- **Language**: Python 3.11+

## Project Structure

```
app/
├── main.py              # FastAPI app factory and startup/shutdown
├── config.py            # Settings and environment configuration
├── database.py          # SQLAlchemy async engine and session
├── redis_client.py      # Redis client and SessionStore
├── jwt_manager.py       # JWT token creation and validation
├── deps.py              # FastAPI dependencies
├── tasks.py             # Celery background tasks
├── api/                 # API route handlers
│   ├── sessions.py      # Session management endpoints
│   └── ...other routers
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic request/response schemas
└── services/            # Business logic services
tests/
├── test_health.py       # Basic health check tests
└── ...test files
alembic/                 # Database migrations
```

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Installation

1. Install dependencies:
```bash
pip install -e ".[dev]"
```

2. Create `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

3. Update `.env` with your database and service credentials

### Database Setup

1. Create PostgreSQL database:
```sql
CREATE DATABASE crypto_portfolio;
```

2. Run migrations (when available):
```bash
alembic upgrade head
```

## Running

### Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
pytest
```

With coverage:
```bash
pytest --cov=app tests/
```

### Background Tasks (Celery)

In separate terminals:

```bash
# Celery worker
celery -A app.tasks worker --loglevel=info

# Celery beat (scheduler)
celery -A app.tasks beat --loglevel=info
```

## Key Features

### Session Management (US-001.4)

- **JWT-based authentication** with access/refresh tokens
- **Redis session store** with timeout management
- **Inactivity timeout**: 30 minutes (configurable)
- **Absolute TTL**: 24 hours (configurable)
- **Multi-device sessions**: Users can view and revoke sessions
- **Endpoints**:
  - `GET /api/auth/sessions` - List all active sessions
  - `POST /api/auth/logout` - Revoke current session
  - `POST /api/auth/sessions/{session_id}/revoke` - Revoke specific session
  - `POST /api/auth/logout-all` - Revoke all sessions

### Infrastructure (US-001.5)

- **Async database access** with connection pooling
- **Redis caching** for sessions and price data
- **Configuration management** via environment variables
- **Structured logging** with configurable levels
- **Health check endpoint** at `GET /health`
- **Graceful startup/shutdown** with lifespan management
- **CORS middleware** for frontend integration

## Environment Variables

See `.env.example` for all available options. Key ones:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/crypto_portfolio
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=your-secret-key-at-least-32-chars
SESSION_TIMEOUT_MINUTES=30
MAX_SESSION_TTL_HOURS=24
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

Run tests with pytest:

```bash
# All tests
pytest

# With coverage
pytest --cov=app

# Specific test file
pytest tests/test_health.py

# Async tests with verbose output
pytest -v --asyncio-mode=auto
```

## Security Notes

⚠️ **IMPORTANT for Production**:
- Change `JWT_SECRET_KEY` to a strong random value (use `openssl rand -hex 32`)
- Enable `DEBUG=false`
- Use strong database passwords
- Rotate `ENCRYPTION_MASTER_KEY` annually
- Use HTTPS only in production
- Configure CORS properly (don't use `allow_origins=["*"]`)
- Store secrets in a secure vault (AWS Secrets Manager, HashiCorp Vault, etc.)

## Deployment

Docker support coming soon. For now, use `pip install` with a virtual environment.

## Development

### Code Style

- Format with `black`
- Lint with `ruff`
- Type check with `mypy`

```bash
black app/ tests/
ruff check app/ tests/
mypy app/
```

### Adding New Endpoints

1. Create schema in `app/schemas/`
2. Create service logic in `app/services/`
3. Create router in `app/api/`
4. Include router in `app/main.py`
5. Add tests in `tests/`

## Contributing

Follow the structure above when adding new features. All new code must have tests with >95% coverage.

## Related Stories

- **US-001.4**: Session Timeout Management - Implemented
- **US-001.5**: Backend Infrastructure Setup - Implemented
- **US-001**: User Registration (frontend pending implementation)
- **US-002**: 2FA Implementation (backend ready)
- **US-003**: JWT Session Management (implemented)
