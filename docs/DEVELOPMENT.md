# Development guide

Conventions and workflows for contributing to LeafyMind.

---

## Repository layout

| Path | Stack |
|------|-------|
| `backend/` | Python 3.11, FastAPI |
| `bff/` | Node ESM, Express |
| `frontend/` | React 18, Vite |
| `db/migrations/` | Raw SQL, applied on Postgres container init |

---

## Python setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

From repo root:

```bash
pip install -r requirements.txt
```

**Run API locally:**

```bash
cd backend
export DATABASE_URL=postgresql+asyncpg://leafymind:password@localhost:5433/leafymind
uvicorn main:app --reload --port 8010
```

**Tests:**

```bash
cd backend
pytest
# Integration (Docker backend running):
python -m scripts.test_auth_smoke
python -m scripts.test_agent_hub_flow
```

---

## Node setup

```bash
cd bff && npm install && npm run dev
cd frontend && npm install && npm run dev
```

Set `VITE_API_BASE_URL=http://localhost:3002/api` in `.env` for local BFF.

---

## Docker workflow

```bash
docker compose up -d --build
docker compose logs -f backend
docker compose restart backend   # after .env changes
.\scripts\show-urls.ps1
```

**Optional pgAdmin:**

```bash
docker compose --profile dev-tools up -d
```

---

## Scripts reference

| Script | Purpose |
|--------|---------|
| `scripts/seed_packages.py` | Load cabana packages into DB |
| `scripts/seed_attractions.py` | Curated attractions |
| `scripts/seed_food.py` | Food catalog |
| `scripts/rebuild_kb.py` | Rebuild FAISS indexes |
| `scripts/verify_external_services.py` | Check API keys and mounts |
| `scripts/send_feedback_emails_now.py` | Trigger feedback email job |
| `scripts/test_auth_smoke.py` | Auth API smoke test |
| `scripts/test_agent_hub_flow.py` | Hub journey integration |
| `scripts/test_full_flow.py` | Classic chat flow |
| `scripts/test_owner_dashboard.py` | Owner feedback API |

All run inside backend container:

```bash
docker exec leafymind-backend python -m scripts.<name>
```

---

## Code conventions

### Python

- PEP 8, type hints on public functions
- `async def` for FastAPI routes and DB calls
- Docstrings on new modules
- No raw SQL in business logic — use SQLAlchemy models
- No direct LLM calls outside `llm_provider.py`

### React

- Functional components and hooks only
- Tailwind for styling; brand tokens: `forest`, `gold`, `cream`
- API calls via `frontend/src/utils/api.js`

### Migrations

- Filename: `00N_description.sql` in `db/migrations/`
- Applied automatically on fresh Postgres volume via `docker-entrypoint-initdb.d`

---

## Adding a new API route

1. Create router in `backend/api/`
2. Register in `backend/main.py` with `include_router`
3. Add Pydantic request/response models
4. Use `Depends(get_current_user)` for protected routes
5. Document in `docs/API_REFERENCE.md`

---

## Adding food images

1. Add JPG/PNG to `frontend/public/images/food/`
2. Prefer names matching dish stems (see `food/README.md`)
3. Restart not required — Vite serves `/images/food/`; backend reads same files via Docker mount

---

## Cursor AI rules

- Root: `.cursorrules`
- Detailed: `.cursor/rules/*.mdc`

Keep rules in sync when changing architecture boundaries.

---

## Common issues

| Symptom | Fix |
|---------|-----|
| `Too many requests` | Wait 15 min or restart BFF; trip-pack routes are exempt |
| Login timeout | Increase backend Docker memory (compose limit 1024M) |
| Food images 🍛 placeholder | Add local file or Unsplash key |
| Trip pack hidden | Complete all 3 planners; hard-refresh `/hub` |
| `.env` ignored | Restart `leafymind-backend` after edits |
