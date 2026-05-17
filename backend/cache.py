import sqlite3, hashlib, json, time, uuid
from pathlib import Path
from typing import Optional

from models import FlightFeedback

CACHE_TTL_HOURS: int = 24  # 24 hours

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
        c.execute("""
            CREATE TABLE IF NOT EXISTS flights (
                id            TEXT    PRIMARY KEY,
                created_at    REAL,
                occasion      TEXT,
                menu          TEXT,
                cellar_leans  TEXT,
                temperament   TEXT,
                ceiling       TEXT,
                bottle_count  INTEGER,
                source_mode   TEXT,
                wine_list_hash TEXT,
                profile_hash  TEXT,
                response_json TEXT
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


def save_flight(
    occasion: str,
    menu: str,
    cellar_leans: str,
    temperament: str,
    ceiling: str,
    bottle_count: int,
    source_mode: str,
    wine_list_hash: str,
    profile_hash: str,
    response,
) -> str:
    flight_id = uuid.uuid4().hex
    with _conn() as c:
        c.execute(
            "INSERT INTO flights VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                flight_id, time.time(), occasion, menu, cellar_leans, temperament,
                ceiling, bottle_count, source_mode, wine_list_hash, profile_hash,
                response.model_dump_json(),
            ),
        )
    return flight_id


def list_flights(limit: int = 50, offset: int = 0) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, created_at, occasion, menu, response_json, bottle_count "
            "FROM flights ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    result = []
    for flight_id, created_at, occasion, menu, response_json, bottle_count in rows:
        try:
            top_wine = json.loads(response_json)["recommendations"][0]["wine_name"]
        except Exception:
            top_wine = "Unknown"
        result.append(dict(
            id=flight_id, created_at=created_at, occasion=occasion or "",
            menu=menu or "", top_wine_name=top_wine, bottle_count=bottle_count,
        ))
    return result


def get_flight(flight_id: str) -> Optional[dict]:
    with _conn() as c:
        row = c.execute(
            "SELECT id, created_at, occasion, menu, cellar_leans, temperament, "
            "ceiling, bottle_count, source_mode, wine_list_hash, profile_hash, response_json "
            "FROM flights WHERE id = ?",
            (flight_id,),
        ).fetchone()
    if not row:
        return None
    keys = [
        "id", "created_at", "occasion", "menu", "cellar_leans", "temperament",
        "ceiling", "bottle_count", "source_mode", "wine_list_hash", "profile_hash", "response_json",
    ]
    return dict(zip(keys, row))


def delete_flight(flight_id: str) -> bool:
    with _conn() as c:
        c.execute("DELETE FROM flights WHERE id = ?", (flight_id,))
        return c.total_changes > 0


def update_flight_feedback(flight_id: str, feedback: FlightFeedback) -> bool:
    """Merge feedback into the response JSON blob of an existing flight row.

    No new columns — feedback is serialised inside the existing ``response_json`` field.
    Returns True if the row was found and updated, False if not found.
    """
    with _conn() as c:
        row = c.execute(
            "SELECT response_json FROM flights WHERE id = ?", (flight_id,)
        ).fetchone()
        if not row:
            return False
        data = json.loads(row[0])
        data["feedback"] = feedback.model_dump(by_alias=True)
        c.execute(
            "UPDATE flights SET response_json = ? WHERE id = ?",
            (json.dumps(data), flight_id),
        )
        return True