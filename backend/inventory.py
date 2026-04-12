import csv
import io
import json
import time
import unicodedata
from pathlib import Path

_SOM_DIR = Path(__file__).resolve().parent
CACHE_PATH = _SOM_DIR / "inventory.json"
CACHE_TTL  = 60 * 60 * 24 * 7  # 1 week — you trigger refresh manually


def decode_cellartracker_upload(raw: bytes) -> str:
    """CellarTracker tab exports are often Windows-1252, not UTF-8."""
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _quantity_positive(row: dict) -> bool:
    raw = row.get("Quantity", 0) or 0
    try:
        return float(str(raw).strip()) > 0
    except (ValueError, TypeError):
        return False


def parse_ct_csv(csv_text: str) -> list[dict]:
    # CT exports TSV not CSV
    reader = csv.DictReader(io.StringIO(csv_text), delimiter="\t")
    return [row for row in reader if _quantity_positive(row)]

def save_inventory(csv_text: str) -> list[dict]:
    bottles = parse_ct_csv(csv_text)
    CACHE_PATH.write_text(json.dumps({
        "bottles": bottles,
        "saved_at": time.time()
    }))
    return bottles

def load_inventory() -> dict | None:
    if not CACHE_PATH.exists():
        return None
    data = json.loads(CACHE_PATH.read_text())
    age_hours = (time.time() - data["saved_at"]) / 3600
    return {
        "bottles": data["bottles"],
        "age_hours": round(age_hours, 1),
        "stale": age_hours > 168
    }


def _fold_for_match(text: str) -> str:
    """Lowercase and strip accents so e.g. côte-rôtie matches cote-rotie in exports."""
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFD", text.casefold())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def get_relevant_bottles(bottles: list[dict], style_terms: list[str]) -> list[dict]:
    style_map = {
        "burgundy":   ["pinot noir", "burgundy", "bourgogne", "gevrey", "chambolle"],
        "chablis":    ["chablis", "chardonnay"],
        "champagne":  ["champagne", "blanc de noirs", "crémant"],
        "nebbiolo":   ["nebbiolo", "barolo", "barbaresco"],
        "chenin":     ["chenin", "vouvray", "savennières"],
        "rhone":      ["syrah", "grenache", "côte-rôtie", "hermitage"],
        "loire":      ["cabernet franc", "chinon", "bourgueil"],
        "beaujolais": ["gamay", "beaujolais", "morgon", "moulin"],
    }
    terms = [t.lower() for t in style_terms]
    keywords = []
    for t in terms:
        keywords += style_map.get(t, [t])

    if not keywords:
        return list(bottles)

    folded_keywords = [_fold_for_match(kw) for kw in keywords]

    def matches(b):
        haystack_raw = " ".join(
            str(b.get(k) or "")
            for k in ("Varietal", "Appellation", "Wine", "Producer")
        )
        hay = _fold_for_match(haystack_raw)
        return any(fk in hay for fk in folded_keywords if fk)

    return [b for b in bottles if matches(b)]