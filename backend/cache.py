import logging, shutil, sqlite3, hashlib, json, time, uuid
from pathlib import Path
from typing import Optional

from bootstrap import ORPHAN_PROFILE_ID, PROFILES_DIR
from models import FlightFeedback

logger = logging.getLogger(__name__)

CACHE_TTL_HOURS: int = 24  # 24 hours

_SOM_DIR = Path(__file__).resolve().parent
DB_PATH = str(_SOM_DIR / "cellar.db")

def _conn():
    return sqlite3.connect(DB_PATH)


def _column_exists(c: sqlite3.Connection, table: str, column: str) -> bool:
    rows = c.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


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
        if not _column_exists(c, "flights", "profile_id"):
            c.execute("ALTER TABLE flights ADD COLUMN profile_id TEXT")
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            TEXT PRIMARY KEY,
                email         TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at    REAL NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id          TEXT PRIMARY KEY,
                user_id     TEXT,
                name        TEXT NOT NULL,
                is_default  INTEGER NOT NULL DEFAULT 0,
                created_at  REAL NOT NULL
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_flights_profile_id ON flights(profile_id)")

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
    profile_id: str,
) -> str:
    flight_id = uuid.uuid4().hex
    with _conn() as c:
        c.execute(
            "INSERT INTO flights "
            "(id, created_at, occasion, menu, cellar_leans, temperament, ceiling, "
            "bottle_count, source_mode, wine_list_hash, profile_hash, response_json, profile_id) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                flight_id, time.time(), occasion, menu, cellar_leans, temperament,
                ceiling, bottle_count, source_mode, wine_list_hash, profile_hash,
                response.model_dump_json(), profile_id,
            ),
        )
    return flight_id


