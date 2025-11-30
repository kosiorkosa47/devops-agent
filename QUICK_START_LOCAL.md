# 🚀 Quick Start - Local Development (5 minutes)

Fast local development setup to test the application before deploying to Kubernetes.

## Prerequisites

- Python 3.12+
- Node.js 20+
- Docker (for PostgreSQL and Redis)
- Claude API Key

## Step 1: Start Database Services (1 min)

```bash
# Start PostgreSQL
docker run -d --name postgres \
  -e POSTGRES_USER=devops \
  -e POSTGRES_PASSWORD=devops123 \
  -e POSTGRES_DB=devops_agent \
  -p 5432:5432 \
  postgres:16-alpine

# Start Redis
docker run -d --name redis \
  -p 6379:6379 \
  redis:7-alpine

# Verify
docker ps
```

## Step 2: Setup Backend (2 min)

```bash
cd apps/backend-python

# Install Poetry (if not installed)
pip install poetry

# Install dependencies
poetry install

# Create .env file
cp .env.example .env

# Edit .env and set:
# - ANTHROPIC_API_KEY=sk-ant-your-key-here
# - DATABASE_URL=postgresql+asyncpg://devops:devops123@localhost:5432/devops_agent
# - REDIS_URL=redis://localhost:6379/0

# Run backend
poetry run python -m app.main
```

Backend will start at: http://localhost:8000

Test it:
```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/docs  # Interactive API docs
```

## Step 3: Setup Frontend (2 min)

Open a new terminal:

```bash
cd apps/frontend

# Install dependencies
npm install

# Create .env.local
cp .env.example .env.local

# Edit .env.local:
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Run frontend
npm run dev
```

Frontend will start at: http://localhost:3000

## Step 4: Test It! 🎉

1. Open http://localhost:3000 in your browser
2. Type a message: "Hello! Can you help me with DevOps?"
3. Get response from Claude AI!

## What You Get

- ✅ Full chat interface with Claude AI
- ✅ Markdown rendering with code highlighting
- ✅ Conversation history (stored in Redis)
- ✅ Real-time messaging
- ✅ Beautiful modern UI
- ✅ Health checks and monitoring endpoints

## Common Commands

### Backend

```bash
# Run tests
poetry run pytest

# Format code
poetry run black app/

# Type checking
poetry run mypy app/

# Run with hot reload
poetry run uvicorn app.main:app --reload
```

### Frontend

```bash
# Development
npm run dev

# Build
npm run build

# Start production build
npm run build && npm start

# Lint
npm run lint
```

## Stopping Services

```bash
# Stop backend: Ctrl+C

# Stop frontend: Ctrl+C

# Stop Docker containers
docker stop postgres redis
docker rm postgres redis
```

## Troubleshooting

### Backend errors

```bash
# Check backend logs in terminal

# Common issues:
# - ANTHROPIC_API_KEY not set → Edit .env
# - Database connection failed → Check PostgreSQL is running
# - Redis connection failed → Check Redis is running

# Test database
psql postgresql://devops:devops123@localhost:5432/devops_agent -c "SELECT 1;"

# Test Redis
redis-cli ping
```

### Frontend errors

```bash
# Check frontend terminal for errors

# Common issues:
# - Backend not responding → Check backend is running on 8000
# - CORS errors → Check CORS_ORIGINS in backend .env
# - Module not found → Run npm install again
```

### Claude API not working

1. Verify API key in `apps/backend-python/.env`
2. Check backend logs for errors
3. Test API key:

```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Next Steps

Once everything works locally:

1. **Deploy to Kubernetes**: Follow [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. **Setup CI/CD**: Configure GitLab pipelines
3. **Enable monitoring**: Deploy Prometheus + Grafana
4. **Production secrets**: Use Infisical for secret management

## Development Tips

- Backend auto-reloads on code changes (with `--reload` flag)
- Frontend hot-reloads automatically
- Use `/api/docs` for interactive API testing
- Check `/api/health/detailed` for dependency status
- Logs are in the terminal - watch for errors

---

**Happy Coding! 🚀**

Need help? Check the full documentation or backend/frontend README files.
