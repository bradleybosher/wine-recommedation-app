# Wine Recommender — Next-Level Recommendations

_Strategic review and prioritised next moves. Generated 2026-05-20. Audience: hiring portfolio reviewers — recommendations lean toward visible LLM-engineering maturity rather than product surface area. Production hardening (`docs/llm/improvement-backlog.md` P1) is out of scope for this plan; bundle separately._

---

## Context

The prototype is feature-complete against its stated MVP:

- JWT-auth multi-profile accounts with per-profile inventory + palate + flight history (`backend/routes/auth.py`, `backend/routes/profiles.py`, `backend/cache.py`).
- Two onboarding paths: CellarTracker TSV (synthesized palate via Claude) and 3–7 seed bottles (`backend/profile.py`, `backend/seed_profile.py`).
- Vision PDF parsing via Claude Haiku for scanned lists and photos (`backend/parser.py`).
- Recommendation via Claude Sonnet tool-use with structured `RecommendationResponse` (`backend/recommender.py`, `backend/prompt.py`).
- 4-dimension silent scorer + JSONL event logging (`backend/scorer.py`, `backend/logging_utils.py`).
- Four-screen Vinothèque UI through redesign Phase 4 — cellar anchor lead-in, grounding badge, structure comparison strip, feedback chips, profile deepening (`frontend/src/pages/{Preferences,Flight,Detail,Compare}.tsx`, `frontend/src/components/Flight/`).

The remaining gap between "working demo" and "engineered LLM product" is not features — it is the **engineering scaffolding around the LLM** (evals, telemetry, retrieval, feedback wiring). The four recommendations below close that gap.

---

## The four recommendations (in priority order)

### 1. LLM eval harness with a golden set + replay mode

**Why this first.** The scoring + JSONL logging already exist (`backend/scorer.py`, `backend/logging_utils.py`), but there is no harness that converts those scores into a CI signal. Today a prompt regression in `prompt.py` or a model swap in `ANTHROPIC_MODEL` is detected only by manual eyeballing. For a portfolio reviewer this is the single biggest gap between "demo" and "engineered LLM product."

**Approach.** Capture a ~12-case golden set of `(taste_profile_id, wine_list_fixture, meal_text, source_mode)` → expected structural properties (varietal overlap with profile, price band, no items already in cellar, grounding ≥ 0.8, no avoided-styles in top-3). Drive each case through the real `/recommend` pipeline with `TEST_MODE=true` for cheap cases and a separate `--live` flag for the costly ones. Add a **replay mode**: stash raw Claude tool-use payloads in `backend/tests/fixtures/llm_replay/` and let the harness re-run scoring + assertions against the cached payload without an API call — same code path as production via a `RECORDED_RESPONSES_DIR` env var that short-circuits `recommender._call_claude()`.