def list_flights(profile_id: str, limit: int = 50, offset: int = 0) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, created_at, occasion, menu, response_json, bottle_count "
            "FROM flights WHERE profile_id = ? "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (profile_id, limit, offset),
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
            "ceiling, bottle_count, source_mode, wine_list_hash, profile_hash, response_json, profile_id "
            "FROM flights WHERE id = ?",
            (flight_id,),
        ).fetchone()
    if not row:
        return None
    keys = [
        "id", "created_at", "occasion", "menu", "cellar_leans", "temperament",
        "ceiling", "bottle_count", "source_mode", "wine_list_hash", "profile_hash", "response_json", "profile_id",
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


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def _user_row_to_dict(row: tuple) -> dict:
    return {"id": row[0], "email": row[1], "password_hash": row[2], "created_at": row[3]}


def create_user(email: str, password_hash: str) -> dict:
    user_id = uuid.uuid4().hex
    created_at = time.time()
    with _conn() as c:
        c.execute(
            "INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (user_id, email, password_hash, created_at),
        )
    return {"id": user_id, "email": email, "password_hash": password_hash, "created_at": created_at}


def get_user_by_email(email: str) -> Optional[dict]:
    with _conn() as c:
        row = c.execute(
            "SELECT id, email, password_hash, created_at FROM users WHERE email = ?", (email,)
        ).fetchone()
    return _user_row_to_dict(row) if row else None


def get_user_by_id(user_id: str) -> Optional[dict]:
    with _conn() as c:
        row = c.execute(
            "SELECT id, email, password_hash, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return _user_row_to_dict(row) if row else None


def count_users() -> int:
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM users").fetchone()[0]


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

def _profile_row_to_dict(row: tuple) -> dict:
    return {
        "id": row[0],
        "user_id": row[1],
        "name": row[2],
        "is_default": bool(row[3]),
        "created_at": row[4],
    }


def create_profile(user_id: str, name: str, is_default: bool = False, profile_id: Optional[str] = None) -> dict:
    pid = profile_id or uuid.uuid4().hex
    created_at = time.time()
    with _conn() as c:
        if is_default:
            c.execute("UPDATE profiles SET is_default = 0 WHERE user_id = ?", (user_id,))
        c.execute(
            "INSERT INTO profiles (id, user_id, name, is_default, created_at) VALUES (?, ?, ?, ?, ?)",
            (pid, user_id, name, 1 if is_default else 0, created_at),
        )
    return {"id": pid, "user_id": user_id, "name": name, "is_default": is_default, "created_at": created_at}


def list_profiles_for_user(user_id: str) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, user_id, name, is_default, created_at FROM profiles "
            "WHERE user_id = ? ORDER BY is_default DESC, created_at ASC",
            (user_id,),
        ).fetchall()
    return [_profile_row_to_dict(r) for r in rows]


def get_profile(profile_id: str) -> Optional[dict]:
    with _conn() as c:
        row = c.execute(
            "SELECT id, user_id, name, is_default, created_at FROM profiles WHERE id = ?",
            (profile_id,),
        ).fetchone()
    return _profile_row_to_dict(row) if row else None


def update_profile(profile_id: str, name: Optional[str] = None) -> Optional[dict]:
    if name is None:
        return get_profile(profile_id)
    with _conn() as c:
        c.execute("UPDATE profiles SET name = ? WHERE id = ?", (name, profile_id))
    return get_profile(profile_id)


def set_default_profile(profile_id: str, user_id: str) -> None:
    with _conn() as c:
        c.execute("UPDATE profiles SET is_default = 0 WHERE user_id = ?", (user_id,))
        c.execute(
            "UPDATE profiles SET is_default = 1 WHERE id = ? AND user_id = ?",
            (profile_id, user_id),
        )


def delete_profile(profile_id: str) -> bool:
    """Remove a profile row, its flights, and its on-disk JSON directory.

    Caller must enforce ownership before invoking.
    """
    with _conn() as c:
        c.execute("DELETE FROM flights WHERE profile_id = ?", (profile_id,))
        c.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        deleted = c.total_changes > 0
    profile_dir = PROFILES_DIR / profile_id
    if profile_dir.exists():
        shutil.rmtree(profile_dir, ignore_errors=True)
    return deleted


def get_orphan_profile() -> Optional[dict]:
    """Return the unclaimed migration profile (user_id IS NULL), if any."""
    with _conn() as c:
        row = c.execute(
            "SELECT id, user_id, name, is_default, created_at FROM profiles "
            "WHERE user_id IS NULL LIMIT 1"
        ).fetchone()
    return _profile_row_to_dict(row) if row else None


def claim_orphan_profile(user_id: str) -> Optional[str]:
    """Attach the orphan profile (if any) to ``user_id`` and mark it default.

    Returns the claimed profile_id, or None if no orphan exists.
    """
    orphan = get_orphan_profile()
    if not orphan:
        return None
    with _conn() as c:
        c.execute(
            "UPDATE profiles SET user_id = ?, is_default = 1 WHERE id = ?",
            (user_id, orphan["id"]),
        )
    return orphan["id"]


# ---------------------------------------------------------------------------
# Legacy data migration
# ---------------------------------------------------------------------------

def migrate_legacy_data() -> Optional[str]:
    """One-shot migration of pre-auth singleton data into an orphan profile.

    Moves backend/profile_data.json + backend/inventory.json into
    profiles/{ORPHAN_PROFILE_ID}/ and assigns any flights with NULL profile_id
    to that orphan. Idempotent — safe to call on every startup.

    Returns the orphan profile_id if a migration ran this call, else None.
    """
    legacy_profile = _SOM_DIR / "profile_data.json"
    legacy_inventory = _SOM_DIR / "inventory.json"
    legacy_profile_backup = _SOM_DIR / "profile_data.backup.json"

    has_legacy_files = legacy_profile.exists() or legacy_inventory.exists()
    has_orphan = get_orphan_profile() is not None
    has_unassigned_flights = False
    with _conn() as c:
        has_unassigned_flights = c.execute(
            "SELECT 1 FROM flights WHERE profile_id IS NULL LIMIT 1"
        ).fetchone() is not None

    if not has_legacy_files and has_orphan:
        return None
    if not has_legacy_files and not has_unassigned_flights:
        return None

    if not has_orphan:
        with _conn() as c:
            c.execute(
                "INSERT INTO profiles (id, user_id, name, is_default, created_at) "
                "VALUES (?, NULL, ?, 1, ?)",
                (ORPHAN_PROFILE_ID, "default", time.time()),
            )
        logger.info("migrate_legacy_data: created orphan profile id=%s", ORPHAN_PROFILE_ID)

    target_dir = PROFILES_DIR / ORPHAN_PROFILE_ID
    target_dir.mkdir(exist_ok=True)
    for src in (legacy_profile, legacy_inventory, legacy_profile_backup):
        if src.exists():
            dest = target_dir / src.name
            shutil.move(str(src), str(dest))
            logger.info("migrate_legacy_data: moved %s -> %s", src.name, dest)

    with _conn() as c:
        c.execute(
            "UPDATE flights SET profile_id = ? WHERE profile_id IS NULL",
            (ORPHAN_PROFILE_ID,),
        )
        if c.total_changes:
            logger.info("migrate_legacy_data: claimed %d unassigned flights", c.total_changes)

    return ORPHAN_PROFILE_ID