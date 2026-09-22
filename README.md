# Social Network API

A social network backend built with FastAPI: stateless JWT authentication (RS256) with access/refresh token rotation, a chat domain with membership, roles and realtime messaging over WebSockets, and a SQLAdmin back office.

## Tech Stack

| Layer            | Technology                                      |
| ---------------- | ----------------------------------------------- |
| Runtime          | Python 3.14+, [uv](https://docs.astral.sh/uv/)  |
| Web framework    | FastAPI + Pydantic Settings                     |
| Database         | PostgreSQL (production) / SQLite (local)        |
| ORM & migrations | SQLAlchemy 2 (async), Alembic                   |
| Realtime         | WebSockets (FastAPI) + Redis Pub/Sub            |
| Authentication   | PyJWT (RS256), pwdlib (argon2)                  |
| CRUD layer       | FastCRUD                                        |
| Admin panel      | SQLAdmin                                        |
| Templates        | Jinja2                                          |
| Object storage   | aioboto3 (S3-compatible)                        |
| Logging          | structlog (structured JSON logs)                |
| Testing          | pytest, pytest-asyncio, Faker                   |
| Code quality     | ruff, pre-commit                                |

## Project Layout

```
src/
├── auth/               # Authentication domain
│   ├── router.py       #   /auth/* endpoints
│   ├── service.py      #   business logic
│   ├── repository.py   #   data access layer
│   ├── jwt.py          #   token issuing & validation
│   ├── depends.py      #   get_current_user dependency
│   ├── admin.py        #   SQLAdmin view for User
│   └── models.py       #   User model
├── chat/               # Chat domain
│   ├── routers/        #   chats, members, pages, ws (WebSocket)
│   ├── service.py      #   ChatService — WS lifecycle, Redis pub/sub, persistence
│   ├── repositories.py #   FastCRUD-backed data access
│   ├── models.py       #   Chat, ChatMember, Message
│   ├── schemas.py      #   *In / *Out schemas
│   └── enums.py        #   ChatType, ChatRole
├── admin/              # Admin panel wiring
│   ├── setup.py        #   SQLAdmin factory
│   ├── auth.py         #   admin authentication backend
│   ├── base.py         #   shared ModelView base
│   └── mixins.py       #   reusable view mixins
└── core/               # Application core
    ├── config.py       #   settings (env-driven)
    ├── database.py     #   async engine, Base, naming convention
    ├── redis.py        #   Redis client, cache and pub/sub wrappers
    ├── schemas.py      #   BaseSchema, DateTimeSchema
    ├── security.py     #   password hashing helpers
    ├── http.py         #   shared async HTTP client
    ├── s3.py           #   S3-compatible object storage client
    ├── templates.py    #   Jinja2 environment
    ├── logging.py      #   structlog configuration
    └── setup.py        #   app factory, middleware, admin, healthcheck
migrations/             # Alembic migrations
templates/              # Jinja2 templates
static/                 # Static assets, mounted at /static
tests/                  # pytest suite (auth, chat)
keys/                   # RSA key pair for JWT signing (never commit)
```

## Getting Started

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- OpenSSL (key generation)
- PostgreSQL 15+ (production mode)

### 1. Install dependencies

```bash
uv sync
```

### 2. Generate the JWT signing key pair

Tokens are signed with RS256. Generate a key pair and keep the private key secret:

```bash
mkdir -p keys
openssl genrsa -out keys/jwt-private.pem 2048
openssl rsa -in keys/jwt-private.pem -pubout -out keys/jwt-public.pem
```

> In production, provision keys through your secret manager and mount them read-only. Rotate them periodically — rotation invalidates all outstanding tokens.

### 3. Configure the environment

Copy the template and adjust the values (or export variables via your orchestrator):

```bash
cp .env.template .env
```

```env
# Application
IS_DEBUG=false
IS_DOCKERIZED=true

# CORS
ALLOW_CREDENTIALS=true
ALLOW_ORIGINS=["https://app.example.com"]
ALLOW_METHODS=["GET","POST","PUT","PATCH","DELETE"]

# PostgreSQL (used when IS_DOCKERIZED=true)
POSTGRES_DB=social_network
POSTGRES_USER=social_network
POSTGRES_PASSWORD=<strong-password>
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis (chat pub/sub)
REDIS_PORT=6379
REDIS_DB=0

# Admin panel (required — no default)
ADMIN_SECRET_KEY=<random-32-bytes>

# S3-compatible object storage
S3_ENDPOINT_URL=https://s3.example.com
S3_ACCESS_KEY=<key>
S3_SECRET_KEY=<secret>
S3_REGION=us-east-1
S3_BUCKET=social-network
```

Configuration reference:

| Variable            | Default      | Description                                              |
| ------------------- | ------------ | -------------------------------------------------------- |
| `IS_DEBUG`          | `true`       | Enables OpenAPI docs; disable in production              |
| `IS_DOCKERIZED`     | `false`      | `true` → PostgreSQL, `false` → local SQLite (`db.sqlite3`) |
| `ALLOW_CREDENTIALS` | — (required) | CORS: allow cookies/credentials                          |
| `ALLOW_ORIGINS`     | — (required) | CORS: allowed origins (JSON list)                        |
| `ALLOW_METHODS`     | — (required) | CORS: allowed HTTP methods (JSON list)                   |
| `POSTGRES_*`        | see config   | PostgreSQL connection parameters                         |
| `REDIS_PORT`, `REDIS_DB` | see config | Redis connection, used for chat pub/sub. Host is derived from `IS_DOCKERIZED` (`redis` vs `localhost`), not directly configurable |
| `ADMIN_SECRET_KEY`  | — (required) | Session signing key for the admin panel                  |
| `S3_*`              | — (required) | Object storage endpoint, credentials, region, bucket     |
| `TIMEOUT`, `CONNECT`, `MAX_CONNECTIONS`, `MAX_KEEPALIVE_CONNECTIONS`, `KEEPALIVE_EXPIRY` | see config | Shared async HTTP client tuning |

Token lifetimes and key paths are defined in `src/core/config.py` (`AuthSettings`). TLS verification for the shared HTTP client follows `IS_DEBUG`: it is disabled in debug mode and enabled otherwise.

### 4. Apply migrations

```bash
uv run alembic upgrade head
```

### 5. Run

Development (auto-reload):

```bash
uv run fastapi dev src/main.py
```

Production (behind a reverse proxy terminating TLS):

```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Interactive API docs are available at `/docs` only when `IS_DEBUG=true`.

## API Overview

### Authentication

| Method | Path             | Description                                          |
| ------ | ---------------- | ---------------------------------------------------- |
| POST   | `/auth/register` | Create an account → access token + refresh cookie    |
| POST   | `/auth/login`    | Authenticate with email/password                     |
| POST   | `/auth/refresh`  | Rotate the token pair using the refresh cookie       |
| POST   | `/auth/logout`   | Clear the refresh cookie                             |

### Chat

All chat endpoints require a valid access token.

| Method | Path                                  | Description                     |
| ------ | ------------------------------------- | ------------------------------- |
| POST   | `/chat`                               | Create a chat                   |
| GET    | `/chat`                               | List chats                      |
| GET    | `/chat/{chat_id}`                     | Chat detail with recent messages |
| PATCH  | `/chat/{chat_id}`                     | Update a chat                   |
| DELETE | `/chat/{chat_id}`                     | Delete a chat and its messages   |
| GET    | `/chat/{chat_id}/messages`            | Message history                 |
| POST   | `/chat/{chat_id}/members`             | Add a member                    |
| GET    | `/chat/{chat_id}/members`             | List members                    |
| GET    | `/chat/{chat_id}/members/{user_id}`   | Member detail                   |
| PATCH  | `/chat/{chat_id}/members/{user_id}`   | Change a member's role          |
| DELETE | `/chat/{chat_id}/members/{user_id}`   | Remove a member                 |

Members carry a role — `owner`, `admin` or `member` — and a chat is either `private` or `group`.
A user can join a chat only once; a duplicate returns `409`.

### Realtime (WebSocket)

| Protocol  | Path                  | Description                          |
| --------- | --------------------- | ------------------------------------- |
| WebSocket | `/chat/{chat_id}/ws`  | Join a chat and exchange messages live |

The access token is passed as a query parameter (`?token=<access_token>`), since browsers
cannot set custom headers on a WebSocket handshake. On connect, the socket auto-joins the
chat (creating a `ChatMember` row if one doesn't already exist) and subscribes to a Redis
channel shared by every member of that chat. Each frame sent over the socket is treated as
plain text: it's persisted as a `Message` (with `sender_id` resolved to the connection's
`ChatMember`) and published to the chat's Redis channel, which every connected member's
socket is listening on and forwards back out verbatim.

### Other

| Method | Path         | Description                                     |
| ------ | ------------ | ----------------------------------------------- |
| GET    | `/health`    | Liveness check (verifies database connectivity) |
| GET    | `/chat-page` | Server-rendered chat page (Jinja2)              |
| GET    | `/admin`     | SQLAdmin back office                            |

### Authentication model

- The **access token** is returned in the response body and must be sent as `Authorization: Bearer <token>`.
- The **refresh token** is stored in an `httponly`, `secure`, `samesite=strict` cookie and never exposed to client-side code.
- Every `/auth/refresh` call rotates both tokens.

## Database Migrations

```bash
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
```

## Testing

```bash
uv run pytest
```

Tests run against an in-memory SQLite database created from the SQLAlchemy metadata, so no
migrations or services are needed. Authentication tests do require the RSA key pair from
step 2. Fixtures live in `tests/conftest.py`; `tests/factories.py` builds request payloads
with Faker.

## Code Quality

```bash
uv run ruff check . --fix
uv run ruff format .
```

Pre-commit hooks are configured; enable them with:

```bash
uv run pre-commit install
```

## Production Checklist

- [ ] `IS_DEBUG=false` — OpenAPI schema is disabled
- [ ] RSA keys provisioned via secret manager, not committed
- [ ] `ALLOW_ORIGINS` restricted to trusted domains
- [ ] TLS terminated at the reverse proxy (refresh cookie is `secure`)
- [ ] Database migrations applied before rollout (`alembic upgrade head`)
- [ ] `ADMIN_SECRET_KEY` set to a strong random value and rotated separately from JWT keys
- [ ] `/admin` restricted at the network layer or behind SSO
- [ ] S3 credentials scoped to the single bucket the application uses
- [ ] `/health` wired to your orchestrator's liveness/readiness probes