**Files & reuse.**
- New: `backend/tests/llm_evals/cases.json` (golden set), `backend/tests/llm_evals/test_recommendations.py` (pytest cases), `backend/tests/fixtures/llm_replay/*.json` (recorded payloads).
- Reuse: `backend/scorer.score_recommendation()` for assertion helpers; `backend/test_fixtures.py` (existing TEST_MODE fixtures — extend, don't replace); `backend/logging_utils.log_recommendation_event()` (extend with an `eval_case_id` field).
- Extend: `backend/recommender.py:242` — read an optional `_RECORDED_RESPONSES_DIR` env at module load; if set, replay `messages.create()` from JSON. Same shape, no Anthropic SDK changes.
- CI step: `pytest backend/tests/llm_evals -m replay` runs on every PR (no API key needed); `pytest -m live` runs nightly with `ANTHROPIC_API_KEY`.

**Verification.** Snapshot the current 12 cases as the baseline pass/fail. Deliberately weaken `prompt.py` (e.g. drop the taste_markers block) and confirm at least three cases regress with diagnostic output naming the failed dimension.

---

### 2. Closed feedback loop — chips drive palate drift suggestions

**Why.** `FlightFeedback` chips ("Too bold / Over budget / Off profile / Perfect") are already collected and persisted in the `flights.response` JSON blob (`docs/ux-improvement-plan.md` Phase A4 shipped). Today that data is a dead letter — nothing reads it. Wiring it into a `GET /profile/insights` endpoint that surfaces drift trends and one-click palate patches converts the existing plumbing into a learning system, which is the kind of vertical slice that demonstrates LLMOps thinking on a CV.

**Approach.** Aggregate the last N flights per profile from `flights` (already filtered by `profile_id`). Compute simple drift signals — e.g. "3 of last 5 flights tagged `too_bold` → suggest body marker −1," or "2 of last 4 flagged `over_budget` → suggest tightening `budget_max` to the 25th percentile of the recommended set." Return a list of `PalateDriftSuggestion { dimension, current, suggested, rationale, supporting_flight_ids }`. The frontend renders these as one-tap chips that PATCH `/profile` with the suggested patch — same wiring as the existing one-tap profile deepening (B5 in `docs/ux-improvement-plan.md`).

**Files & reuse.**
- New: `backend/insights.py` — `compute_drift_suggestions(profile_id) -> list[PalateDriftSuggestion]`. Pure function, no LLM call, deterministic.
- New: `backend/routes/insights.py` — `GET /profile/insights`.
- Extend: `backend/models.py` — add `PalateDriftSuggestion`, follow existing `ConfigDict(alias_generator=to_camel)` pattern.
- Frontend: extend `frontend/src/pages/Profile.tsx` (or `Flight.tsx` if you want it post-flight); reuse the chip styling from the existing feedback chip strip in `frontend/src/components/Flight/`.
- Reuse: `backend/cache.py` — `flights` table read helpers already exist.

**Verification.** Seed a profile with 5 flights, 4 marked `over_budget`. Hit `GET /profile/insights` → expect a `budget_max` suggestion with `supporting_flight_ids` of length 4. Click "Apply" → `PATCH /profile` succeeds, next call to `/insights` no longer returns the suggestion.

---

### 3. Retrieval-augmented prompting for large wine lists

**Why.** `HUMAN_NOTES.md:14–29` documents "poor match quality on large lists" as a known bug. The pipeline currently sends the entire `wine_list_text` (lexically filtered via `inventory.filter_wine_list`) into the recommendation prompt — a 200-line restaurant list eats tokens and dilutes Claude's attention across irrelevant entries. Pre-ranking by lightweight profile relevance and capping the prompt at the top ~40 candidates fixes the bug, cuts cost, and demonstrates a real retrieval design choice (which reviewers can latch onto on a portfolio call).

**Approach.** Split parsing into two stages already half-present:
1. `parser.parse_wine_list()` → already returns `wine_list_text`. Add `parse_wine_entries()` that returns a structured `list[WineListEntry { line, producer, name, region, vintage, price }]` using the same vision/text pass — Claude already emits per-line structure for vision PDFs, just keep it instead of joining.
2. New `backend/retrieval.py` with `rank_wine_entries(entries, profile, override_terms, limit=40) -> list[WineListEntry]`. Score each entry on: varietal overlap with `top_varietals`, region overlap with `top_regions`, price within `[budget_min*0.8, budget_max*1.2]`, descriptor token overlap with `preferred_descriptors`. Negative score for `avoided_styles` matches. Return top `limit`.
3. `routes/recommend.py` passes only the ranked subset into the prompt. If `len(entries) ≤ limit`, skip ranking (no behaviour change for small lists).

**Files & reuse.**
- Extend: `backend/parser.py` — add `parse_wine_entries()` alongside existing `parse_wine_list()`. Reuse the vision call path at `parser.py:140`.
- New: `backend/retrieval.py` — single pure function, mirrors the style of `backend/scorer.py`.
- Extend: `backend/routes/recommend.py` — call `rank_wine_entries` between parse and `recommender.get_recommendation()`.
- Reuse: `backend/inventory.get_relevant_bottles` (line 432) uses the same scoring shape — copy the patterns (term folding, profile-prefs dict) rather than re-inventing.
- Surface in eval (rec #1): add a `large_list` case to the golden set with a 200-line synthetic restaurant list; assert grounding doesn't drop below baseline despite the cap.

**Verification.** Pick a real 150+ entry wine list. Compare token counts in `logs/llm.log` before/after — expect ~70% reduction in user-payload tokens. Run the full golden set with retrieval on vs off; expect grounding and budget_fit to improve on the `large_list` case and stay flat on the small-list cases.

---

### 4. Cost / latency / token telemetry + a portfolio-visible debug surface

**Why.** Five Anthropic call sites exist (`recommender.py:242`, `seed_profile.py:127`, `parser.py:154`, `profile.py:581`, `profile.py:959`) but none capture the `response.usage` block. There is no answer to "what does a flight cost?" or "what's P90 latency?" — both routine questions in a portfolio interview. Adding structured telemetry is one afternoon; surfacing it in a tiny dashboard makes it visible to reviewers.

**Approach.**
1. Wrap every `client.messages.create(...)` call with a thin `call_claude(purpose, **kwargs)` helper in a new `backend/llm_client.py`. The helper times the call, records `usage.input_tokens` + `usage.output_tokens` + `model` + `purpose` (one of `recommend | enrich_profile | seed_profile | vision_parse | synthesize_palate`) and appends to a new `logs/llm_calls.jsonl`.
2. Extend `backend/logging_utils.log_recommendation_event()` to include aggregate `llm_calls: list[{purpose, ms, in_tokens, out_tokens}]` for the flight so each recommendation row in `recommendations.jsonl` is self-contained.
3. New `GET /debug/stats` endpoint (auth-gated like the existing `routes/debug.py`) returning P50/P90 latency per purpose, total tokens per day, cache hit ratio, total estimated cost using a configurable `MODEL_PRICING` dict in `bootstrap.py`.
4. New `frontend/src/pages/DebugStats.tsx` — a one-screen Vinothèque-styled grid (reuse `<PaperFrame>`, `INK`/`RULE` tokens) showing the same data. Behind the existing `VITE_SHOW_DEBUG` flag so it doesn't appear to end users.

**Files & reuse.**
- New: `backend/llm_client.py`, extend `backend/routes/debug.py`, new `frontend/src/pages/DebugStats.tsx`.
- Refactor (small): the five `messages.create()` call sites switch to `call_claude(purpose="...")`. Keep behaviour identical otherwise.
- Reuse: `backend/retry_utils.py` (already exists) — wrap inside `call_claude` so all five sites get retry for free, retiring the gap noted in `docs/llm/improvement-backlog.md` item 4.
- Reuse: `frontend/src/design/tokens.ts` for styling; do not introduce charting libraries — render numbers in a hairline table.

**Verification.** Run 5 flights. Check `logs/llm_calls.jsonl` has 5+ rows per flight (recommend + enrich + 0–N vision). Hit `/debug/stats` → returns sensible P50/P90. Verify the React page renders the same numbers behind `VITE_SHOW_DEBUG=true` and is hidden when the flag is off.

---

## Sequencing

Recommendations 1 and 4 are **prerequisites** for the others: rec #1 makes regressions visible, rec #4 makes cost/quality tradeoffs visible. Recommendations 2 and 3 are the substantive product wins that benefit from that scaffolding.

Suggested order:

1. **Week 1:** Rec #4 telemetry — one afternoon for `llm_client.py`, half a day for the debug page. Cheap, high leverage, unblocks everything.
2. **Week 1–2:** Rec #1 eval harness — start with replay mode (no API cost), then add `--live` cases. Pair with rec #4 since both touch the LLM call sites.
3. **Week 2–3:** Rec #3 retrieval — the only one that meaningfully changes recommendation quality. Validate on the golden set from rec #1.
4. **Week 3–4:** Rec #2 closed feedback loop — needs flight data to be meaningful, so leave for last so the demo has 10+ flights of feedback to draw on.

---

## Critical files to touch

| Concern | Files |
|---|---|
| Eval harness (#1) | `backend/tests/llm_evals/` (new), `backend/recommender.py:242`, `backend/test_fixtures.py`, `backend/logging_utils.py` |
| Feedback loop (#2) | `backend/insights.py` (new), `backend/routes/insights.py` (new), `backend/models.py`, `backend/cache.py`, `frontend/src/pages/Profile.tsx` |
| Retrieval (#3) | `backend/parser.py:140` (vision call), `backend/retrieval.py` (new), `backend/routes/recommend.py`, `backend/inventory.py:432` (pattern reference) |
| Telemetry (#4) | `backend/llm_client.py` (new), all five `messages.create()` sites, `backend/routes/debug.py`, `backend/bootstrap.py`, `frontend/src/pages/DebugStats.tsx` (new) |

---

## End-to-end verification

1. With `RECORDED_RESPONSES_DIR` set, `pytest backend/tests/llm_evals -m replay` runs in CI without an API key and passes all 12 baseline cases. Deliberately corrupt one fixture → corresponding case fails with a clear dimension name.
2. From the UI, run a flight, mark it `over_budget`, run two more flights with the same outcome. Load `/profile` → expect a "Tighten budget to $X?" suggestion. Click apply → budget updates, suggestion disappears.
3. Upload a 200-line wine list. Confirm `logs/llm.log` shows the trimmed payload (~40 entries). Confirm grounding score in `logs/recommendations.jsonl` is no worse than a smaller-list baseline.
4. Hit `/debug/stats` after running 5 mixed flights → all 5 purposes appear with non-zero token counts; P50 latency for `recommend` is below 10s.

---

## Docs to update on each rec landing (per `CLAUDE.md` Documentation Update Protocol)

- Rec #1: `docs/llm/modules/recommender.md`, `docs/llm/conventions.md` (add testing section).
- Rec #2: `docs/llm/modules/insights.md` (new), `docs/llm/interfaces.md`, `CLAUDE.md` Data Flow.
- Rec #3: `docs/llm/modules/parser.md`, `docs/llm/modules/retrieval.md` (new), `docs/llm/modules/routes_recommend.md`, `CLAUDE.md` Data Flow.
- Rec #4: `docs/llm/modules/llm_client.md` (new), `docs/llm/modules/routes_debug.md`, `docs/llm/interfaces.md`, `README.md` debug section.
