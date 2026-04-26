# Vehicle DIY Guide

AI-powered, step-by-step repair guides built from real repair manuals, YouTube transcripts, and community knowledge — tailored to your exact vehicle.

![Tech Stack](https://img.shields.io/badge/stack-FastAPI%20%7C%20Next.js%20%7C%20Claude%20AI%20%7C%20pgvector-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## What It Does

Enter your vehicle (year, make, model, engine) and describe what needs fixing. The app:

1. Searches repair manuals, YouTube tutorials, and community forums in parallel
2. Synthesizes everything into a vehicle-specific, step-by-step guide using Claude AI
3. Caches the guide in Postgres — repeat queries load instantly at $0 cost
4. Walks you through each step with an AI mechanic you can ask questions in real time

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.12, asyncio |
| AI | Claude Sonnet (guide synthesis), Claude Haiku (chat) |
| Database | PostgreSQL + pgvector |
| Sources | Tavily web search, YouTube Data API, Reddit (PRAW) |
| Infra (local) | Docker Compose |

## Features

- **Safety tiers** — repairs classified as green (cosmetic), yellow (mechanical), or red (safety-critical) with prominent warnings
- **Step-level confidence scoring** — each step shows how certain the AI is; low-confidence steps prompt manual verification
- **Torque specs** — highlighted in an amber banner so you can't miss them
- **AI chat** — ask "which bolt?" or "what does that look like?" without leaving the step
- **Smart caching** — first build costs ~$0.09 and takes 30–60s; every repeat user pays $0 and waits <1s
- **Model tiering** — Haiku for intent detection and chat, Sonnet only for synthesis (32% cost reduction)

## Project Structure

```
vehicle-diy-guide/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # FastAPI endpoints (guides, session)
│   │   ├── db/                  # Async SQLAlchemy + guide caching
│   │   ├── models/              # RepairGuide with pgvector embedding
│   │   ├── services/
│   │   │   ├── knowledge_builder/   # Source gathering + Claude synthesis
│   │   │   │   └── sources/         # Web, YouTube, Reddit, images
│   │   │   └── guide_session/       # Session state + AI chat
│   │   └── config.py
│   └── scripts/                 # CLI runner, batch test suite
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # Home — vehicle + repair input
│   │   ├── building/            # Animated build progress screen
│   │   ├── preflight/           # Safety check + tools/parts checklist
│   │   └── session/             # Step-by-step guide + AI chat
│   └── lib/
│       ├── api.ts               # API client
│       └── types.ts             # TypeScript interfaces
└── docker-compose.yml           # Postgres (pgvector) + Redis
```

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker Desktop

### API Keys needed

- `ANTHROPIC_API_KEY` — [console.anthropic.com](https://console.anthropic.com)
- `TAVILY_API_KEY` — [tavily.com](https://tavily.com)
- `YOUTUBE_API_KEY` — Google Cloud Console → YouTube Data API v3
- `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` — [reddit.com/prefs/apps](https://reddit.com/prefs/apps)

### Setup

```bash
# 1. Start the database
docker compose up -d

# 2. Backend
cd backend
cp .env.example .env          # fill in your API keys
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/guides/intent` | Classify user query (symptom vs repair) |
| POST | `/api/guides/build` | Build or fetch cached repair guide |
| POST | `/api/session/start` | Initialize a repair session |
| POST | `/api/session/chat` | Send message to AI mechanic |
| POST | `/api/session/next` | Advance to next step |
| GET | `/api/session/state/{id}` | Get current session state |

## Cost Model

| Event | Claude cost |
|---|---|
| First guide build (Sonnet synthesis) | ~$0.06–0.10 |
| Cache hit (repeat query) | $0.00 |
| Chat message (Haiku) | ~$0.001 |
| Intent detection (Haiku) | ~$0.0005 |

A popular repair (e.g. Toyota Camry oil change) gets built once and served free to every subsequent user.
