# routes/profile.py

## Responsibility

All profile-related HTTP endpoints: CellarTracker upload, seed-bottle inference, backup revert, summary.

## Endpoints

- **`POST /upload-profile`** → `UploadProfileResponse`
  Detects the export type via `profile.ingest_export`. 400 on parse failure or empty file, 413 on oversize. Persists raw bytes (`save_profile_export`), busts cache, and returns the freshly built Pydantic `TasteProfile`.

- **`POST /seed-profile`** → `UploadProfileResponse`
  Accepts a `SeedProfileRequest` (3–7 loved + 0–3 disliked wines). Calls `seed_profile.infer_profile_from_seeds(req, ANTHROPIC_API_KEY, ANTHROPIC_MODEL)`; on `(anthropic.APIError, RuntimeError, ValueError)` returns 502. On success, persists via `persist_seed_profile` (which backs up the existing profile), busts cache, and returns the inferred `TasteProfile` carrying `profile_source="seed_bottles"` + `inference_confidence`.

- **`POST /profile/revert`** → `{"message": ...}`
  Restores `profile_data.json` from `profile_data.backup.json`. 404 when no backup exists. Busts both the profile cache and the response cache on success.

- **`GET /profile-summary`** → `ProfileSummaryResponse`
  Builds the summary from `profile.load_profile_data` + `build_taste_profile`. Computes `taste_markers` either from the seed-derived dict or via `derive_taste_markers` from descriptors. Computes `cellar_stats` from the inventory bottles. For non-seed profiles, calls `enrich_profile_with_anthropic` to obtain `style_summary`; failures (APIError / ValueError / RuntimeError / Exception) are logged but non-fatal — `style_summary` falls back to None. Strips enrichment-only keys before splatting into the Pydantic response so extras don't fail validation.

## Dependencies

- `bootstrap.ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `MAX_UPLOAD_BYTES`
- `cache.bust_cache`
- `inventory.load_inventory`
- `models.{CellarStats, ProfileSummaryResponse, SeedProfileRequest, TasteMarkers, UploadProfileResponse}`
- `profile.{PROFILE_DATA_PATH, build_taste_profile, build_taste_profile_pydantic, bust_profile_cache, derive_taste_markers, enrich_profile_with_anthropic, ingest_export, load_profile_data, save_profile_export}`
- `seed_profile.infer_profile_from_seeds`, `persist_seed_profile`

## Patterns & Gotchas

- `_SEED_INFERENCE_ERRORS = (anthropic.APIError, RuntimeError, ValueError)` is defined once at module scope (replaces the old `anthropic_module_error_types()` helper that re-imported anthropic).
- `PROFILE_DATA_PATH` is imported at the top of the module (was previously a deferred in-function import in `main.py`).
