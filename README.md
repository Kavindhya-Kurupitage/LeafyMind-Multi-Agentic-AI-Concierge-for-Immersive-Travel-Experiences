<div align="center">

<!-- BANNER -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=200&section=header&text=LeafyMind&fontSize=80&fontColor=fff&animation=twinkling&fontAlignY=35&desc=AI-Powered%20Guest%20Concierge%20for%20Leafy%20Cave&descAlignY=60&descSize=18" width="100%"/>

<<<<<<< HEAD
<!-- BADGES ROW 1 -->
<p>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black"/>
  <img src="https://img.shields.io/badge/LangChain-Enabled-1C3C3C?style=for-the-badge&logo=chainlink&logoColor=white"/>
  <img src="https://img.shields.io/badge/Groq-LLM-F55036?style=for-the-badge&logo=groq&logoColor=white"/>
</p>

<!-- BADGES ROW 2 -->
<p>
  <img src="https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white"/>
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/Tailwind_CSS-3-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white"/>
  <img src="https://img.shields.io/badge/FAISS-Vector_Search-FF6B35?style=for-the-badge&logo=meta&logoColor=white"/>
  <img src="https://img.shields.io/badge/JWT-Auth-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white"/>
</p>

<!-- STATUS BADGES -->
<p>
  <img src="https://img.shields.io/badge/Status-Active_Development-brightgreen?style=flat-square"/>
  <img src="https://img.shields.io/badge/License-Proprietary-red?style=flat-square"/>
  <img src="https://img.shields.io/badge/Location-Wellawaya%2C_Sri_Lanka-orange?style=flat-square&logo=googlemaps&logoColor=white"/>
  <img src="https://img.shields.io/badge/AI_Agents-6_Specialists-purple?style=flat-square"/>
</p>

<br/>

