# Testing Catalog

Canonical module → test-file map for the wine-recommendation-app. **Rule:** when you modify a module listed below, update (or add) the matching test file in the same change. New modules must land with at least one test file from this catalog.

Run everything:

```bash
.\backend\.venv\Scripts\python.exe -m pytest backend/tests
npm --prefix frontend test:run
```

LLM evaluations (separate, opt-in):

```bash
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/llm_evals -m replay   # offline, fixture-replay
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/llm_evals -m live     # bills; needs ANTHROPIC_API_KEY
```

---

## Backend — HIGH priority (pure, no LLM/IO)

These modules are deterministic and have no external dependencies. They drive the recommendation pipeline so regressions here silently degrade output quality.

| Module under test | Test file | Covers |
|---|---|---|
| [backend/synonyms.py](../../backend/synonyms.py) | `backend/tests/test_synonyms.py` | `expand_term` / `expand_terms` — grape & region expansion, sub-appellation cascade, alias → canonical lookup, unknown-term passthrough, dedup + first-seen ordering |
| [backend/palate_stats.py](../../backend/palate_stats.py) | `backend/tests/test_palate_stats.py` | `compute_palate_stats` frequency tables, sentiment lexicon, `aspirational_skew` derivation, `avoided_style_tokens` thresholds, empty-input behavior |
| [backend/retrieval.py](../../backend/retrieval.py) | `backend/tests/test_retrieval.py` | `rank_wine_list` tiered scoring (producer +2.0 / region +1.5 / grape +1.0 / style +0.5 / avoided −2.0), top-40 truncation, synonym-expanded matches, malformed-price tolerance, empty list |
| [backend/insights.py](../../backend/insights.py) | `backend/tests/test_insights.py` | `compute_drift_suggestions` <3 flights → empty, ≥30 % hit-rate threshold, omit-already-in-profile filter |
| [backend/cellar_terms.py](../../backend/cellar_terms.py) | `backend/tests/test_cellar_terms.py` | `inventory_terms_by_frequency` stopword filtering, `cellar_character_from_terms` top-5 sentence composition |
| [backend/auth.py](../../backend/auth.py) | `backend/tests/test_auth.py` | `hash_password` / `verify_password` round-trip, `create_access_token` / `decode_access_token` round-trip, expired token, tampered token, missing-subject, password-prehash boundary (>72 bytes) |
| [backend/rate_limit.py](../../backend/rate_limit.py) | `backend/tests/test_rate_limit.py` | sliding window: under-limit pass, exact-limit pass, over-limit reject, window expiry releases capacity |

## Backend — MEDIUM priority (route handlers; FastAPI `TestClient` + mocked LLM/cache)

Pattern: `monkeypatch` `llm_client.call_claude`, in-memory SQLite for `cache`, `tmp_path` for `PROFILES_DIR`. Mirror the layout from `backend/tests/test_openapi_sync.py`.

