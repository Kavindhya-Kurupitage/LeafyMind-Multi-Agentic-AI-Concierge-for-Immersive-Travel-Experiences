# Quest 2 — Submission checklist (LeafyMind)

Use this list against the **5-Day Remote Forward Deploy Trial** requirements. Check off each item before you submit.

---

## What you must submit

| # | Deliverable | Status | Where |
|---|-------------|--------|--------|
| 1 | **Public GitHub repo** | ☐ | Push `LeafyMind`; no secrets in history |
| 2 | **Live URL** | ☐ | Deploy or tunnel — see § Live demo below |
| 3 | **Case study** | ☐ | [CASE_STUDY.md](CASE_STUDY.md) → Notion or PDF export |
| 4 | **Client one-liner** (optional) | ☐ | Screenshot or quote in case study |
| 5 | **5-min Loom video** | ☐ | Script in case study § Demo video |

---

## What you already have in this repo

| Quest requirement | Your artifact |
|-------------------|---------------|
| Cursor-ready setup | `.cursorrules`, `.cursor/rules/*.mdc` |
| Secrets removed | `.env.example`, `.gitignore` ignores `.env` |
| README | `README.md` |
| Architecture | `docs/ARCHITECTURE.md` |
| API docs | `docs/API_REFERENCE.md` |
| Setup guide | `docs/EXTERNAL_SERVICES_SETUP.md` |
| Test plan | `docs/FULL_APP_TESTING_GUIDE.md` |
| Security | `SECURITY.md` |

---

## What you still need to do

### Before submission (critical)

1. **Record a real client interview** (≥30 min) with Leafy Cave owner/staff — fill [PROBLEM_1PAGER.md](PROBLEM_1PAGER.md) with actual quotes and decisions.
2. **Run baseline comparison** — document in case study § Evaluation (numbers or qualitative table).
3. **Deploy live URL** — guest can open `/hub` without your laptop (see below).
4. **Record Loom** — screen + terminal; show register → hub → 3 planners → trip pack PDF.
5. **Get client feedback** — one sentence + screenshot for case study.
6. **Audit repo for secrets** — `git log`, no `.env` committed; rotate keys if ever leaked.

### Recommended polish

- Add `frontend/public/logo.png` for PDF branding.
- Add 10+ food photos in `frontend/public/images/food/`.
- Run `docker exec leafymind-backend python -m scripts.verify_external_services`.
- Promote test user to `owner` and show `/owner` in Loom (30 seconds).

---

## Live demo options

Pick one for submission **Live URL**:

| Option | Effort | Notes |
|--------|--------|-------|
| **Railway / Render / Fly.io** | Medium | Docker Compose or split services; set env vars in dashboard |
| **VPS + Docker** | Medium | `docker compose up` on DigitalOcean/Hetzner |
| **ngrok / Cloudflare Tunnel** | Low | Temporary URL for Loom only — state “demo tunnel” in case study |

Minimum live proof: landing page loads, sign-in works, Agent Hub shows journey, one agent returns a result.

---

## 5-day rhythm mapping (what you did / document)

| Day | Quest focus | LeafyMind deliverable |
|-----|-------------|------------------------|
| **Day 1** | Discovery | `PROBLEM_1PAGER.md` + client interview notes |
| **Day 2** | Design & v1 | Agent Hub + orchestrator + Docker stack |
| **Day 3–4** | Build & eval | Rules engine, food images, trip pack, integration tests |
| **Day 5** | Handoff | Case study, Loom, client quote, public repo |

---

## Evaluation axes — self-score prep

Score yourself 1–5 per axis after submission (reviewers will score separately):

| Axis | Your evidence in repo |
|------|------------------------|
| Problem framing | Real cabana; international guests; pre-arrival planning pain |
| Priority judgment | Profile first → planners → trip pack → feedback last |
| AI fluency | Multi-agent hub, rules + LLM, eval scripts, Cursor workflow |
| Shipping | Docker, health endpoints, working SSE agents |
| Evaluation | Baseline table in case study (you must complete) |
| Ownership | Docs, honest “what broke” section, `.env.example` |

---

## Loom structure (5 minutes)

| Time | Show |
|------|------|
| 0:00–0:30 | Problem + who the client is |
| 0:30–1:00 | README / architecture diagram |
| 1:00–2:00 | `docker compose ps` + health URLs |
| 2:00–3:30 | Register → Profile Builder → Package → Food (photos) → Itinerary |
| 3:30–4:30 | Trip pack: Download PDF + Email button |
| 4:30–5:00 | What you’d improve next + client quote |

---

## GitHub publish steps

```bash
# Ensure .env is not tracked
git status
git check-ignore -v .env

# Create public repo on GitHub, then:
git remote add origin https://github.com/YOUR_USER/leafymind.git
git branch -M main
git push -u origin main
```

Add to README topdiv:

```markdown
**Quest 2 demo:** [Live app](YOUR_LIVE_URL) · [Case study](docs/CASE_STUDY.md) · [Loom](YOUR_LOOM_URL)
```

---

## Final submission message template

```
Quest 2 — LeafyMind (Leafy Cave AI Concierge)

Repo: https://github.com/YOUR_USER/leafymind
Live: https://YOUR_LIVE_URL
Case study: https://github.com/YOUR_USER/leafymind/blob/main/docs/CASE_STUDY.md
Loom: https://www.loom.com/share/YOUR_ID

Client: Leafy Cave Luxury Cabana, Wellawaya, Sri Lanka
```
