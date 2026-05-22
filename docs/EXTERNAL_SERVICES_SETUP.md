# External services setup (LeafyMind)

Complete this checklist so **Groq**, **local food images**, **Unsplash**, **OpenTripMap**, and **Gmail SMTP** are all active (chat, food guide, itinerary, trip pack PDF email, and feedback survey).

After filling `.env`, verify everything:

```powershell
cd "D:\Leafy Cave AI Project\LeafyMind"
docker compose up -d
docker exec leafymind-backend python -m scripts.verify_external_services
```

---

## 1. Groq (LLM — required)

**You already have this** if `GROQ_API_KEY` is set and chat works.

| Step | Action |
|------|--------|
| Account | [https://console.groq.com](https://console.groq.com) |
| Key | API Keys → Create → paste into `.env` as `GROQ_API_KEY` |
| Test | Sign in at `http://localhost:5174` and send a chat message |

---

## 2. Local food images (required for Leafy Cave branding)

No API account. Add your own photos.

| Step | Action |
|------|--------|
| Folder | `frontend/public/images/food/` |
| Names | See `frontend/public/images/food/README.md` (e.g. `egg-hoppers.jpg`, `kottu-roti.jpg`) |
| Docker | Backend mounts this folder automatically (`docker-compose.yml`) |
| Test | Run Food Guide agent → images load from `/images/food/...` in browser Network tab |

**Minimum for demo:** add at least 3–4 images for dishes you expect the AI to recommend.

---

## 3. Unsplash (required fallback)

Used when a recommended dish has **no** local file.

| Step | Action |
|------|--------|
| 1 | Go to [https://unsplash.com/join](https://unsplash.com/join) and create an account |
| 2 | Open [https://unsplash.com/developers](https://unsplash.com/developers) |
| 3 | **New Application** → name e.g. `LeafyMind` → accept terms |
| 4 | Copy **Access Key** (not Secret Key) |
| 5 | In `.env`: `UNSPLASH_ACCESS_KEY=paste_access_key_here` |
| 6 | `docker compose restart leafymind-backend` |

**Free tier:** 50 requests/hour (demo). Production may need higher tier or rely more on local images.

**Test:** Temporarily rename one local food image, run Food Guide for that dish → should load from `images.unsplash.com`.

---

## 4. OpenTripMap (required for itinerary discoveries)

Adds “Nearby Discovery” places when curated DB attractions do not fully cover guest interests.

| Step | Action |
|------|--------|
| 1 | Register at [https://opentripmap.io/](https://opentripmap.io/) |
| 2 | Profile / API → copy your **API key** |
| 3 | In `.env`: `OPENTRIPMAP_API_KEY=paste_key_here` |
| 4 | Confirm cabana coordinates (Wellawaya): `CABANA_LAT=6.7311`, `CABANA_LON=81.1003` |
| 5 | `docker compose restart leafymind-backend` |

**Free tier:** ~5 requests/second — enough for dev.

**Test:** Complete profile + run Itinerary Planner → narrative may include “Nearby Discovery” entries; backend logs show `OpenTripMap: N places`.

---

## 5. Gmail SMTP (required for emails)

Powers two separate guest emails:

| Email | When |
|-------|------|
| **Trip plan PDF** | Guest clicks **Email my plan** on Agent Hub (on-demand) |
| **Feedback survey** | After all three planners complete (automatic once) |

Scheduler also runs post-stay feedback jobs on backend startup (`feedback_email_delay_days`).

| Step | Action |
|------|--------|
| 1 | Use a Gmail account (e.g. `leafycave.feedback@gmail.com`) |
| 2 | Google Account → **Security** → enable **2-Step Verification** |
| 3 | Security → **App passwords** → App: Mail, Device: Windows → **Generate** |
| 4 | Copy the 16-character password (spaces optional) |
| 5 | In `.env`: |
| | `GMAIL_SENDER_ADDRESS=your@gmail.com` |
| | `GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx` |
| | `FRONTEND_URL=http://localhost:5174` (must match how guests open the app) |
| 6 | `docker compose restart leafymind-backend` |

**Test (manual send):**

```powershell
docker exec leafymind-backend python -m scripts.send_feedback_emails_now
```

(Check backend logs; guest sessions need `email` in profile and completed stay dates.)

---

## 6. Optional: OpenAI embeddings

Only if you want FAISS indexes built with OpenAI instead of the free local HuggingFace model.

| `.env` | `OPENAI_API_KEY=sk-...` |
| Rebuild KB | `docker exec leafymind-backend python -m scripts.rebuild_kb` |

Leave empty for normal operation with Groq.

---

## 7. Trip pack branding (optional)

| Step | Action |
|------|--------|
| Logo | Add `frontend/public/logo.png` for PDF header (else text “LEAFY CAVE”) |
| Test | Complete all 3 planners → `/hub` → **Download PDF** |

See [TRIP_PACK.md](TRIP_PACK.md).

---

## `.env` checklist

Before calling the app “complete”, confirm:

- [ ] `GROQ_API_KEY` — set (not `REPLACE_`)
- [ ] `UNSPLASH_ACCESS_KEY` — set
- [ ] `OPENTRIPMAP_API_KEY` — set
- [ ] `GMAIL_SENDER_ADDRESS` + `GMAIL_APP_PASSWORD` — set
- [ ] `FRONTEND_URL` matches `http://localhost:YOUR_FRONTEND_PORT`
- [ ] `PUBLIC_ASSETS_DIR` / food volume mounts (default in `docker-compose.yml`)
- [ ] At least several files in `frontend/public/images/food/`
- [ ] `docker exec leafymind-backend python -m scripts.verify_external_services` — all OK

---

## Production notes

- Never commit `.env` to Git.
- Use strong `JWT_SECRET` and `POSTGRES_PASSWORD` on the server.
- Set `FRONTEND_URL` to your real domain (e.g. `https://guest.leafycave.com`).
- Restrict `CORS_ALLOWED_ORIGINS` to your real frontend/BFF URLs only.
- Rotate API keys if they are ever exposed.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Food images show 🍛 | Add local file OR set `UNSPLASH_ACCESS_KEY` |
| No itinerary discoveries | Set `OPENTRIPMAP_API_KEY`; check backend logs |
| No feedback emails | Gmail app password + guest email in profile; run `send_feedback_emails_now` |
| Login slow | See README Docker memory; stop other heavy containers |
| Keys in `.env` but not loaded | `docker compose restart leafymind-backend` after editing `.env` |