| Route | Test file | Covers |
|---|---|---|
| [backend/routes/auth.py](../../backend/routes/auth.py) | `backend/tests/routes/test_auth_routes.py` | `/auth/register` duplicate email → 409, orphan-profile claim path, fresh-profile path; `/auth/login` wrong password → 401, success returns token + default profile; `/auth/me`; `/auth/forgot-password` always 200; `/auth/reset-password` token expired / wrong / reused |
| [backend/routes/recommend.py](../../backend/routes/recommend.py) | `backend/tests/routes/test_recommend_routes.py` | TEST_MODE fixture short-circuit (5 fixtures), `_build_tasting_note_library` dedup, `source_mode="cellar"` skips parser, `bottle_count≥3` injects stretch slot, missing `X-Profile-Id` → 400/422 |
| [backend/routes/profile.py](../../backend/routes/profile.py) | `backend/tests/routes/test_profile_routes.py` | `GET /profile` shape, `PATCH /profile` overrides written to `_overrides`, `/upload-profile` clears `_overrides` and writes `_synthesized` |
| [backend/routes/inventory.py](../../backend/routes/inventory.py) | `backend/tests/routes/test_inventory_routes.py` | TSV upload happy path, malformed TSV → 400, profile scoping (cannot read another user's inventory) |
| [backend/routes/history.py](../../backend/routes/history.py) + [backend/routes/insights.py](../../backend/routes/insights.py) | `backend/tests/routes/test_history_insights_routes.py` | history scoped to active profile, insights requires ≥3 flights |
| [backend/dependencies.py](../../backend/dependencies.py) | `backend/tests/test_dependencies.py` | `get_current_user` missing/invalid JWT → 401, `get_current_profile` cross-user ownership → 403 |

## Backend — LOW priority (wrappers / composition)

| Module | Test file | Covers |
|---|---|---|
| [backend/recommender.py](../../backend/recommender.py) | `backend/tests/test_recommender_blend.py` | `_find_reference_bars` accent-normalized match, `_blend_bars` 50/50 math, missing-reference fallback, `_get_norm_reference` cache reuse + rebuild-on-source-change |
| [backend/wine_reviews.py](../../backend/wine_reviews.py) | `backend/tests/test_wine_reviews.py` | `lookup_critic` confident/no match + shared-connection arg, `_reviews_available` readiness probe runs once (cached), `enrich_critics` enriches only confident matches and opens a single connection for the whole flight |
| [backend/inventory.py](../../backend/inventory.py) | `backend/tests/test_inventory_terms.py` | pre-folded keyword constants stay in sync with `_WINE_STYLE_KEYWORDS`, `extract_terms_from_wine_list_text` returns canonical keyword accent-insensitively, empty-text passthrough |
| [backend/profile.py](../../backend/profile.py) | `backend/tests/test_profile_overrides.py` | `build_taste_profile` precedence `_synthesized > _inferred > deterministic`, `_overrides` layered on top, override-clear behavior |
| [backend/cache.py](../../backend/cache.py) | `backend/tests/test_cache_schema.py` | in-memory DB: users/profiles/flights CRUD, `claim_orphan_profile` idempotency, `password_reset_tokens` single-use enforcement |
| [backend/test_fixtures.py](../../backend/test_fixtures.py) | `backend/tests/test_test_fixtures.py` | each fixture deserializes against `RecommendationResponse` (catches schema drift) |

---

## Frontend (Vitest + React Testing Library, colocated)

Run: `npm --prefix frontend test:run`. Phase 0 scaffolding lives in `frontend/vitest.config.ts`, `frontend/src/test/setup.ts`, `frontend/src/test/mswHandlers.ts`.

| Subject | Test file | Covers |
|---|---|---|
| [frontend/src/client/configure.ts](../../frontend/src/client/configure.ts) | `frontend/src/client/configure.test.ts` | JWT header injection when token present, omission when absent, `X-Profile-Id` injection from store, 401 → logout handler fires |
| [frontend/src/state/authStore.tsx](../../frontend/src/state/authStore.tsx) | `frontend/src/state/authStore.test.tsx` | login persists token to localStorage, logout clears, 401 interceptor triggers logout, register flow, hydration from storage on mount |
| [frontend/src/state/profileStore.tsx](../../frontend/src/state/profileStore.tsx) | `frontend/src/state/profileStore.test.tsx` | active-profile reconciliation when active is deleted, fallback to default, CRUD round-trip via mocked SDK |
| [frontend/src/components/AuthGuard.tsx](../../frontend/src/components/AuthGuard.tsx) | `frontend/src/components/AuthGuard.test.tsx` | loading → renders nothing, unauthenticated → redirect to /login with `from` preserved, authenticated → renders children |
| [frontend/src/design/wineColor.ts](../../frontend/src/design/wineColor.ts) | `frontend/src/design/wineColor.test.ts` | palette derivation by keyword, region coord lookup, unknown-region fallback, drink-window calc bounds |
| [frontend/src/FileUploader.tsx](../../frontend/src/FileUploader.tsx) | `frontend/src/FileUploader.test.tsx` | rejects oversized file, rejects wrong MIME, base64 conversion success, drag-drop event handling |
| [frontend/src/UploadFlow.tsx](../../frontend/src/UploadFlow.tsx) | `frontend/src/UploadFlow.test.tsx` | step progression choose → upload → refine → done, error short-circuits flow |
| [frontend/src/pages/Login.tsx](../../frontend/src/pages/Login.tsx) | `frontend/src/pages/Login.test.tsx` | empty submit → validation error, server `detail` vs `msg` error extraction, redirect to `from` after success |

---

## Adding a new module

When adding a new backend module or frontend file with non-trivial logic, append a row to the table above and create the corresponding test file in the same PR. If the module is pure glue / Pydantic schema / log config, note it explicitly here as "no tests" with a one-line justification.