> 🌿 **LeafyMind** is an intelligent guest concierge built for [Leafy Cave](https://leafycave.com), a luxury cabana retreat nestled in the heart of Wellawaya, Sri Lanka.  
> It guides international guests through every step — from arrival planning to post-stay feedback — using specialised AI agents, rule-based intelligence, and deep Sri Lankan cultural context.

<br/>

[🚀 Quick Start](#-quick-start) &nbsp;·&nbsp; [🏗️ Architecture](#️-architecture) &nbsp;·&nbsp; [🤖 AI Agents](#-ai-agents) &nbsp;·&nbsp; [📖 Docs](#-documentation) &nbsp;·&nbsp; [🔒 Security](SECURITY.md)

</div>
=======
> **Quest 2 portfolio:** [Case study](docs/CASE_STUDY.md) · [Submission checklist](docs/QUEST2_SUBMISSION_CHECKLIST.md) · _[Live demo URL]_ · _[Loom video]_


LeafyMind helps international guests plan stays through guided AI specialists: travel profiles, rule-based cabana packages, Sri Lankan food guides with photos, curated itineraries, branded trip-plan PDFs, and post-stay feedback. Recommendations are grounded in Leafy Cave business rules, PostgreSQL data, and Sri Lankan cultural context.


---

## 📋 Table of Contents

- [✨ Features](#-features)
- [🏗️ Architecture](#️-architecture)
- [🧰 Tech Stack](#-tech-stack)
- [🚀 Quick Start](#-quick-start)
- [⚙️ Environment Variables](#️-environment-variables)
- [🤖 AI Agents](#-ai-agents)
- [📦 Trip Pack](#-trip-pack)
- [📁 Project Structure](#-project-structure)
- [🌐 API Overview](#-api-overview)
- [🧪 Testing](#-testing)
- [🚢 Production Notes](#-production-notes)
- [📖 Documentation](#-documentation)
- [📄 License](#-license)

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🧭 Agent Hub
Five guided specialists on `/hub` walking guests through a seamless planning journey:

**Profile → Package → Food → Itinerary → Feedback**

Each agent is purpose-built with domain rules and Sri Lankan cultural knowledge.

</td>
<td width="50%">

### 💬 Classic Concierge
Streaming chat experience at `/chat` powered by a multi-phase LangChain orchestrator.

Handles complex, open-ended guest queries with context-aware, multi-turn dialogue.

</td>
</tr>
<tr>
<td>

### 🏡 Smart Package Matching
Rule-based cabana package recommendations including:
- 💑 **Love Nest Getaway**
- 👨‍👩‍👧 **Together Time Package**
- 🎉 Custom-named packages when no strong rule match

</td>
<td>

### 🍛 Food Guide
- Must-try Sri Lankan dishes with spice level indicators
- Local food photos from `frontend/public/images/food/`
- Unsplash fallback for missing images
- Cultural context and dining tips

</td>
</tr>
<tr>
<td>

### 🗺️ Itinerary Planner
- Handpicked Wellawaya-area attractions
- Live discoveries powered by **OpenTripMap**
- Full day-by-day itinerary generation

</td>
<td>

### 📄 Trip Pack (PDF + Email)
- Branded PDF after all three planners complete
- One-click download or email delivery
- Covers profile, packages, food, and itinerary

</td>
</tr>
<tr>
<td>

### 🛡️ Owner Dashboard
- Accessible at `/owner` (role: `owner`)
- View flagged feedback
- Read AI-generated feedback summaries

</td>
<td>

### 🔐 Security
- JWT auth + bcrypt password hashing
- BFF-layer rate limiting
- Prompt sanitisation on all LLM inputs
- See [SECURITY.md](SECURITY.md) for details

</td>
</tr>
</table>

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           🌐  Guest Browser                               │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │  HTTP / WebSocket
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  ⚛️  Frontend  (React 18 + Vite + Tailwind)          PORT: 5174           │
│  Landing  ·  /hub  ·  /agents/*  ·  /chat  ·  /owner                    │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │  /api/*  →  VITE_API_BASE_URL
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  🔀  BFF  (Express + Node.js)                        PORT: 3002           │
│  CORS  ·  Helmet  ·  Rate Limiting  ·  Reverse Proxy  ·  WS Chat         │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  ⚡  Backend  (FastAPI + Python 3.11)                PORT: 8010           │
│  Auth  ·  Agents  ·  Chat  ·  Recommendations  ·  Feedback  ·  PDF       │
│  LangChain  ·  FAISS KB  ·  sentence-transformers  ·  Gmail SMTP         │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │  SQLAlchemy (async)
                                     ▼
                          ┌──────────────────────┐
                          │  🐘  PostgreSQL 15    │
                          │      POSTGRES_PORT    │
                          └──────────────────────┘
```

> **Request flow:** Browser → BFF → FastAPI → SQLAlchemy → PostgreSQL  
> All LLM calls are routed exclusively through `backend/services/llm_provider.py`.  
> Agents never call each other directly — the orchestrator and `AgentRunner` manage all routing.

📐 Full system design → [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 🧰 Tech Stack

<div align="center">

| Layer | Technologies |
|:---:|:---|
| **⚛️ Frontend** | React 18 · Vite 6 · Tailwind CSS 3 · Framer Motion · Axios |
| **🔀 BFF** | Node.js 20+ · Express 4 · express-rate-limit · http-proxy-middleware |
| **⚡ Backend** | Python 3.11 · FastAPI · SQLAlchemy 2 (async) · LangChain · Groq |
| **🗄️ Data** | PostgreSQL 15 · FAISS · sentence-transformers |
| **🔗 Integrations** | Unsplash API · OpenTripMap API · Gmail SMTP |
| **🐳 DevOps** | Docker · Docker Compose |

</div>

---

## 🚀 Quick Start

### Prerequisites

Ensure you have the following installed:

| Tool | Version | Required |
|---|---|:---:|
| [Docker](https://docs.docker.com/get-docker/) | Latest | ✅ |
| Docker Compose | Latest | ✅ |
| Node.js | 20+ | ⚡ Optional |
| Python | 3.11+ | ⚡ Optional |

> ⚡ Node.js and Python are only needed if running services **outside** Docker.

---

### Step 1 — Clone & Configure

```bash
git clone <your-repo-url> leafymind
cd leafymind
cp .env.example .env
```

> 📝 Edit `.env` with your keys.  
> **Minimum required:** `GROQ_API_KEY`, `JWT_SECRET`, `POSTGRES_PASSWORD`  
> 📋 Full checklist → [docs/EXTERNAL_SERVICES_SETUP.md](docs/EXTERNAL_SERVICES_SETUP.md)

---

### Step 2 — Start the Stack

```bash
docker compose up -d --build
```

```powershell
# Windows — print all service URLs from your .env
.\scripts\show-urls.ps1
```

---

### Step 3 — Open the App

With default `.env.example` ports:

| 🖥️ Page | 🔗 URL |
|---|---|
| 🏠 Landing | http://localhost:5174/ |
| 🧭 Agent Hub | http://localhost:5174/hub |
| 💬 Classic Chat | http://localhost:5174/chat |
| 🏥 BFF Health | http://localhost:3002/health |
| 🏥 Backend Health | http://localhost:8010/health |

---

### Step 4 — Seed Data *(Recommended)*

```bash
docker exec leafymind-backend python -m scripts.seed_packages
docker exec leafymind-backend python -m scripts.seed_attractions
docker exec leafymind-backend python -m scripts.seed_food
```

---

### Step 5 — Verify External Services

```bash
docker exec leafymind-backend python -m scripts.verify_external_services
```

---

### 🛠️ Running Without Docker

> PostgreSQL must be running locally. Set `DATABASE_URL` in `.env` to point to `localhost`.

```bash
# 1. Backend
pip install -r requirements.txt
cd backend && uvicorn main:app --reload --port 8010

# 2. BFF
cd bff && npm install && npm run dev

# 3. Frontend
cd frontend && npm install && npm run dev
```

---

## ⚙️ Environment Variables

Copy [`.env.example`](.env.example) → `.env` and configure:

| Variable | Description | Required |
|---|---|:---:|
| `DATABASE_URL` | Async PostgreSQL connection string | ✅ |
| `JWT_SECRET` | JWT signing secret *(min. 32 chars)* | ✅ |
| `LLM_PROVIDER` | LLM provider name *(default: `groq`)* | ✅ |
| `GROQ_API_KEY` | Groq API key for LLM inference | ✅ |
| `UNSPLASH_ACCESS_KEY` | Fallback food image fetching | ⚡ |
| `OPENTRIPMAP_API_KEY` | Itinerary attraction discovery | ⚡ |
| `GMAIL_SENDER_ADDRESS` | Gmail address for outbound emails | ⚡ |
| `GMAIL_APP_PASSWORD` | Gmail app password (SMTP) | ⚡ |
| `FRONTEND_URL` | Guest app public URL | ✅ |
| `VITE_API_BASE_URL` | Browser → BFF base URL | ✅ |
| `CORS_ALLOWED_ORIGINS` | Allowed browser origins (comma-separated) | ✅ |

> ✅ = Required &nbsp;|&nbsp; ⚡ = Required for that feature

---

## 🤖 AI Agents

All agents are registered in `backend/agents/registry.py`.

```
                    ┌─────────────────────────┐
                    │      🧭 Agent Hub        │
                    │    Guided tap-through    │
                    └────────────┬────────────┘
                                 │
      ┌──────────┬───────────────┼───────────────┬──────────┐
      ▼          ▼               ▼               ▼          ▼
  👤 Profile  📦 Package     🍛 Food        🗺️ Itinerary  ⭐ Feedback
  Builder    Planner         Guide          Planner      Collector
  (Step 1 ─  (Rule-based     (Dishes +      (Day plans + (Post-stay
  required)   packages)       photos)        discovery)   ratings)
```

| 🤖 Agent | 🆔 ID | 📋 Role |
|---|---|---|
| 👤 Profile Builder | `profile_builder` | 8-step guest profile — **must complete first** |
| 📦 Package Planner | `package_recommender` | Rule-based cabana package matching |
| 🍛 Food Guide | `food_guide` | Dish recommendations, spice levels, photos |
| 🗺️ Itinerary Planner | `itinerary_planner` | Day plans and nearby attraction discovery |
| ⭐ Feedback Collector | `feedback_collector` | Post-stay ratings and open comments |
| 🎩 Full Concierge | `concierge` | Classic `/chat` multi-phase orchestration |

> 📁 Business rules: `backend/rules/business_rules.py`  
> 🔗 LLM gateway: `backend/services/llm_provider.py`  
> 📖 Full agent docs: [docs/AGENT_HUB.md](docs/AGENT_HUB.md)

---

## 📦 Trip Pack

After completing **all three planners** (package + food + itinerary), guests unlock their trip pack:

```
  ✅ Package Planner  +  ✅ Food Guide  +  ✅ Itinerary Planner
                              │
                              ▼
              ┌───────────────────────────────┐
              │       🎁 Your Trip Pack        │
              ├───────────────────────────────┤
              │  📄 Download PDF               │
              │  📧 Email My Plan              │
              └───────────────────────────────┘
```

| Feature | Description |
|---|---|
| 📄 **Download PDF** | Branded plan — profile, packages, food photos, itinerary |
| 📧 **Email My Plan** | Sends PDF on demand; requires email on profile + Gmail SMTP |
| 📝 **Feedback Email** | Sent separately after all planners complete |

📖 Full details: [docs/TRIP_PACK.md](docs/TRIP_PACK.md)

---

## 📁 Project Structure

```
LeafyMind/
│
├── 📄 .env.example                   # Environment variable template
├── 🐳 docker-compose.yml             # Local development stack
├── 📋 README.md
├── 🔒 SECURITY.md
│
├── 🐍 backend/
│   ├── agents/                       # Specialist agents + orchestrator
│   ├── api/                          # FastAPI route handlers
│   ├── models/                       # SQLAlchemy ORM models
│   ├── services/                     # LLM · email · PDF · journey · KB
│   ├── rules/                        # Package matching business rules
│   ├── scripts/                      # Seeds · smoke tests · verification
│   └── requirements.txt
│
├── 🔀 bff/                           # Express reverse proxy server
│
├── ⚛️ frontend/
│   ├── src/                          # React components and pages
│   └── public/images/food/           # Dish photos (mounted into backend)
│
├── 🗄️ db/migrations/                 # PostgreSQL schema (001–005)
├── 📖 docs/                          # Project documentation
└── 🛠️ scripts/show-urls.ps1          # Print local service URLs
```

---

## 🌐 API Overview

All guest APIs are proxied by the BFF under `/api/*`.  
Authenticated routes require: `Authorization: Bearer <jwt>`

| 🔗 Prefix | 📡 Endpoints |
|---|---|
| 🔐 `/auth` | `POST /register` · `POST /login` · `GET /me` |
| 🤖 `/agents` | `GET /journey` · `POST /{agent}/threads` · SSE message stream |
| 💬 `/chat` | `POST /session/start` · `POST /message` *(SSE)* |
| 🎯 `/recommendations` | `GET /packages/{sessionId}` · `GET /food/` · `GET /itinerary/` |
| 📦 `/trip-pack` | `GET /summary` · `GET /pdf` · `POST /email` |
| ⭐ `/feedback` | `POST /submit` · `GET /summary` *(owner only)* |

📖 Full reference: [docs/API_REFERENCE.md](docs/API_REFERENCE.md)

---

## 🧪 Testing

### 🔥 Smoke Tests

```bash
# Auth flow
docker exec leafymind-backend python -m scripts.test_auth_smoke

# Agent Hub end-to-end
docker exec leafymind-backend python -m scripts.test_agent_hub_flow

# Owner dashboard
docker exec leafymind-backend python -m scripts.test_owner_dashboard
```

### 🧬 Unit Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

### 📋 Manual E2E

Full test checklist → [docs/FULL_APP_TESTING_GUIDE.md](docs/FULL_APP_TESTING_GUIDE.md)

---

## 🚢 Production Notes

> ⚠️ **Never deploy with default `.env.example` values.**

### 🔐 Security Checklist

| Item | Action |
|---|---|
| `JWT_SECRET` | Strong unique value — minimum 32 characters |
| `POSTGRES_PASSWORD` | Strong unique value |
| `CORS_ALLOWED_ORIGINS` | Explicit production URLs only — no wildcards |
| `NODE_ENV` | Set to `production` |
| `FRONTEND_URL` | Real guest-facing domain |
| API Keys | Use a secrets manager — **never commit `.env`** |

---

### 👑 Promote an Owner Account

```sql
UPDATE users SET role = 'owner' WHERE email = 'you@yourdomain.com';
```

---

### 🔄 Rebuild FAISS Knowledge Base

Run this after seeding new packages or attractions:

```bash
docker exec leafymind-backend python -m scripts.rebuild_kb
docker compose restart backend
```

---

### 📊 View Logs

```bash
docker compose logs -f backend
docker compose logs -f bff
docker compose logs -f frontend
```

---

## 📖 Documentation

| 📄 Document | 📋 Description |
|---|---|
| [docs/README.md](docs/README.md) | Documentation index |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, data flow, key modules |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | REST endpoints and authentication |
| [docs/AGENT_HUB.md](docs/AGENT_HUB.md) | Agent journey, flows, and artifacts |
| [docs/TRIP_PACK.md](docs/TRIP_PACK.md) | PDF download and email delivery |
| [docs/EXTERNAL_SERVICES_SETUP.md](docs/EXTERNAL_SERVICES_SETUP.md) | API keys and Gmail SMTP setup |
| [docs/FULL_APP_TESTING_GUIDE.md](docs/FULL_APP_TESTING_GUIDE.md) | End-to-end manual test checklist |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Local dev workflow and conventions |
| [SECURITY.md](SECURITY.md) | Auth model, rate limits, vulnerability reporting |
| [frontend/public/images/food/README.md](frontend/public/images/food/README.md) | Food photo naming convention |

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=100&section=footer" width="100%"/>

**Built with 🌿 for [Leafy Cave](https://leafycave.com) — Wellawaya, Sri Lanka**

*Proprietary — Leafy Cave / LeafyMind. All rights reserved.*

</div>
