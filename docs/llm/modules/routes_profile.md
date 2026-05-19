# routes/profile.py

## Responsibility

All profile-related HTTP endpoints: CellarTracker upload, seed-bottle inference, backup revert, manual patch, summary. All endpoints require Bearer JWT + `X-Profile-Id` header and resolve the active profile via `Depends(get_current_profile)`.

## Authentication

All endpoints in this module require:
- **Bearer JWT** in the `Authorization` header (JWT token issued at registration/login)
- **`X-Profile-Id`** header specifying the active profile UUID

Per-request flow: `Depends(get_current_profile)` extracts the user_id from the JWT and loads the profile by ID. The profile object is then passed to each endpoint handler.

## Endpoints

- **`POST /upload-profile`** → `UploadProfileResponse`
  Requires Bearer JWT + `X-Profile-Id` header. Extracts `profile` via `Depends(get_current_profile)`. Detects the export type via `profile.ingest_export`. 400 on parse failure or empty file, 413 on oversize. Persists raw bytes via `save_profile_export(profile.id, ...)`, clears any `_overrides` via `_clear_profile_overrides(profile.id)` and any prior `_synthesized` via `clear_synthesized_profile(profile.id)`, busts cache, then calls `synthesize_palate_from_notes(profile_data, profile.id, ANTHROPIC_API_KEY, ANTHROPIC_MODEL)` and persists the result under `_synthesized` via `persist_synthesized_profile(profile.id, ...)` on success. Synthesis failure (caught via `_SYNTHESIS_ERRORS`) is logged and tolerated — the deterministic fallback in `build_taste_profile()` keeps the upload functional. The synthesis status (`"synthesized (confidence: ...)"` | `"failed (deterministic fallback active)"` | `"skipped"`) is appended to the response `message`. Returns the freshly built Pydantic `TasteProfile`.
  
  Profile data is stored at `backend/profiles/{profile_id}/profile_data.json`.

- **`POST /seed-profile`** → `UploadProfileResponse`
  Requires Bearer JWT + `X-Profile-Id` header. Extracts `profile` via `Depends(get_current_profile)`. Accepts a `SeedProfileRequest` (3–7 loved + 0–3 disliked wines). Calls `seed_profile.infer_profile_from_seeds(req, profile.id, ANTHROPIC_API_KEY, ANTHROPIC_MODEL)`; on `(anthropic.APIError, RuntimeError, ValueError)` returns 502. On success, persists via `persist_seed_profile(profile.id, ...)` (which backs up the existing profile), clears any `_overrides` from prior manual edits via `_clear_profile_overrides(profile.id)`, busts cache, and returns the inferred `TasteProfile` carrying `profile_source="seed_bottles"` + `inference_confidence`.

- **`POST /profile/revert`** → `{"message": ...}`
  Requires Bearer JWT + `X-Profile-Id` header. Extracts `profile` via `Depends(get_current_profile)`. Restores `profile_data.json` from `profile_data.backup.json` for the active profile via `restore_profile_backup(profile.id)`. 404 when no backup exists. Busts both the profile cache and the response cache on success.

- **`PATCH /profile`** → `ProfileSummaryResponse`
  Requires Bearer JWT + `X-Profile-Id` header. Extracts `profile` via `Depends(get_current_profile)`. Accepts a `ProfilePatchRequest` (any subset of `top_varietals`, `top_regions`, `preferred_descriptors`, `avoided_styles`, `avg_spend`, `style_summary`, `taste_markers`). Non-`None` fields are merged into `profile_data["_overrides"]` via `write_profile_data(profile.id, ...)`, then `build_taste_profile()` layers them on top of the derived/inferred base. 400 if the request body has no non-`None` fields. Busts profile + response caches and returns the freshly built `ProfileSummaryResponse`.

- **`GET /profile-summary`** → `ProfileSummaryResponse`
  Requires Bearer JWT + `X-Profile-Id` header. Extracts `profile` via `Depends(get_current_profile)`. Builds the summary from `profile.load_profile_data(profile.id)` + `build_taste_profile` (which now applies `_overrides`). `taste_markers` resolution: an explicit `taste_markers` dict on the merged profile (from seed inference, synthesized CT palate, OR a user override) wins verbatim; otherwise falls back to `derive_taste_markers` from descriptors. Computes `cellar_stats` from the inventory bottles. For profiles that are NOT seed-derived AND NOT synthesized AND have no user `style_summary` override, calls `enrich_profile_with_anthropic` (legacy fallback) to obtain `style_summary`; failures (APIError / ValueError / RuntimeError / Exception) are logged but non-fatal — `style_summary` falls back to None. `inference_confidence` is surfaced when `profile_source` is `seed_bottles` or `cellartracker_synthesized`.

## Helpers

- **`_clear_profile_overrides(profile_id)`** — module-private. Removes the `_overrides` key from `profile_data.json` for the given profile (no-op if absent) and busts the profile cache. Called by `/upload-profile` and `/seed-profile` because a full replacement of the underlying profile invalidates any previously layered manual edits.

## Dependencies

- `bootstrap.ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `MAX_UPLOAD_BYTES`
- `cache.bust_cache`
- `inventory.load_inventory`
- `models.{CellarStats, ProfileSummaryResponse, SeedProfileRequest, TasteMarkers, UploadProfileResponse}`
- `profile.{build_taste_profile, build_taste_profile_pydantic, bust_profile_cache, clear_synthesized_profile, derive_taste_markers, enrich_profile_with_anthropic, ingest_export, load_profile_data, persist_synthesized_profile, restore_profile_backup, save_profile_export, synthesize_palate_from_notes, write_profile_data}`
- `seed_profile.infer_profile_from_seeds`, `persist_seed_profile`
- `routes.auth.get_current_profile` — dependency injector for authenticated profile resolution

## Patterns & Gotchas

- `_SEED_INFERENCE_ERRORS = (anthropic.APIError, RuntimeError, ValueError)` is defined once at module scope (replaces the old `anthropic_module_error_types()` helper that re-imported anthropic). `_SYNTHESIS_ERRORS` is an alias for the same tuple — `synthesize_palate_from_notes()` raises the same set on failure.
- All profile data helpers (from `profile.py`) now accept `profile_id` as the first positional argument to scope operations to the active profile's directory (`backend/profiles/{profile_id}/`).
