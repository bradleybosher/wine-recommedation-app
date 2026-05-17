"""Wine review lookup from the Wine Enthusiast public dataset (~130K reviews).

Seeded once into SQLite from backend/data/wine_reviews.csv (auto-downloaded on
first startup). At recommendation time, each wine is matched against the dataset
by winery keyword + vintage window + wine-name word overlap. A confident match
replaces Claude's estimated critic score with a real published reviewer score.

Matching is intentionally conservative (threshold 0.75 word overlap) to avoid
false-positive substitutions.
"""

import csv
import logging
import re
import sqlite3
import unicodedata
import urllib.request
from pathlib import Path
from typing import Optional

from models import Critic

logger = logging.getLogger("sommelier.wine_reviews")

_BACKEND_DIR = Path(__file__).resolve().parent
_DATA_FILE = _BACKEND_DIR / "data" / "wine_reviews.csv"
_DB_PATH = str(_BACKEND_DIR / "cellar.db")

_CSV_URL = (
    "https://raw.githubusercontent.com/rfordatascience/tidytuesday"
    "/master/data/2019/2019-05-28/winemag-data-130k-v2.csv"
)

# Common winery name prefixes that aren't distinctive for matching
_PREFIXES = frozenset({
    "chateau", "domaine", "maison", "tenuta", "cantina", "bodega", "bodegas",
    "estate", "weingut", "the", "les", "von", "vini", "cave", "caves",
    "clos", "mas", "quinta",
})

_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS wine_reviews (
    id      INTEGER PRIMARY KEY,
    winery  TEXT NOT NULL,
    title   TEXT NOT NULL,
    vintage INTEGER,
    points  INTEGER NOT NULL,
    taster  TEXT
)
"""
_INDEX_DDL = (
    "CREATE INDEX IF NOT EXISTS idx_wr_winery ON wine_reviews (lower(winery))"
)

_MATCH_THRESHOLD = 0.75


def _normalize(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s.lower())).strip()


def _extract_vintage(title: str) -> Optional[int]:
    m = re.search(r"\b(19[5-9]\d|20[012]\d)\b", title)
    return int(m.group(1)) if m else None


def _distinctive_word(producer: str) -> str:
    """First non-prefix word (>=4 chars) from a producer name, used for SQL pre-filter."""
    words = _normalize(producer).split()
    for w in words:
        if w not in _PREFIXES and len(w) >= 4:
            return w
    return words[-1] if words else ""


def _word_overlap(wine_name: str, title: str) -> float:
    """Fraction of significant wine_name words (>=4 chars) found in title."""
    qwords = {w for w in _normalize(wine_name).split() if len(w) >= 4}
    twords = set(_normalize(title).split())
    if not qwords:
        return 0.0
    return len(qwords & twords) / len(qwords)


def _download_csv() -> bool:
    """Download the Wine Enthusiast dataset CSV (~56 MB). Returns True on success."""
    _DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        logger.info("wine_reviews: downloading dataset from GitHub (~56 MB) …")
        urllib.request.urlretrieve(_CSV_URL, _DATA_FILE)
        logger.info("wine_reviews: download complete → %s", _DATA_FILE)
        return True
    except Exception as exc:
        logger.warning("wine_reviews: download failed (%s); critic lookup disabled", exc)
        return False


def seed_wine_reviews() -> None:
    """Create wine_reviews table and seed from CSV if not already done.

    Called once at server startup. If the CSV is absent it is auto-downloaded
    (~56 MB, one-time). Subsequent starts skip seeding when the table already
    has rows.
    """
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute(_TABLE_DDL)
        conn.execute(_INDEX_DDL)
        count = conn.execute("SELECT COUNT(*) FROM wine_reviews").fetchone()[0]
        if count > 0:
            logger.info("wine_reviews: already seeded (%d rows)", count)
            return

    if not _DATA_FILE.exists():
        if not _download_csv():
            return

    rows: list[tuple] = []
    with open(_DATA_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                points = int(row["points"])
                winery = (row.get("winery") or "").strip()
                title = (row.get("title") or "").strip()
                if not winery or not title or not points:
                    continue
                rows.append((
                    winery,
                    title,
                    _extract_vintage(title),
                    points,
                    (row.get("taster_name") or None),
                ))
            except (ValueError, KeyError):
                continue

    with sqlite3.connect(_DB_PATH) as conn:
        conn.executemany(
            "INSERT INTO wine_reviews (winery, title, vintage, points, taster)"
            " VALUES (?,?,?,?,?)",
            rows,
        )
    logger.info("wine_reviews: seeded %d rows", len(rows))


def lookup_critic(
    wine_name: str,
    producer: Optional[str],
    vintage: Optional[int],
) -> Optional[Critic]:
    """Return a real Wine Enthusiast score for a wine, or None if no confident match.

    Strategy:
      1. SQL pre-filter by the producer's most distinctive word (winery LIKE)
         plus a ±1 year vintage window when a vintage is known.
      2. Python word-overlap check: fraction of significant wine_name words
         (>=4 chars) that appear in the dataset title.
      3. Accept only matches at or above _MATCH_THRESHOLD (0.75).
    """
    key_word = _distinctive_word(producer or wine_name)
    if not key_word:
        return None

    try:
        with sqlite3.connect(_DB_PATH) as conn:
            tbl = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='wine_reviews'"
            ).fetchone()
            if not tbl:
                return None
            if conn.execute("SELECT COUNT(*) FROM wine_reviews").fetchone()[0] == 0:
                return None

            if vintage:
                candidates = conn.execute(
                    "SELECT winery, title, vintage, points, taster FROM wine_reviews"
                    " WHERE lower(winery) LIKE ?"
                    "   AND (vintage IS NULL OR abs(vintage - ?) <= 1)",
                    (f"%{key_word}%", vintage),
                ).fetchall()
            else:
                candidates = conn.execute(
                    "SELECT winery, title, vintage, points, taster FROM wine_reviews"
                    " WHERE lower(winery) LIKE ?",
                    (f"%{key_word}%",),
                ).fetchall()
    except Exception as exc:
        logger.warning("wine_reviews: lookup error: %s", exc)
        return None

    if not candidates:
        return None

    best_overlap = 0.0
    best_points: Optional[int] = None
    best_taster: Optional[str] = None

    for _winery, title, _row_vintage, points, taster in candidates:
        overlap = _word_overlap(wine_name, title)
        if overlap > best_overlap:
            best_overlap = overlap
            best_points = points
            best_taster = taster

    if best_overlap < _MATCH_THRESHOLD or best_points is None:
        return None

    source = f"Wine Enthusiast ({best_taster})" if best_taster else "Wine Enthusiast"
    logger.debug(
        "wine_reviews: matched producer=%r wine=%r vintage=%r overlap=%.2f pts=%d",
        producer, wine_name, vintage, best_overlap, best_points,
    )
    return Critic(score=float(best_points), source=source)


def enrich_critics(recommendation) -> None:
    """Replace each wine's critic field with a real dataset score where available.

    Wines that don't match the dataset keep whatever Claude returned (including
    None). Only overwrites with a real score when a confident match is found.
    """
    for wine in recommendation.recommendations:
        real = lookup_critic(wine.wine_name, wine.producer, wine.vintage)
        if real is not None:
            wine.critic = real
