# Case Study: LeafyMind — AI Concierge for Leafy Cave

**Quest 2 · 5-Day Remote Forward Deploy Trial**  
**Author:** _[Your name]_  
**Dates:** _[Mon–Fri dates]_  
**Repository:** https://github.com/_[YOUR_USER]_/leafymind  
**Live demo:** https://_[YOUR_LIVE_URL]_  
**Loom (5 min):** https://www.loom.com/share/_[YOUR_ID]_

---

## Executive summary

I built **LeafyMind**, an AI-native pre-arrival concierge for **Leafy Cave Luxury Cabana** (Wellawaya, Sri Lanka). International guests use a guided **Agent Hub** to complete a travel profile, receive rule-grounded package recommendations, a Sri Lankan food guide with photos, and a day-by-day itinerary—then download or email a **branded trip-plan PDF**.

This is not a thin ChatGPT wrapper: it combines **multi-agent orchestration**, a **business-rules engine** for cabana packages, **structured artifacts** per specialist, **FAISS knowledge retrieval**, external APIs (OpenTripMap, Unsplash), and **evaluation scripts**—shipped as a Dockerized full stack (React + BFF + FastAPI + PostgreSQL).

---

## 1. Client & problem

### Client

| Field | Detail |
|-------|--------|
| **Business** | Leafy Cave Luxury Cabana |
| **Owner** | Pramitha Madushanka |
| **Location** | Wellawaya, Sri Lanka |
| **Guests** | International tourists (couples, families, small groups) |

### Problem (validated in client interview)

Leafy Cave’s owner spent significant time on **repetitive pre-arrival questions** via WhatsApp and email: which cabana package fits a couple vs family, what to eat with dietary restrictions, how to plan days around Ella, waterfalls, and wildlife, and what guests should know about spice levels and local culture.

Guests arrived with **uneven preparation**—some overwhelmed, some mis-matched to packages—while the owner had no single **shareable plan document** to send before travel.

**Target user:** Overseas guest planning a 2–7 night stay who wants one trusted, warm planning experience—not generic LLM travel advice.

Full discovery doc: [PROBLEM_1PAGER.md](PROBLEM_1PAGER.md)

---

## 2. Hypothesis & chosen solution

### Hypothesis

> A **guided multi-agent workflow** with **owner business rules** and a **deliverable trip pack (PDF/email)** will reduce owner repetitive work and increase guest confidence before arrival—faster than a single chat thread or manual concierge alone.

### Options considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| A. WhatsApp + ChatGPT copy-paste | Zero build | No rules, no persistence, owner still in loop | Rejected |
| B. Single chatbot page | Fast UI | Weak structure, package hallucination risk | Rejected |
| **C. Agent Hub + rules + trip pack** | Clear journey, testable artifacts, brand output | More engineering | **Chosen** |
| D. Custom mobile app | Native UX | Out of 5-day scope | Deferred |

### Chosen solution (MVP)

**LeafyMind Agent Hub** (`/hub`):

1. **Profile Builder** (required) — 8-step guided interview  
2. **Package Planner** — rule-based matching (`Love Nest Getaway`, `Together Time Package`, custom name if weak match)  
3. **Food Guide** — must-try dishes, spice, local images  
4. **Itinerary Planner** — curated DB attractions + OpenTripMap discoveries  
5. **Trip pack** — PDF download + on-demand email when all three planners complete  
6. **Feedback Collector** — post-planning / post-stay ratings for owner dashboard  

Secondary path: **classic streaming concierge** (`/chat`) for guests who prefer one continuous conversation.

---

## 3. AI-native workflow

### How AI was used as a multiplier (not just chat)

| Layer | AI / automation role |
|-------|----------------------|
| **Development** | Cursor + `.cursorrules` / `.cursor/rules` — rapid full-stack iteration, tests, docs |
| **Runtime** | Groq (`llama-3.1-8b-instant`) via single `llm_provider.py` gateway |
| **Agents** | LangChain specialists: profile extraction, narrative, food copy, itinerary narration |
| **Grounding** | `business_rules.py` overrides weak LLM package picks; FAISS KB for retrieval |
| **Structure** | SSE streaming + JSON **artifacts** per agent (packages, food, itinerary) |
| **Evaluation** | `test_agent_hub_flow.py`, `test_package_rules.py`, `verify_external_services.py` |
| **Delivery** | Programmatic PDF (`fpdf2`) with embedded food photos—not LLM-generated PDF |

### Architecture (shipped)

```
Guest → React (Vite) → Express BFF → FastAPI → PostgreSQL
                              ↓
                    LangChain agents + rules + FAISS
                              ↓
              OpenTripMap · Unsplash · Gmail SMTP
```

### What failed / honest notes

- **Food images in chat markdown** — guests expected photos in chat text; fixed by rendering **`FoodGuideCard`** from structured artifacts, not raw LLM markdown.  
- **Wrong package for group type** — fixed with `MIN_STRONG_MATCH_SCORE` and custom package naming when no strong rule match.  
- **Survey vs trip-plan email confusion** — feedback email now sends only after all three planners; trip PDF is **on-demand** via button.  
- **Rate limits in dev** — BFF 100 req/15 min; trip-pack routes exempted.  

---

## 4. Evaluation & baseline comparison

