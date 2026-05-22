# LeafyMind Security

This document describes security controls for the LeafyMind MVP and how to report issues.

## Authentication flow

1. **Registration** — `POST /auth/register` with email, password, and full name. Passwords are hashed with **bcrypt** before storage. Password rules: minimum 8 characters, at least one uppercase letter and one digit.

2. **Login** — `POST /auth/login` returns a **JWT** (`access_token`) on success. Failed attempts are recorded in `login_attempts` (user ID, IP, timestamp, success flag).

3. **Account lockout** — After **5 failed login attempts within 15 minutes** for the same user, further attempts return **HTTP 429** with: `Too many attempts, try again in 15 minutes`.

4. **Authenticated requests** — Clients send `Authorization: Bearer <token>`. The backend validates signature, expiry, and checks the token’s `jti` against `revoked_tokens`.

5. **Logout** — `POST /auth/logout` inserts the token’s `jti` into `revoked_tokens`. The client must discard the token from storage.

6. **Password reset (MVP)** — `POST /auth/password-reset-request` generates a one-hour token (hashed in DB). At MVP, the plaintext token is **logged server-side** instead of emailed. `POST /auth/password-reset/confirm` validates the token and updates the password.

## Token lifecycle

| Stage | Detail |
|--------|--------|
| Creation | JWT includes `user_id`, `email`, `role`, `jti` (unique ID), and `exp` |
| Storage (client) | Browser `localStorage` key `leafymind_token` |
| Validation | Signature + expiry + `revoked_tokens` lookup |
| Revocation | Logout writes `jti` to `revoked_tokens` |
| Expiry | Configured via `JWT_EXPIRY_MINUTES` (default in `.env.example`) |

**Recommendation for production:** move tokens to **httpOnly Secure cookies**, shorten expiry, and add refresh tokens with rotation.

## Rate limiting policy

| Layer | Policy |
|--------|--------|
| BFF (Express) | 100 requests / 15 min per IP (global); 10 / min on `/api/auth/*` |
| Backend login | 5 failed attempts / 15 min per user account → HTTP 429 |

## Input validation and injection prevention

- All POST bodies use **Pydantic v2** models (no raw dict bodies on public routes).
- Chat messages: HTML stripped, **2000-character** cap, and `prompt_sanitizer.sanitize_user_input()` before LLM calls.
- Database access uses **SQLAlchemy ORM** (`select()` / mapped models). Migration SQL is static files only—no user input in SQL strings.
- API errors return generic messages; stack traces and file paths are **never** sent to clients.

## Request tracing

Every HTTP request receives an **`X-Request-ID`** (UUID). It is attached to responses and included in server logs for correlation.

## Docker

- Service containers run as **non-root** users (`appuser` / `appuser`).
- `.dockerignore` excludes `.env`, `node_modules`, `__pycache__`, and `.git` from images.

## Frontend security

- JWT cleared from `localStorage` on logout (and server revocation attempted).
- **Content-Security-Policy** meta tag in `index.html` restricts script, connect, and frame sources.
- Form fields use `maxLength`; registration/login inputs are sanitized before submit.
- Only `VITE_*` public config is used in the frontend—**no API keys** in client code.

## Known limitations 

- JWTs in `localStorage` are vulnerable to XSS; httpOnly cookies are not yet implemented.
- Password reset tokens are logged, not emailed.
- No CAPTCHA or device fingerprinting on login.
- `revoked_tokens` is not pruned automatically (grow over time; add TTL job in production).
- WebSocket auth uses query-string `?token=` (may appear in proxy logs).
- CSP allows `'unsafe-inline'` for Tailwind/Google Fonts in development builds.
- LLM prompt sanitisation is pattern-based and cannot guarantee complete injection resistance.

## Reporting vulnerabilities

If you discover a security issue, please **do not** open a public GitHub issue with exploit details.

Contact the maintainers privately with:

- Description and impact
- Steps to reproduce
- Affected component (frontend / BFF / backend)
- Optional proof-of-concept

We aim to acknowledge reports within **72 hours** and provide a remediation timeline when applicable.
