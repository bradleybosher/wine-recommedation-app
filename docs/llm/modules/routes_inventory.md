# routes/inventory.py

## Responsibility

Inventory HTTP endpoints. Registered on the app from `main.py` via `app.include_router(inventory_router)`.

## Endpoints

- **`POST /upload-inventory`** (`upload_inventory`) → `UploadInventoryResponse`
  Read uploaded CellarTracker TSV, enforce `MAX_UPLOAD_BYTES` (413 if exceeded), decode via `inventory.decode_cellartracker_upload`, persist via `inventory.save_inventory`, then `cache.bust_cache()`. Returns saved bottle count.

- **`GET /inventory`** (`get_inventory`) → `InventoryResponse`
  Loads `inventory.json` via `inventory.load_inventory`, returns bottles + `age_hours` + `stale` flag. Empty list when no inventory has been uploaded.

## Dependencies

- `bootstrap.MAX_UPLOAD_BYTES`
- `cache.bust_cache`
- `inventory.decode_cellartracker_upload`, `load_inventory`, `save_inventory`
- `models.Bottle`, `InventoryResponse`, `UploadInventoryResponse`
