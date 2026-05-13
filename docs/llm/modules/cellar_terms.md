# cellar_terms.py

## Responsibility

Pure helpers that turn raw cellar bottles into (a) a frequency-ranked list of terms (varietal + appellation tokens) and (b) an English sentence fragment describing the cellar's character. Consumed exclusively by `/recommend`.

## Public surface

- `inventory_terms_by_frequency(bottles: list[dict], limit: int = 10) -> list[str]` — Counter over `Varietal` and `Appellation` fields. Each raw value gets +3, each tokenised non-stopword (≥ 3 chars) gets +1. Returns the top-`limit` terms.
- `cellar_character_from_terms(terms: list[str]) -> str` — formats up to the top 5 terms into a sentence fragment ("skews heavily toward Pinot Noir and Chardonnay, with strong …"). Returns empty string when no terms.

## Constants

- `_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z\-']+")`.
- `_STOPWORDS` — small set of articles, prepositions, and generic wine words to suppress.

## Patterns & Gotchas

- No FastAPI surface — kept at top-level (not under `routes/`) so routes stay thin.
- The top-5 result feeds the `cellar_summary` prompt section; the top-10 result feeds inventory bottle filtering. Both share the same scoring.
