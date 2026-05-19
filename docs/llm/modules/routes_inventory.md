# routes/inventory.py

## Responsibility

Inventory HTTP endpoints. Registered on the app from `main.py` via `app.include_router(inventory_router)`.

## Authentication

Both endpoints require:
- **Bearer JWT** in the `Authorization` header (JWT token issued at registration/login)
- **`X-Profile-Id`** header specifying the active profile UUID

Per-request flow: `Depends(get_current_profile)` extracts the user_id from the JWT and loads the profile by ID from the `X-Profile-Id` header. The profile object is then passed to the endpoint handler.

## Endpoints

- **`POST /upload-inventory`** (`upload_inventory`) → `UploadInventoryResponse`
  Requires Bearer JWT + `X-Profile-Id` header. Extracts `profile` via `Depends(get_current_profile)`. Reads uploaded CellarTracker TSV, enforces `MAX_UPLOAD_BYTES` (413 if exceeded), decodes via `inventory.decode_cellartracker_upload`, persists via `inventory.save_inventory(profile.id, ...)`, then `cache.bust_cache()`. Returns saved bottle count.
  
  Inventory is stored at `backend/profiles/{profile_id}/inventory.json`.

- **`GET /inventory`** (`get_inventory`) → `InventoryResponse`
  Requires Bearer JWT + `X-Profile-Id` header. Extracts `profile` via `Depends(get_current_profile)`. Loads `inventory.json` for the active profile via `inventory.load_inventory(profile.id)`, returns bottles + `age_hours` + `stale` flag. Empty list when no inventory has been uploaded.

## Dependencies

- `bootstrap.MAX_UPLOAD_BYTES`
- `cache.bust_cache`
- `inventory.decode_cellartracker_upload`, `load_inventory`, `save_inventory`
- `models.Bottle`, `InventoryResponse`, `UploadInventoryResponse`
- `routes.auth.get_current_profile` — dependency injector for authenticated profile resolution
