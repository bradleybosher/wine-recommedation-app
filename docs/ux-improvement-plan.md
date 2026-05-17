# UX Improvement Plan — High & Medium Impact Features

_Generated 2026-05-17. Implements the five features identified in the strategic app-vs-Claude review._

---

## Features

| # | Feature | Effort | Files |
|---|---------|--------|-------|
| 1 | Cellar anchor lead-in | Frontend only | `ListEntry.tsx`, `Detail.tsx` |
| 2 | Per-wine grounding badge | Backend + Frontend | `models.py`, `routes/recommend.py`, `ListEntry.tsx` |
| 3 | Structure comparison strip | Frontend only | new `StructureComparison.tsx`, `Flight.tsx` |
| 4 | Post-flight feedback chips | Backend + Frontend | `models.py`, `routes/history.py`, `cache.py`, `Flight.tsx` |
| 5 | One-tap profile deepening | Frontend only | `Flight.tsx` |

---

## Phase A — Backend Changes

> After all Phase A edits are committed, the user runs `sync_types.bat` before any frontend work begins.

### A1 — `backend/models.py` _(must complete before A2/A3/A4)_

- Add `verified_on_list: Optional[bool] = None` to `WineRecommendation`
  - Set server-side post-validation; `None` in cellar mode
- Add `flight_id: Optional[str] = None` to `RecommendationResponse`
  - Set in recommend route after `save_flight()` so frontend can reference the saved record
- Add new `FlightFeedback` model:
  ```python
  class FlightFeedback(BaseModel):
      model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
      chip: str           # "too_bold" | "over_budget" | "off_profile" | "perfect"
      recorded_at: float  # unix timestamp
  ```
- Add `feedback: Optional[FlightFeedback] = None` to `FlightRecord`

### A2 — `backend/routes/recommend.py` _(after A1)_

After recommendations are validated and before saving the flight:
- For `source_mode="winelist"`: compute `verified_on_list` per wine using the substring / ≥75% token-overlap logic already in `scorer._score_grounding()`. Extract that check into a shared `_is_grounded(wine_name, list_text) -> bool` helper (keep it in `scorer.py`; import it here).
- Set `response.flight_id` after `save_flight()` returns the new row id.

### A3 — `backend/routes/history.py` _(after A1, parallel with A2/A4)_

Add endpoint:
```
PATCH /history/{flight_id}/feedback
Body: FlightFeedback
Response: 200 { "ok": true } | 404
```
Calls new `cache.update_flight_feedback()`.

### A4 — `backend/cache.py` _(after A1, parallel with A2/A3)_

Add `update_flight_feedback(flight_id: str, feedback: FlightFeedback) -> bool`:
- UPDATE the `response` JSON blob in the `flights` row to include `feedback` at top level.
- No new DB columns — serialise feedback inside the existing `response` JSON.
- Return `True` if row found and updated, `False` if not found.

---

## Phase B — Frontend Changes

> All Phase B work starts only after `sync_types.bat` has been run.

### B1+B2 — `frontend/src/components/Flight/ListEntry.tsx`

**Cellar anchor lead-in (B1):**
- Extract first sentence of `wine.reasoning` (split on `". "`, take index 0).
- If it starts with `"Like your"` → render with `OXBLOOD` accent color, preceded by a 1px `RULE` hairline.
- Otherwise → render in `INK_SOFT` italic as a profile-fit lead sentence.
- Position: between the producer/vintage line and the palate paragraph in column 2.

**Grounding badge (B2):**
- In column 3, directly below the price:
  - `verified_on_list === true` → `"✓ on list"` in `INK_SOFT`, micro, EB Garamond
  - `verified_on_list === false` → `"⚠ not verified"` in `OXBLOOD`, micro
  - `null/undefined` (cellar mode) → render nothing

### B1-Detail — `frontend/src/pages/Detail.tsx` _(parallel with B1+B2)_

- Same cellar anchor extraction as B1.
- Render the first reasoning sentence in the hero section above the main palate paragraph.
- Same conditional styling (accent if "Like your", INK_SOFT italic otherwise).

### B3+B4+B5 — `frontend/src/pages/Flight.tsx` + new component _(parallel with B1+B2 and B1-Detail)_

**New file: `frontend/src/components/Flight/StructureComparison.tsx` (B3)**

Props: `wines: EnrichedWine[]`

