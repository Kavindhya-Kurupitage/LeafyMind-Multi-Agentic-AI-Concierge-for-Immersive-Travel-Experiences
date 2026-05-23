# README for AI assistants (Cursor, Claude, Copilot)

This file helps AI tools understand **LeafyMind** quickly. Humans should start with [README.md](README.md).

---

## Project

**LeafyMind** — AI concierge for **Leafy Cave** luxury cabana (Wellawaya, Sri Lanka).  
Stack: `frontend/` (React+Vite) → `bff/` (Express) → `backend/` (FastAPI) → PostgreSQL.

## Non-negotiable rules

1. LLM only via `backend/services/llm_provider.py`
2. DB only via SQLAlchemy models in `backend/models/`
3. Agents do not call agents — use `orchestrator.py` or `agent_runner.py`
4. Package matching in `backend/rules/business_rules.py`
5. No secrets in code — use `backend/config.py` + `.env`

## Key paths

| Area | Path |
|------|------|
| API routes | `backend/api/` |
| Agents | `backend/agents/` |
| Journey / trip pack | `backend/services/journey_service.py`, `trip_summary_service.py` |
| Hub UI | `frontend/src/pages/AgentHubPage.jsx` |
| Trip pack UI | `frontend/src/components/agents/TripPackPanel.jsx` |
| Cursor rules | `.cursorrules`, `.cursor/rules/*.mdc` |

## Docs index

See [docs/README.md](docs/README.md).

## Default ports (.env.example)

- Frontend: 5174  
- BFF API: 3002/api  
- Backend: 8010  

## Quest 2 portfolio

Case study: [docs/CASE_STUDY.md](docs/CASE_STUDY.md)
