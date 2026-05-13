"""Inventory routes: upload CellarTracker TSV, fetch current inventory."""
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from bootstrap import MAX_UPLOAD_BYTES
from cache import bust_cache
from inventory import decode_cellartracker_upload, load_inventory, save_inventory
from models import Bottle, InventoryResponse, UploadInventoryResponse

router = APIRouter()
logger = logging.getLogger("sommelier.api")


@router.post("/upload-inventory")
async def upload_inventory(file: UploadFile = File(...)) -> UploadInventoryResponse:
    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 20 MB.")
    text = decode_cellartracker_upload(raw)
    bottles = save_inventory(text)
    bust_cache()
    return UploadInventoryResponse(
        count=len(bottles),
        message=f"Saved {len(bottles)} bottles. Response cache cleared.",
    )


@router.get("/inventory")
def get_inventory() -> InventoryResponse:
    inv = load_inventory()
    if not inv:
        return InventoryResponse(bottles=[], age_hours=None, stale=False)

    bottles = [Bottle(**bottle) for bottle in inv.get("bottles", [])]
    return InventoryResponse(
        bottles=bottles,
        age_hours=inv.get("age_hours"),
        stale=inv.get("stale", False),
    )
