# VIPCam - Barbearia VIP Face Analytics

Real-time facial analysis system for Barbearia VIP franchise units.

## Architecture

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0 async, PostgreSQL 16 + pgvector, Redis 7
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, Zustand, Recharts
- **GPU Pipeline**: YOLOv8x (person detection) → InsightFace buffalo_l (face recognition) → HSEmotion enet_b2_8 (emotion analysis)
- **Real-time**: WebSocket + Redis Pub/Sub

## Quick Start

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Start infrastructure
docker compose up -d db redis

# 3. Run migrations
cd backend && alembic upgrade head

# 4. Download AI models
bash scripts/download_models.sh

# 5. Seed cameras
python scripts/seed_cameras.py

# 6. Start backend
cd backend && uvicorn app.main:app --reload

# 7. Start frontend
cd frontend && npm run dev
```

## Development with Docker

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## Project Structure

```
vipcam/
├── backend/          # FastAPI + GPU processing pipeline
│   ├── app/
│   │   ├── api/      # REST + WebSocket endpoints
│   │   ├── models/   # SQLAlchemy ORM models
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── services/ # Business logic
│   │   └── pipeline/ # RTSP capture + ML inference
│   └── alembic/      # Database migrations
├── frontend/         # Next.js 14 dashboard
│   └── src/
│       ├── app/      # Pages (dashboard, cameras, people, analytics, settings)
│       ├── components/
│       ├── stores/   # Zustand state management
│       └── hooks/    # WebSocket hooks
├── scripts/          # Setup and seed scripts
└── docker-compose.yml
```
