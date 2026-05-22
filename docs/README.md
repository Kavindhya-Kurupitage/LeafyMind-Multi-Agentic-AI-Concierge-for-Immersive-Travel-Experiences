# LeafyMind documentation

Central index for technical documentation. Start with the [main README](../README.md) for setup.

---

## Getting started

| Guide | Audience | Content |
|-------|----------|---------|
| [EXTERNAL_SERVICES_SETUP.md](EXTERNAL_SERVICES_SETUP.md) | DevOps / developers | Groq, Unsplash, OpenTripMap, Gmail, food images |
| [FULL_APP_TESTING_GUIDE.md](FULL_APP_TESTING_GUIDE.md) | QA / developers | End-to-end manual test phases |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Developers | Conventions, scripts, debugging |

---

## System design

| Guide | Content |
|-------|---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Layers, agents, data stores, security boundaries |
| [API_REFERENCE.md](API_REFERENCE.md) | REST routes, auth, SSE streaming |
| [AGENT_HUB.md](AGENT_HUB.md) | Guided flows, journey states, artifacts |
| [TRIP_PACK.md](TRIP_PACK.md) | PDF generation and email delivery |

---

## Related files

| File | Purpose |
|------|---------|
| [../SECURITY.md](../SECURITY.md) | Authentication, rate limits, vulnerability reporting |
| [../.env.example](../.env.example) | Environment variable template |
| [../frontend/public/images/food/README.md](../frontend/public/images/food/README.md) | Local dish image naming |

---

## Service URLs (default `.env.example`)

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5174 |
| Agent Hub | http://localhost:5174/hub |
| BFF API | http://localhost:3002/api |
| Backend (direct) | http://localhost:8010 |

Run `.\scripts\show-urls.ps1` after `docker compose up` to print ports from your `.env`.