A 5-row × N-column matrix:
```
                  Wine 1    Wine 2    Wine 3
tannin            ████░░    ███░░░    █████░
acidity           █████░    ████░░    ██░░░░
body              ████░░    ████░░    ███░░░
sweetness         █░░░░░    ██░░░░    █░░░░░
oak               ███░░░    █░░░░░    █░░░░░
```
- Row labels: EB Garamond italic, `typeScale.label`, left column
- Wine name headers: Cormorant Garamond, `typeScale.label`, `INK_SOFT`, abbreviated
- Bars: reuse the same SVG bar from `StructureBars.tsx` (same 200px viewBox, tick marks, filled rect)
- Bar fill color: `wine.color.accent` per wine
- Skip wines where `bars` is null; hide component entirely if fewer than 2 wines have bars

**Flight.tsx additions:**

Render `<StructureComparison wines={sortedWines} />` between the wine cards and the footer line.

**Feedback chips (B4):**

State: `feedbackChip: string | null` (null = not submitted yet)

Below the comparison strip:
```
How was the flight?   [Too bold]  [Over budget]  [Off profile]  [Perfect]
```
- Label: EB Garamond italic, `typeScale.label`, `INK_SOFT`
- Chips: 1px solid `RULE` border, no fill, no rounded corners, Cormorant Garamond, `typeScale.label`, `INK`
- On click: call `PATCH /history/{flightId}/feedback` via SDK; replace chips with `"Noted. Adjust your palate on the Profile page →"` (link to `/profile`)
- `flightId` sourced from `response.flight_id` (added in A1/A2)

**One-tap profile deepening (B5):**

On mount: fetch `GET /profile` alongside existing recommendation state.

Check:
- `topWine = sortedWines[0]`
- `topWine.grape` is defined AND not already in `profile.top_varietals`

If true, render above the feedback strip:
```
Enjoying Nebbiolo?   [Add to your profile]   [Dismiss]
```
- Same chip styling as B4
- On "Add": `PATCH /profile { topVarietals: [...profile.top_varietals, topWine.grape] }` → replace with `"Nebbiolo added. ✓"` (fades after 3s)
- On "Dismiss": hide without API call

---

## Parallel Execution Map

```
Round 1 ─────────────────────────────────────────────────
  Agent 1: A1 — models.py   (sequential prerequisite)

Round 2 ─────────────────────────────────────────────────
  Agent 2: A2 — routes/recommend.py   ┐
  Agent 3: A3 — routes/history.py     ├── all parallel, all depend on A1
  Agent 4: A4 — cache.py              ┘

  ↓ user runs sync_types.bat ↓

Round 3 ─────────────────────────────────────────────────
  Agent 5: ListEntry.tsx (B1 + B2)         ┐
  Agent 6: Detail.tsx (B1-Detail)           ├── all parallel, touch different files
  Agent 7: StructureComparison.tsx          │
           + Flight.tsx (B3 + B4 + B5)     ┘
```

**Why B3/B4/B5 must share one agent:** All three write to `Flight.tsx`. Splitting them across agents would cause merge conflicts on that file.

**Why A2/A3/A4 are safe to parallelise:** They modify three distinct files (`routes/recommend.py`, `routes/history.py`, `cache.py`) with no shared state.

---

## Verification Checklist

1. **Cellar anchor** — Run winelist recommendation with inventory containing stylistic matches. Confirm "Like your…" renders prominently in ListEntry and Detail with accent colour.
2. **Grounding badge** — Winelist mode: each card shows `✓ on list`. Cellar mode: no badge. Force a grounding miss via TEST_MODE to verify warning state.
3. **Structure strip** — Confirm 5×3 matrix appears on Flight below wine cards, bars coloured per wine palette. Confirm hidden when fewer than 2 wines have bars data.
4. **Feedback chips** — Click any chip, verify `PATCH /history/{id}/feedback` returns 200, verify chips replaced by confirmation text, verify feedback persists on `GET /history/{id}`.
5. **Profile deepening** — Load flight where rank-1 grape is absent from `top_varietals`. Confirm callout appears. Click "Add". Verify PATCH succeeded and Profile page shows the new varietal.

---

## Post-Implementation Docs (mandatory per CLAUDE.md)

| Modified file | Update |
|---|---|
| `backend/models.py` | `docs/llm/modules/models.md` |
| `backend/routes/recommend.py` | `docs/llm/modules/routes_recommend.md` |
| `backend/routes/history.py` | `docs/llm/modules/history.md` |
| `backend/cache.py` | `docs/llm/modules/cache.md` |
| All of the above | `docs/llm/interfaces.md` |