### Baseline (before / without LeafyMind)

| Dimension | Baseline | Method |
|-----------|----------|--------|
| Planning channel | Owner WhatsApp/email | Client interview |
| Time to plan | _[~2 hours back-and-forth — fill your measured]_ | Stopwatch on manual replay |
| Package correctness | Owner memory; occasional mismatch | Review 5 personas |
| Structured output | None (text threads only) | N/A |
| Feedback capture | Ad hoc | N/A |

### With LeafyMind (MVP)

| Dimension | Result | Method |
|-----------|--------|--------|
| End-to-end hub flow | Pass | `python -m scripts.test_agent_hub_flow` |
| Package rules | Pass | `pytest backend/tests/test_package_rules.py` |
| Auth smoke | Pass | `python -m scripts.test_auth_smoke` |
| External services | _[Pass/Fail per key]_ | `python -m scripts.verify_external_services` |
| Guest time to trip pack | _[~XX min — fill from Loom test]_ | New user test |
| Trip pack PDF | Generated with photos + itinerary | Download from `/hub` |

### Comparison table (fill numbers after your test run)

| Metric | Baseline | LeafyMind | Δ |
|--------|----------|-----------|---|
| Owner minutes per guest (planning) | _[60+]_ | _[15 self-serve + 5 review]_ | _[-70% target]_ |
| Wrong package shown (5 test profiles) | _[1–2]_ | _[0]_ | Rules engine |
| Single shareable document | No | Yes (PDF) | New capability |
| Automated integration test | No | Yes | 3+ scripts |

### Evaluation thinking (why this matters)

I did not only “demo happy path.” I added:

- **Rule-based tests** so package recommendations are regression-testable  
- **Integration script** for full Agent Hub journey  
- **Service verification** script for API keys and mounts  
- **Explicit baseline** (manual concierge) vs **structured agent outputs**  

---

## 5. What I learned & next improvements

### Learned

1. **Real clients need rules, not just prompts** — cabana packages must be hard-constrained by group type and travel style.  
2. **Artifacts > chat** — UI must render structured JSON (cards, timeline, PDF), not rely on markdown in chat.  
3. **Separate deliverables** — trip plan PDF and feedback survey are different jobs; triggers must be explicit.  
4. **AI-native delivery** — Cursor rules + docs let me ship a multi-service repo in five days without losing architecture discipline.  

### Next (v2)

| Priority | Improvement |
|----------|-------------|
| P0 | Production deploy (HTTPS, managed Postgres, secrets manager) |
| P1 | httpOnly cookie auth instead of `localStorage` JWT |
| P2 | Owner CMS for packages/attractions without SQL |
| P3 | Sinhala/Tamil guest UI |
| P4 | Booking.com / payment integration |
| P5 | Analytics funnel (profile → planners → PDF → booking) |

---

## 6. Handoff to client

### What the client receives

- GitHub access to documentation and setup guides  
- Docker Compose instructions to run locally or on a VPS  
- `.env.example` — no secrets in repo  
- [EXTERNAL_SERVICES_SETUP.md](EXTERNAL_SERVICES_SETUP.md) for Gmail, Groq, Unsplash, OpenTripMap  

### Training (15 min)

1. Open `/hub` after guest registers  
2. Guest completes Profile → 3 planners → Trip pack  
3. Optional: promote owner account → `/owner` for feedback  

### Client feedback (replace with real quote + screenshot)

> _“_[One sentence from Pramitha — e.g. ‘This saves me explaining the same packages every week, and guests finally get one document before they fly.’]_”_

— **Pramitha Madushanka**, Owner, Leafy Cave Cabana

---

## 7. Demo video guide (Loom)

**Title:** LeafyMind — 5-Day FDE Trial Demo (Leafy Cave)

1. Problem (30s)  
2. `docker compose ps` + health checks (30s)  
3. Register → Profile Builder complete (60s)  
4. Package + Food (show photos) + Itinerary (90s)  
5. Trip pack: Download PDF, mention Email button (60s)  
6. Show `test_agent_hub_flow` or pytest in terminal (30s)  
7. Lessons + client quote (30s)  

---

## 8. Self-assessment vs Quest rubric (1–5)

| Axis | Score | Evidence |
|------|-------|----------|
| Problem framing | _[4–5]_ | Real cabana, clear guest, interview doc |
| Priority judgment | _[4–5]_ | Profile → planners → trip pack → feedback |
| AI fluency | _[4–5]_ | Multi-agent, rules, evals, Cursor workflow |
| Shipping & execution | _[4–5]_ | Docker, live URL, working SSE + PDF |
| Evaluation thinking | _[3–5]_ | Baseline table + tests — **strengthen with your numbers** |
| Ownership & communication | _[4–5]_ | Full docs, honest failures, `.env.example` |

---

## Appendix: Links

| Resource | Path |
|----------|------|
| README | [../README.md](../README.md) |
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) |
| API | [API_REFERENCE.md](API_REFERENCE.md) |
| Testing | [FULL_APP_TESTING_GUIDE.md](FULL_APP_TESTING_GUIDE.md) |
| Submission checklist | [QUEST2_SUBMISSION_CHECKLIST.md](QUEST2_SUBMISSION_CHECKLIST.md) |
