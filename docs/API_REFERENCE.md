# API reference

Base URL for browser clients: **`{VITE_API_BASE_URL}`** (default `http://localhost:3002/api`).

Direct backend (debugging): `http://localhost:8010` — same paths without `/api` prefix when calling FastAPI directly.

---

## Authentication

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | No | Create guest account |
| POST | `/auth/login` | No | Returns `access_token` (JWT) |
| GET | `/auth/me` | Yes | Current user |
| POST | `/auth/logout` | Yes | Revoke token `jti` |
| POST | `/auth/password-reset-request` | No | MVP: token logged server-side |
| POST | `/auth/password-reset/confirm` | No | Set new password with token |

**Header:** `Authorization: Bearer <access_token>`

---

## Health

| Method | Path | Auth |
|--------|------|------|
| GET | `/health` | No |

Response: `{ "status": "ok", "version": "1.0.0", "timestamp": "...", "request_id": "..." }`

---

## Agents (Agent Hub)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/agents` | Yes | List specialist metadata |
| GET | `/agents/journey` | Yes | Profile %, step locks, trip pack flags |
| GET | `/agents/{agent_id}` | Yes | Single agent metadata |
| POST | `/agents/{agent_id}/threads` | Yes | Create thread |
| GET | `/agents/{agent_id}/threads` | Yes | List threads for agent |
| GET | `/agents/threads/{thread_id}` | Yes | Thread + messages + artifacts |
| POST | `/agents/threads/{thread_id}/message` | Yes | **SSE** stream (JSON body or guided_response) |

### Journey response fields

- `profile_complete`, `profile_completeness`
- `optional_agents_completed` — list of agent IDs with results
- `trip_pack_ready` — all three planners done
- `trip_pack_planners_done` — `{ package_recommender: bool, food_guide: bool, itinerary_planner: bool }`
- `steps` — per-agent `status`, `locked`, `thread_id`

### SSE event types (agent message)

- `chunk` — streamed text
- `artifact` — structured result (`packages`, `food`, `itinerary`, `profile`)
- `journey` — planning progress / trip pack ready
- `tool_start` / `tool_end` — specialist tool labels
- `done` — final thread state

---

## Trip pack

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/trip-pack/summary` | Yes | Aggregated profile + all planner artifacts |
| GET | `/trip-pack/pdf` | Yes | Download PDF (requires `trip_pack_ready`) |
| POST | `/trip-pack/email` | Yes | Email PDF attachment (on-demand) |

Email body optional: `{ "email": "override@example.com" }` — defaults to profile email.

---

## Chat (classic concierge)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/chat/session/start` | Yes | New concierge session |
| GET | `/chat/session/{session_id}` | Yes | Session state |
| POST | `/chat/message` | Yes | **SSE** guest message |
| GET | `/chat/history/{session_id}` | Yes | Paginated history |
| POST | `/chat/session/{session_id}/end` | Yes | End session |

WebSocket (optional): `ws://{bff}/ws/chat/{session_id}?token=<jwt>`

---

## Recommendations (session-scoped)

| Method | Path | Auth |
|--------|------|------|
| GET | `/recommendations/packages/{session_id}` | Yes |
| GET | `/recommendations/food/{session_id}` | Yes |
| GET | `/recommendations/itinerary/{session_id}` | Yes |

Used by classic chat right panel; Agent Hub uses thread artifacts instead.

---

## Feedback

| Method | Path | Auth | Role |
|--------|------|------|------|
| POST | `/feedback/submit` | Yes | guest |
| GET | `/feedback/summary` | Yes | owner |
| GET | `/feedback/flagged` | Yes | owner |
| POST | `/feedback/flag/{feedback_id}` | Yes | owner |

---

## Error format

```json
{ "detail": "Human-readable message" }
```

Responses include `X-Request-ID` for log correlation.

---

## Rate limits (BFF)

| Scope | Limit |
|-------|-------|
| Global `/api/*` | 100 / 15 min per IP |
| `/api/auth/*` | 10 / min per IP |
| `/api/trip-pack/*` | Exempt from global limit |

Backend login lockout: 5 failed attempts / 15 min per account → HTTP 429.
