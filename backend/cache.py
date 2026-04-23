import sqlite3, hashlib, json, time
from pathlib import Path
from typing import Optional

CACHE_TTL_HOURS: int = 168  # 7 days

_SOM_DIR = Path(__file__).resolve().parent
DB_PATH = str(_SOM_DIR / "cellar.db")

def _conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS response_cache (
                key TEXT PRIMARY KEY,
                response TEXT,
                created_at REAL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS parse_cache (
                pdf_hash TEXT PRIMARY KEY,
                wine_list_text TEXT,
                created_at REAL
            )
        """)

def make_parse_key(pdf_bytes: bytes) -> str:
    return hashlib.sha256(pdf_bytes).hexdigest()

def get_parse_cached(pdf_hash: str) -> Optional[str]:
    with _conn() as c:
        row = c.execute(
            "SELECT wine_list_text, created_at FROM parse_cache WHERE pdf_hash = ?", (pdf_hash,)
        ).fetchone()
    if not row:
        return None
    wine_list_text, created_at = row
    if (time.time() - created_at) / 3600 > CACHE_TTL_HOURS:
        with _conn() as c:
            c.execute("DELETE FROM parse_cache WHERE pdf_hash = ?", (pdf_hash,))
        return None
    return wine_list_text

def set_parse_cached(pdf_hash: str, wine_list_text: str) -> None:
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO parse_cache VALUES (?, ?, ?)",
            (pdf_hash, wine_list_text, time.time())
        )

def make_key(image_bytes: bytes, meal: str, inventory_hash: str, profile_hash: str = "") -> str:
    h = hashlib.sha256()
    h.update(image_bytes)
    h.update(meal.encode())
    h.update(inventory_hash.encode())
    h.update(profile_hash.encode())
    return h.hexdigest()

def inventory_hash(bottles: list[dict]) -> str:
    return hashlib.md5(json.dumps(bottles, sort_keys=True).encode()).hexdigest()

def get_cached(key: str) -> Optional[str]:
    with _conn() as c:
        row = c.execute(
            "SELECT response, created_at FROM response_cache WHERE key = ?", (key,)
        ).fetchone()
    if not row:
        return None
    response, created_at = row
    if (time.time() - created_at) / 3600 > CACHE_TTL_HOURS:
        with _conn() as c:
            c.execute("DELETE FROM response_cache WHERE key = ?", (key,))
        return None
    return response

def set_cached(key: str, response: str):
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO response_cache VALUES (?, ?, ?)",
            (key, response, time.time())
        )

def purge_expired() -> int:
    cutoff = time.time() - CACHE_TTL_HOURS * 3600
    with _conn() as c:
        r1 = c.execute("DELETE FROM response_cache WHERE created_at < ?", (cutoff,))
        r2 = c.execute("DELETE FROM parse_cache WHERE created_at < ?", (cutoff,))
    return r1.rowcount + r2.rowcount


def bust_cache():
    """Call this after inventory refresh."""
    with _conn() as c:
        c.execute("DELETE FROM response_cache")
        c.execute("DELETE FROM parse_cache")