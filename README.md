# LeafyMind

> AI-powered guest concierge for [Leafy Cave](https://leafycave.com) — a luxury cabana retreat in Wellawaya, Sri Lanka.

LeafyMind guides international guests through their entire stay: building travel profiles, matching curated cabana packages, exploring Sri Lankan cuisine, generating personalised itineraries, downloading branded trip-plan PDFs, and collecting post-stay feedback. All recommendations are grounded in Leafy Cave business rules, a PostgreSQL knowledge base, and authentic Sri Lankan cultural context.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [AI Agents](#ai-agents)
- [Trip Pack](#trip-pack)
- [Project Structure](#project-structure)
- [API Overview](#api-overview)
- [Testing](#testing)
- [Production Notes](#production-notes)
- [Documentation](#documentation)
- [License](#license)

---

## Features

| Area | Capability |
|---|---|
| **Agent Hub** | Five guided specialists on `/hub` — profile → package → food → itinerary → feedback |
| **Classic Concierge** | Streaming chat at `/chat` with multi-phase orchestrator |
| **Package Matching** | Rule-based packages (`Love Nest Getaway`, `Together Time Package`, etc.) with custom names when no strong match |
| **Food Guide** | Must-try dishes, spice levels, local photos, Unsplash fallback |
| **Itinerary Planner** | Curated attractions and OpenTripMap discoveries near the cabana |
| **Trip Pack** | Branded PDF and optional email delivery after all three planners complete |
| **Owner Dashboard** | Flagged feedback and summaries at `/owner` (role: `owner`) |
| **Security** | JWT auth, bcrypt passwords, BFF rate limits, prompt sanitisation — see [SECURITY.md](SECURITY.md) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            Guest Browser                                 │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │  HTTP / WebSocket
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Frontend  (React 18 + Vite + Tailwind)             FRONTEND_PORT 5174  │
│  Landing · /hub · /agents/* · /chat · /owner                            │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │  /api/*  (VITE_API_BASE_URL)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  BFF  (Express)                                       BFF_PORT 3002      │
│  CORS · Helmet · rate limiting · reverse proxy · WebSocket chat          │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Backend  (FastAPI)                                BACKEND_PORT 8010     │
│  auth · agents · chat · recommendations · feedback · trip-pack           │
│  LangChain agents · FAISS knowledge base · Gmail SMTP · PDF (fpdf2)     │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
                          ┌──────────────────┐
                          │  PostgreSQL 15   │
                          │  POSTGRES_PORT   │
                          └──────────────────┘
```

**Request flow:** Browser → BFF → FastAPI → SQLAlchemy → PostgreSQL.

All LLM calls are routed through `backend/services/llm_provider.py`. Agents do not call each other directly — the orchestrator and `AgentRunner` handle all routing.

For full design details, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite 6, Tailwind CSS 3, Framer Motion, Axios |
| **BFF** | Node.js 20+, Express 4, express-rate-limit, http-proxy-middleware |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2 (async), LangChain, Groq (default LLM) |
| **Data** | PostgreSQL 15, FAISS, sentence-transformers |
| **Integrations** | Unsplash, OpenTripMap, Gmail SMTP |
| **DevOps** | Docker Compose |

---

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- *(Optional)* Node.js 20+ and Python 3.11+ for running services outside Docker

### 1. Clone and configure

```bash
git clone <your-repo-url> leafymind
cd leafymind
cp .env.example .env
```

Edit `.env` — the minimum required keys are `GROQ_API_KEY`, `JWT_SECRET`, and `POSTGRES_PASSWORD`.
Full setup checklist: [docs/EXTERNAL_SERVICES_SETUP.md](docs/EXTERNAL_SERVICES_SETUP.md)

### 2. Start the stack

```bash
docker compose up -d --build
```

```powershell
# Windows — print all service URLs from your .env ports
.\scripts\show-urls.ps1
```

### 3. Open the app

With default `.env.example` ports:

| Page | URL |
|---|---|
| Landing | http://localhost:5174/ |
| Agent Hub | http://localhost:5174/hub |
| Classic Chat | http://localhost:5174/chat |
| BFF Health | http://localhost:3002/health |
| Backend Health | http://localhost:8010/health |

### 4. Seed data *(recommended)*

```bash
docker exec leafymind-backend python -m scripts.seed_packages
docker exec leafymind-backend python -m scripts.seed_attractions
docker exec leafymind-backend python -m scripts.seed_food
```

### 5. Verify external services

```bash
docker exec leafymind-backend python -m scripts.verify_external_services
```

### Running without Docker

> PostgreSQL must be running locally. Set `DATABASE_URL` in `.env` to `localhost`.

```bash
# Backend
pip install -r requirements.txt
cd backend && uvicorn main:app --reload --port 8010

# BFF
cd bff && npm install && npm run dev

# Frontend
cd frontend && npm install && npm run dev
```

---

## Environment Variables

Copy [`.env.example`](.env.example) to `.env` and fill in the following:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Async PostgreSQL connection string |
| `JWT_SECRET` | JWT signing secret (minimum 32 characters) |
| `LLM_PROVIDER` | LLM provider name (default: `groq`) |
| `GROQ_API_KEY` | Groq API key for LLM chat |
| `UNSPLASH_ACCESS_KEY` | Food image fallback |
| `OPENTRIPMAP_API_KEY` | Itinerary attraction discovery |
| `GMAIL_SENDER_ADDRESS` | Gmail address for outbound emails |
| `GMAIL_APP_PASSWORD` | Gmail app password for SMTP |
| `FRONTEND_URL` | Guest app URL (used in links and image URLs) |
| `VITE_API_BASE_URL` | Browser-to-BFF base URL (e.g. `http://localhost:3002/api`) |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed browser origins |

---

## AI Agents

All agents are registered in `backend/agents/registry.py`. Hub agents use guided tap-through flows; the full concierge uses the streaming orchestrator.

| Agent | ID | Role |
|---|---|---|
| Profile Builder | `profile_builder` | 8-step guest profile *(required first)* |
| Package Planner | `package_recommender` | Rule-based cabana package matching |
| Food Guide | `food_guide` | Dish recommendations, spice levels, photos |
| Itinerary Planner | `itinerary_planner` | Day plans and nearby attraction discovery |
| Feedback Collector | `feedback_collector` | Post-stay ratings and comments |
| Full Concierge | `concierge` | Classic `/chat` multi-phase orchestration |

Business rules: `backend/rules/business_rules.py`
LLM gateway: `backend/services/llm_provider.py`

For full agent behaviour and journey details, see [docs/AGENT_HUB.md](docs/AGENT_HUB.md).

---

## Trip Pack

After all three planners (package, food, itinerary) complete, guests receive:

1. **Your Trip Pack** — a summary preview displayed in the Agent Hub.
2. **Download PDF** — a branded trip plan including profile, packages, food photos, and itinerary.
3. **Email My Plan** — sends the PDF on demand; requires an email on the guest profile and Gmail SMTP configured.

> The post-stay feedback survey email is sent separately after all three planners complete.

For full details, see [docs/TRIP_PACK.md](docs/TRIP_PACK.md).

---

## Project Structure

```
LeafyMind/
├── .cursorrules                    # Cursor AI rules (summary)
├── .cursor/rules/                  # Detailed Cursor rule files
├── .env.example                    # Environment variable template
├── docker-compose.yml              # Local development stack
├── requirements.txt                # → backend/requirements.txt
├── README.md
├── SECURITY.md
├── backend/
│   ├── agents/                     # Specialist agents and orchestrator
│   ├── api/                        # FastAPI routers
│   ├── models/                     # SQLAlchemy ORM models
│   ├── services/                   # LLM, email, PDF, journey, knowledge base
│   ├── rules/                      # Package matching business rules
│   ├── scripts/                    # Seeds, smoke tests, service verification
│   └── requirements.txt
├── bff/                            # Express reverse proxy
├── frontend/                       # React guest UI
│   └── public/images/food/         # Dish photos (mounted into backend)
├── db/migrations/                  # PostgreSQL schema (001–005)
├── docs/                           # Project documentation
└── scripts/show-urls.ps1           # Print local service URLs from .env
```

---

## API Overview

All guest-facing APIs are proxied through the BFF under `/api/*`. Authenticated routes require `Authorization: Bearer <jwt>`.

| Prefix | Example Endpoints |
|---|---|
| `/auth` | `POST /register`, `POST /login`, `GET /me` |
| `/agents` | `GET /journey`, `POST /{agent}/threads`, SSE message stream |
| `/chat` | `POST /session/start`, `POST /message` (SSE) |
| `/recommendations` | `GET /packages/{sessionId}`, `GET /food/`, `GET /itinerary/` |
| `/trip-pack` | `GET /summary`, `GET /pdf`, `POST /email` |
| `/feedback` | `POST /submit`, `GET /summary` *(owner only)* |

Full reference: [docs/API_REFERENCE.md](docs/API_REFERENCE.md)

---

## Testing

### Smoke tests

```bash
docker exec leafymind-backend python -m scripts.test_auth_smoke
docker exec leafymind-backend python -m scripts.test_agent_hub_flow
docker exec leafymind-backend python -m scripts.test_owner_dashboard
```

### Unit tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

Manual end-to-end test checklist: [docs/FULL_APP_TESTING_GUIDE.md](docs/FULL_APP_TESTING_GUIDE.md)

---

## Production Notes

Before any public deployment, update the following at minimum:

| Item | Action |
|---|---|
| `JWT_SECRET` | Set a strong, unique value (32+ characters) |
| `POSTGRES_PASSWORD` | Set a strong, unique value |
| `CORS_ALLOWED_ORIGINS` | Restrict to explicit production URLs only |
| `NODE_ENV` | Set to `production` |
| `FRONTEND_URL` | Set to the real guest domain |
| All API keys | Manage via a secrets manager — never commit `.env` |

**Promoting an owner account:**

```sql
UPDATE users SET role = 'owner' WHERE email = 'you@yourdomain.com';
```

**Rebuilding the FAISS knowledge base** after seeding new packages or attractions:

```bash
docker exec leafymind-backend python -m scripts.rebuild_kb
docker compose restart backend
```

**Viewing logs:**

```bash
docker compose logs -f backend
docker compose logs -f bff
docker compose logs -f frontend
```

---

## Documentation

| Document | Description |
|---|---|
| [docs/README.md](docs/README.md) | Documentation index |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, data flow, key modules |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | REST endpoints and authentication |
| [docs/AGENT_HUB.md](docs/AGENT_HUB.md) | Guided agents, journey flow, and artifacts |
| [docs/TRIP_PACK.md](docs/TRIP_PACK.md) | PDF download and email trip plan |
| [docs/EXTERNAL_SERVICES_SETUP.md](docs/EXTERNAL_SERVICES_SETUP.md) | API keys and Gmail SMTP setup |
| [docs/FULL_APP_TESTING_GUIDE.md](docs/FULL_APP_TESTING_GUIDE.md) | End-to-end test checklist |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Local development workflow and conventions |
| [SECURITY.md](SECURITY.md) | Auth model, rate limits, and vulnerability reporting |
| [frontend/public/images/food/README.md](frontend/public/images/food/README.md) | Food photo naming convention |

---

## License

Proprietary — Leafy Cave / LeafyMind. All rights reserved.
