# DevOps Agent Backend

FastAPI backend with Claude API integration for AI-powered DevOps assistance.

## Features

- ✅ Claude API integration (Anthropic)
- ✅ Async FastAPI framework
- ✅ PostgreSQL database with SQLAlchemy
- ✅ Redis caching and session management
- ✅ Prometheus metrics
- ✅ Health checks and readiness probes
- ✅ Rate limiting
- ✅ CORS configuration
- ✅ Conversation history management

## Quick Start

### Local Development

```bash
# Install dependencies
poetry install

# Copy environment file
cp .env.example .env

# Edit .env and add your ANTHROPIC_API_KEY

# Run database (Docker)
docker run -d --name postgres -e POSTGRES_PASSWORD=changeme -p 5432:5432 postgres:16

# Run Redis (Docker)
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Update DATABASE_URL and REDIS_URL in .env to use localhost

# Run application
poetry run python -m app.main

# Or with uvicorn
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access

- API: http://localhost:8000
- Docs: http://localhost:8000/api/docs
- Health: http://localhost:8000/api/health
- Metrics: http://localhost:8000/metrics

## API Endpoints

### Health
- `GET /api/health` - Basic health check
- `GET /api/ready` - Readiness check
- `GET /api/health/detailed` - Detailed health with dependencies

### Chat
- `POST /api/chat/` - Send message to Claude
- `POST /api/chat/stream` - Stream response from Claude
- `DELETE /api/chat/conversation/{id}` - Delete conversation

### Users
- `GET /api/users/me` - Get current user info

## Environment Variables

See `.env.example` for all available configuration options.

**Required:**
- `ANTHROPIC_API_KEY` - Your Claude API key
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - Application secret key

## Testing

```bash
# Run tests
poetry run pytest

# With coverage
poetry run pytest --cov=app --cov-report=html
```

## Docker

```bash
# Build
docker build -t devops-agent-backend:latest -f ../../docker/Dockerfile.python .

# Run
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your-key \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  devops-agent-backend:latest
```

## Kubernetes Deployment

See `kubernetes/` directory in project root for deployment manifests.

## Architecture

```
app/
├── main.py              # FastAPI application entry
├── config.py            # Configuration settings
├── api/
│   ├── routes/
│   │   ├── chat.py      # Chat endpoints
│   │   ├── health.py    # Health checks
│   │   └── users.py     # User endpoints
│   └── dependencies.py  # Auth and dependencies
└── core/
    ├── claude.py        # Claude API client
    ├── database.py      # Database connection
    └── redis.py         # Redis connection
```

## Security

- Non-root container
- Read-only filesystem
- No privilege escalation
- Health checks configured
- Rate limiting enabled
- CORS properly configured
- Secrets via environment variables (Infisical in K8s)

## Monitoring

- Prometheus metrics at `/metrics`
- Structured logging
- Health checks for liveness and readiness
- Request tracing (optional with OpenTelemetry)

## License

Private - All rights reserved
