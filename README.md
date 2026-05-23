# LeafyMind

**AI-powered guest concierge for [Leafy Cave](https://leafycave.com)** — a luxury cabana retreat in Wellawaya, Sri Lanka.

> **Quest 2 portfolio:** [Case study](docs/CASE_STUDY.md) · [Submission checklist](docs/QUEST2_SUBMISSION_CHECKLIST.md) · _[Live demo URL]_ · _[Loom video]_


LeafyMind helps international guests plan stays through guided AI specialists: travel profiles, rule-based cabana packages, Sri Lankan food guides with photos, curated itineraries, branded trip-plan PDFs, and post-stay feedback. Recommendations are grounded in Leafy Cave business rules, PostgreSQL data, and Sri Lankan cultural context.

---

## Table of contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Quick start](#quick-start)
- [Documentation](#documentation)
- [Environment variables](#environment-variables)
- [AI agents](#ai-agents)
- [Trip pack (PDF & email)](#trip-pack-pdf--email)
- [Project structure](#project-structure)
- [API overview](#api-overview)
- [Testing](#testing)
- [Production notes](#production-notes)
- [License](#license)

---

## Features

| Area | Capability |
|------|------------|
| **Agent Hub** | Five guided specialists on `/hub` — profile → package → food → itinerary → feedback |
| **Classic concierge** | Streaming chat at `/chat` with multi-phase orchestrator |
| **Package matching** | Rule-based packages (`Love Nest Getaway`, `Together Time Package`, etc.) with custom names when no strong match |
| **Food guide** | Must-try dishes, spice levels, local photos (`frontend/public/images/food/`), Unsplash fallback |
| **Itinerary** | Curated attractions + OpenTripMap discoveries near the cabana |
| **Trip pack** | Branded PDF + optional email after all three planners complete |
| **Owner dashboard** | `/owner` for flagged feedback and summaries (role `owner`) |
| **Security** | JWT auth, bcrypt passwords, BFF rate limits, prompt sanitisation — see [SECURITY.md](SECURITY.md) |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Guest browser                                     │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │ HTTP / WebSocket
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  Frontend (React 18 + Vite + Tailwind)          FRONTEND_PORT (5174)      │
│  Landing · /hub · /agents/* · /chat · /owner                             │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │ /api/*  (VITE_API_BASE_URL)
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  BFF (Express)                                   BFF_PORT (3002→3001)     │
│  CORS · Helmet · rate limit · proxy · WS chat                             │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  Backend (FastAPI)                               BACKEND_PORT (8010)      │
│  auth · agents · chat · recommendations · feedback · trip-pack            │
│  LangChain agents · FAISS KB · Gmail SMTP · PDF (fpdf2)                   │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ PostgreSQL 15   │
                        │  POSTGRES_PORT  │
                        └─────────────────┘
```

**Request flow:** Browser → BFF → FastAPI → SQLAlchemy → PostgreSQL. All LLM calls go through `backend/services/llm_provider.py`. Agents do not call each other directly; the orchestrator and `AgentRunner` coordinate routing.

Detailed design: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Tech stack

| Layer | Technologies |
|-------|----------------|
| Frontend | React 18, Vite 6, Tailwind CSS 3, Framer Motion, Axios |
| BFF | Node.js 20+, Express 4, express-rate-limit, http-proxy-middleware |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2 (async), LangChain, Groq (default LLM) |
| Data | PostgreSQL 15, FAISS + sentence-transformers |
| Integrations | Unsplash, OpenTripMap, Gmail SMTP |
| DevOps | Docker Compose (local development) |

---

## Quick start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- (Optional) Node.js 20+ and Python 3.11+ for running services outside Docker

### 1. Clone and configure

```bash
git clone <your-repo-url> leafymind
cd leafymind
cp .env.example .env
```

Edit `.env` — minimum: `GROQ_API_KEY`, `JWT_SECRET`, `POSTGRES_PASSWORD`.  
Full checklist: [docs/EXTERNAL_SERVICES_SETUP.md](docs/EXTERNAL_SERVICES_SETUP.md)

### 2. Start the stack

```bash
docker compose up -d --build
```

```powershell
# Windows — print URLs from your .env ports
.\scripts\show-urls.ps1
```

### 3. Open the app

With default `.env.example` ports:

| Page | URL |
|------|-----|
| Landing | http://localhost:5174/ |
| Agent Hub | http://localhost:5174/hub |
| Classic chat | http://localhost:5174/chat |
| BFF health | http://localhost:3002/health |
| Backend health | http://localhost:8010/health |

### 4. Seed data (recommended)

```bash
docker exec leafymind-backend python -m scripts.seed_packages
docker exec leafymind-backend python -m scripts.seed_attractions
docker exec leafymind-backend python -m scripts.seed_food
```

### 5. Verify external services

```bash
docker exec leafymind-backend python -m scripts.verify_external_services
```

### Run without Docker

```bash
# PostgreSQL must be running; set DATABASE_URL in .env to localhost

pip install -r requirements.txt
cd backend && uvicorn main:app --reload --port 8010

cd bff && npm install && npm run dev

cd frontend && npm install && npm run dev
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/README.md](docs/README.md) | Documentation index |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, data flow, key modules |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | REST endpoints and auth |
| [docs/AGENT_HUB.md](docs/AGENT_HUB.md) | Guided agents, journey, artifacts |
| [docs/TRIP_PACK.md](docs/TRIP_PACK.md) | PDF download and email trip plan |
| [docs/EXTERNAL_SERVICES_SETUP.md](docs/EXTERNAL_SERVICES_SETUP.md) | API keys and Gmail setup |
| [docs/FULL_APP_TESTING_GUIDE.md](docs/FULL_APP_TESTING_GUIDE.md) | End-to-end test checklist |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Local dev workflow and conventions |
| [SECURITY.md](SECURITY.md) | Auth, rate limits, reporting vulnerabilities |
| [frontend/public/images/food/README.md](frontend/public/images/food/README.md) | Food photo naming |

---

## Environment variables

Copy [`.env.example`](.env.example) to `.env`. Critical variables:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Async PostgreSQL connection string |
| `JWT_SECRET` | JWT signing (≥ 32 chars) |
| `LLM_PROVIDER` / `GROQ_API_KEY` | Groq chat (default) |
| `UNSPLASH_ACCESS_KEY` | Food image fallback |
| `OPENTRIPMAP_API_KEY` | Itinerary discoveries |
| `GMAIL_SENDER_ADDRESS` / `GMAIL_APP_PASSWORD` | Trip plan + feedback emails |
| `FRONTEND_URL` | Guest app URL for links and image URLs |
| `VITE_API_BASE_URL` | Browser → BFF (`http://localhost:3002/api`) |
| `CORS_ALLOWED_ORIGINS` | Allowed browser origins |

---

## AI agents

Registered in `backend/agents/registry.py`. Hub agents use guided tap-through flows; the concierge uses the full orchestrator.

| Agent | ID | Role |
|-------|-----|------|
| Profile Builder | `profile_builder` | 8-step profile (required first) |
| Package Planner | `package_recommender` | Rule-based cabana packages |
| Food Guide | `food_guide` | Dishes, spice, photos |
| Itinerary Planner | `itinerary_planner` | Day plans + discoveries |
| Feedback Collector | `feedback_collector` | Post-stay ratings |
| Full Concierge | `concierge` | Classic `/chat` orchestration |

Business rules: `backend/rules/business_rules.py`  
LLM gateway: `backend/services/llm_provider.py`

Details: [docs/AGENT_HUB.md](docs/AGENT_HUB.md)

---

## Trip pack (PDF & email)

After **all three** planners (package, food, itinerary) complete:

1. Agent Hub shows **Your trip pack** with preview.
2. **Download PDF** — branded plan with profile, packages, food photos, itinerary.
3. **Email my plan (PDF)** — on-demand; requires email on profile + Gmail SMTP.

The feedback survey email is sent only after all three planners finish (separate from the trip plan PDF).

Details: [docs/TRIP_PACK.md](docs/TRIP_PACK.md)

---

## Project structure

```
LeafyMind/
├── .cursorrules              # Cursor AI rules (summary)
├── .cursor/rules/            # Detailed Cursor rule files
├── .env.example              # Environment template
├── docker-compose.yml        # Local dev stack
├── requirements.txt          # → backend/requirements.txt
├── README.md
├── SECURITY.md
├── backend/
│   ├── agents/               # Specialist agents + orchestrator
│   ├── api/                  # FastAPI routers
│   ├── models/               # SQLAlchemy ORM
│   ├── services/             # LLM, email, PDF, journey, KB
│   ├── rules/                # Package matching business rules
│   ├── scripts/              # Seeds, tests, verify_external_services
│   └── requirements.txt
├── bff/                      # Express proxy
├── frontend/                 # React guest UI
│   └── public/images/food/   # Dish photos (mounted into backend)
├── db/migrations/            # PostgreSQL schema (001–005)
├── docs/                     # Project documentation
└── scripts/show-urls.ps1     # Print local URLs from .env
```

---

## API overview

All guest APIs are prefixed by the BFF as `/api/*`. Authenticated routes require `Authorization: Bearer <jwt>`.

| Prefix | Examples |
|--------|----------|
| `/auth` | `POST /register`, `POST /login`, `GET /me` |
| `/agents` | `GET /journey`, `POST /{agent}/threads`, SSE message stream |
| `/chat` | `POST /session/start`, `POST /message` (SSE) |
| `/recommendations` | `GET /packages/{sessionId}`, `/food/`, `/itinerary/` |
| `/trip-pack` | `GET /summary`, `GET /pdf`, `POST /email` |
| `/feedback` | `POST /submit`, owner `GET /summary` |

Full reference: [docs/API_REFERENCE.md](docs/API_REFERENCE.md)

---

## Testing

```powershell
docker exec leafymind-backend python -m scripts.test_auth_smoke
docker exec leafymind-backend python -m scripts.test_agent_hub_flow
docker exec leafymind-backend python -m scripts.test_owner_dashboard
```

Manual E2E: [docs/FULL_APP_TESTING_GUIDE.md](docs/FULL_APP_TESTING_GUIDE.md)

```bash
cd backend && pip install -r requirements-dev.txt && pytest
```

---

## Production notes

Before any public deployment, change at minimum:

- `JWT_SECRET`, `POSTGRES_PASSWORD` — strong unique values
- `CORS_ALLOWED_ORIGINS` — explicit production URLs only
- `NODE_ENV=production`
- `FRONTEND_URL` — real guest domain
- All API keys via secrets manager (never commit `.env`)

**Owner account:** guests register as `guest`. Promote via SQL:

```sql
UPDATE users SET role = 'owner' WHERE email = 'you@yourdomain.com';
```

**Rebuild FAISS** after seeding new packages/attractions:

```bash
docker exec leafymind-backend python -m scripts.rebuild_kb
docker compose restart backend
```

**Logs:**

```bash
docker compose logs -f backend
docker compose logs -f bff
docker compose logs -f frontend
```

---

## License

Proprietary — Leafy Cave / LeafyMind. All rights reserved.
