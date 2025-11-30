# DevOps Agent Frontend

Modern Next.js frontend with AI chat interface powered by Claude.

## Features

- ✅ Beautiful chat interface
- ✅ Real-time messaging with Claude AI
- ✅ Markdown rendering with syntax highlighting
- ✅ Conversation history
- ✅ Responsive design
- ✅ TailwindCSS styling
- ✅ TypeScript support

## Quick Start

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Update NEXT_PUBLIC_API_URL if needed

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Production Build

```bash
# Build
npm run build

# Start production server
npm start
```

## Docker

```bash
# Build
docker build -t devops-agent-frontend:latest -f ../../docker/Dockerfile.nextjs .

# Run
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=https://api.yourdomain.com \
  devops-agent-frontend:latest
```

## Environment Variables

- `NEXT_PUBLIC_API_URL` - Backend API URL (default: http://localhost:8000)

## Tech Stack

- Next.js 14 (App Router)
- React 18
- TypeScript
- TailwindCSS
- Axios
- React Markdown
- React Syntax Highlighter
- Heroicons

## License

Private - All rights reserved
