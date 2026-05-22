# Agent Hub

The Agent Hub (`/hub`) is the primary guided planning experience: five specialist cards, journey progress, and trip pack delivery.

---

## Agent order and locks

| Step | Agent ID | Required | Unlocks after |
|------|----------|----------|---------------|
| 1 | `profile_builder` | Yes | — (always available) |
| 2 | `package_recommender` | Optional | Profile complete |
| 3 | `food_guide` | Optional | Profile complete |
| 4 | `itinerary_planner` | Optional | Profile complete |
| 5 | `feedback_collector` | After planning | ≥1 planner **or** feedback email sent |

Step statuses: `locked` · `available` · `in_progress` · `completed`

---

## Guided interview flow

Each specialist (except feedback) uses **tap-through** steps defined in `backend/agents/guided_steps.py`:

- Profile Builder — 8 steps (group, style, budget, dietary, nights, etc.)
- Package — priorities then rule-based recommendations
- Food — spice tolerance, meal preferences
- Itinerary — pace, themes (nature, culture, adventure)

Messages are sent as:

```json
{
  "message": "",
  "guided_response": {
    "step_id": "group_type",
    "selected": ["couple"],
    "free_text": null
  }
}
```

---

## Artifacts storage

Thread artifacts are JSON on `agent_threads.artifacts`:

| Agent | Nested key | Key fields |
|-------|------------|------------|
| Profile | `profile` / guest_profile | `email`, `travel_style`, `group_type`, … |
| Package | `packages` | `recommendations[]`, `narrative` |
| Food | `food` | `must_try[]`, `safe_starter`, `narrative` |
| Itinerary | `itinerary` | `itinerary[]` (days), `total_estimated_cost_usd` |

Legacy flat artifacts are still read via `_planning_block()` in `journey_service.py`.

Food dishes may include `image.url` pointing to `/images/food/<file>.jpg` (served by Vite public folder).

---

## Package recommender rules

Implemented in `backend/rules/business_rules.py`:

- Canonical packages include **Love Nest Getaway**, **Together Time Package**, and others in `PACKAGE_NAMES`.
- `TRAVEL_STYLE_ALIASES` maps profile styles (`romance`, `nature`, …) to rule tags.
- `MIN_STRONG_MATCH_SCORE` (0.45) — below threshold → **custom** package name via `build_custom_package_name()`.
- Group-type guards prevent wrong packages (e.g. Love Nest not shown to families).

---

## Journey API

`GET /api/agents/journey` returns:

- `trip_pack_ready` — `true` when package + food + itinerary all have complete artifacts
- `trip_pack_planners_done` — per-planner boolean map
- `feedback_unlocked` — profile complete and at least one planner

---

## Completion side effects

When a planner finishes (`services/hub_feedback.py`):

1. Thread status → `completed`
2. Feedback session created/linked
3. **Feedback survey email** sent only when **all three** planners are done (not after the first)
4. SSE `journey` event includes `trip_pack_ready`, `planners_done_count`

---

## Frontend components

| Component | Path |
|-----------|------|
| Hub dashboard | `frontend/src/pages/AgentHubPage.jsx` |
| Workspace | `frontend/src/pages/AgentWorkspacePage.jsx` |
| Artifact sidebar | `frontend/src/components/agents/AgentArtifactPanel.jsx` |
| Trip pack panel | `frontend/src/components/agents/TripPackPanel.jsx` |

---

## Troubleshooting

| Issue | Check |
|-------|--------|
| Planner stuck “in progress” | Re-open thread; confirm last message has artifacts in Network tab |
| Trip pack not ready | All three agents show **Done** on hub; re-run agent if needed |
| No food photos | Local files in `frontend/public/images/food/` or `UNSPLASH_ACCESS_KEY` |
| Wrong package for group | Re-run package agent after profile fix; see business rules tests |

Run: `docker exec leafymind-backend python -m scripts.test_agent_hub_flow`
