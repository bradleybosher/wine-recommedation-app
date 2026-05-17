# Module: wine_reviews.py

Provides a one-time-seeded SQLite lookup against the Wine Enthusiast public review
dataset (~130 K reviews). At recommendation time, each recommended wine is matched
and its `critic` field is replaced with a real published score where the match is
confident enough.

## Why it exists

Claude's `critic` field is explicitly AI-estimated and frequently hallucinated.
This module substitutes verified Wine Enthusiast scores (real reviewer, real points)
for wines that can be confidently matched, without adding any external API dependency
or rate-limit exposure.

## Dataset

- **Source:** Wine Enthusiast magazine reviews (~130 K rows, vintage 2017–2019)
- **Origin URL:** `rfordatascience/tidytuesday` GitHub (auto-downloaded on first startup)
- **Local path:** `backend/data/wine_reviews.csv` (gitignored)
- **SQLite table:** `wine_reviews` in `cellar.db`
- **Columns stored:** `winery`, `title`, `vintage`, `points`, `taster`

## Startup flow

`seed_wine_reviews()` is called from `main.py` after `init_db()`:

1. Creates `wine_reviews` table + winery index in `cellar.db` if absent.
2. Checks row count — skips seeding if > 0 (subsequent restarts are instant).
3. If CSV absent, downloads it from GitHub (~56 MB, one-time, ~10–30 s).
4. Parses CSV, extracts vintage from `title`, inserts rows.

## Matching algorithm (`lookup_critic`)

```
producer → _distinctive_word() → SQL WHERE lower(winery) LIKE '%word%'
vintage  → AND abs(vintage - ?) <= 1   (when vintage is known)
wine_name words ≥4 chars → word_overlap with each candidate title
Accept if overlap >= 0.75
```

`_distinctive_word` strips common prefixes (`chateau`, `domaine`, `tenuta`, etc.)
so "Château Margaux" → `"margaux"` as the SQL key.

`_word_overlap` counts significant wine-name words (≥4 chars) found in the title.
Only wine_name words are counted (not producer words) so the producer filter (SQL)
and name filter (Python) stay independent.

## Enrichment hook (`enrich_critics`)

Called from `routes/recommend.py` immediately after `get_recommendation()` returns,
before scoring and flight persistence. Non-fatal — any exception is caught and
logged as a warning; the recommendation proceeds unchanged.

Wines that don't match keep whatever Claude returned (including `None`). The dataset
score only replaces Claude's estimate when overlap ≥ 0.75.

## Key constants

| Constant | Value | Purpose |
|---|---|---|
| `_MATCH_THRESHOLD` | 0.75 | Minimum word-overlap to accept a match |
| `_CSV_URL` | GitHub raw URL | Auto-download source |
| `_PREFIXES` | set of 14 words | Skipped when selecting SQL key word |
