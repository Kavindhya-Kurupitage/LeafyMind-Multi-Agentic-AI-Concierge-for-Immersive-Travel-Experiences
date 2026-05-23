# Problem 1-pager — Leafy Cave / LeafyMind

**Quest 2 · Day 1 · Discovery**  
**Date:** _[fill after interview]_  
**Client:** Leafy Cave Luxury Cabana — Pramitha Madushanka (Owner)  
**Location:** Wellawaya, Uva Province, Sri Lanka  
**Interviewer:** _[Your name]_

---

## Client in one sentence

Leafy Cave is a boutique luxury cabana serving **international tourists** who need warm, trustworthy guidance on **where to stay, what to eat, and what to do** around Wellawaya—not generic Sri Lanka advice from a single chatbot.

---

## Target user (primary)

| Attribute | Detail |
|-----------|--------|
| Who | Overseas guests (couples, families, small groups) booking 2–7 night stays |
| Context | Planning **before** arrival; limited local knowledge; anxiety about spice, culture, transport |
| Current behaviour | WhatsApp/email questions to owner; scattered Google searches; long back-and-forth |
| Success for guest | Confident plan in one sitting: package + food + day-by-day itinerary they can keep |
| Success for owner | Fewer repetitive DMs; higher conversion; consistent brand; captured feedback |

---

## Problem statement

**Before LeafyMind**, pre-arrival planning for Leafy Cave was:

1. **Manual and repetitive** — the owner answered the same questions (packages, diet, Ella vs Yala, spice levels) for every booking channel.
2. **Inconsistent** — recommendations depended on who replied and how much time they had.
3. **Not structured** — no single artefact guests could download or email before travel.
4. **Weak feedback loop** — post-stay opinions rarely captured in a structured way for improvement.

**Pain intensity:** High for owner (time); medium-high for guests (uncertainty before a long-haul trip).

---

## Interview notes (fill from real 30+ min session)

### Questions asked

1. Walk me through the last 3 guest bookings—where did questions come from and how long did planning take?
2. Which questions do you answer most often?
3. What packages do you never want shown to the wrong guest type?
4. What goes wrong when guests arrive unprepared (food, itinerary, expectations)?
5. What would “success” look like if a digital concierge worked well for 80% of guests?

### Key quotes (replace with real quotes)

> “_[Quote 1 — e.g. time spent on WhatsApp]_”

> “_[Quote 2 — e.g. wrong package shown to family]_”

> “_[Quote 3 — e.g. what guests ask about food/spice]_”

### Constraints discovered

- [ ] Must respect real package names and business rules (not hallucinated prices)
- [ ] Must feel **warm and Sri Lanka–aware**, not corporate
- [ ] Owner has limited time to maintain content—prefer DB + rules over manual copy each week
- [ ] _[Add client-specific constraints]_

---

## Hypothesis (Day 1)

If we give guests a **guided multi-agent hub** (profile → package → food → itinerary) with **rule-grounded recommendations** and a **branded trip-pack PDF**, then:

- Guest planning time drops from _[baseline X hours]_ to _[target <30 min]_ self-serve.
- Owner repetitive messages drop by _[target %]_.
- Guests arrive with clearer expectations (food spice, day plan).

---

## 5-day scope (explicit in / out)

### In scope (MVP)

| # | Feature |
|---|---------|
| 1 | Guest auth + profile builder (guided) |
| 2 | Package recommender with **business rules** (Love Nest, Together Time, custom fallback) |
| 3 | Food guide with **local photos** + Unsplash fallback |
| 4 | Itinerary with curated attractions + OpenTripMap discoveries |
| 5 | Trip pack PDF + on-demand email |
| 6 | Feedback collector + owner dashboard |
| 7 | Dockerized deploy path + documentation |

### Out of scope (v2)

- Payments / booking engine
- Multi-property chain support
- Sinhala/Tamil UI (English-first for international guests)
- Native mobile apps
- 24/7 human handoff chat to owner (escalation flag only)

---

## Success metrics (measurable)

| Metric | Baseline | Target (5-day MVP) | How to measure |
|--------|----------|---------------------|----------------|
| Time to first complete plan | _[e.g. 2h owner WhatsApp]_ | < 30 min self-serve | Loom + test user timing |
| Package match correctness | _[subjective %]_ | ≥ 90% on 5 test personas | `test_package_rules.py` + manual review |
| Planner completion rate | N/A | 3/3 planners in test script | `test_agent_hub_flow.py` |
| Trip pack generated | No | Yes (PDF + email) | Manual + API test |
| Owner would recommend | N/A | Yes (1-sentence feedback) | Client quote |

---

## Sign-off

| Role | Name | Date | Notes |
|------|------|------|-------|
| Client | Pramitha Madushanka | _____ | Scope agreed |
| Builder | _____ | _____ | Ready for Day 2 |
