"""Derive a short 'cellar character' phrase + frequency-ranked term list from
inventory bottles. Pure logic, no FastAPI surface. Consumed by /recommend."""
import re
from collections import Counter

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z\-']+")
_STOPWORDS = {
    "and", "the", "de", "du", "des", "di", "della", "delle", "del", "la", "le",
    "a", "to", "in", "for", "with", "sur", "superiore", "classico", "unknown",
    "rosso", "bianco", "blanc", "noir", "wine", "wines",
}


def _value_or_empty(v: object) -> str:
    return str(v or "").strip()


def inventory_terms_by_frequency(bottles: list[dict], limit: int = 10) -> list[str]:
    counts: Counter[str] = Counter()
    for bottle in bottles:
        for field in ("Varietal", "Appellation"):
            raw = _value_or_empty(bottle.get(field))
            if not raw:
                continue
            normalized = raw.lower()
            counts[normalized] += 3
            for token in _TOKEN_RE.findall(normalized):
                if len(token) < 3 or token in _STOPWORDS:
                    continue
                counts[token] += 1
    return [term for term, _ in counts.most_common(limit)]


def _display_term(term: str) -> str:
    return " ".join(w.capitalize() for w in term.replace("-", " ").split())


def cellar_character_from_terms(terms: list[str]) -> str:
    """Sentence fragment for Owner's cellar character (top terms from Varietal + Appellation)."""
    t = terms[:5]
    if not t:
        return ""
    if len(t) == 1:
        return f"skews heavily toward {_display_term(t[0])}."
    if len(t) == 2:
        return f"skews heavily toward {_display_term(t[0])} and {_display_term(t[1])}."
    if len(t) == 3:
        return (
            f"skews heavily toward {_display_term(t[0])}, {_display_term(t[1])}, "
            f"and {_display_term(t[2])}."
        )
    if len(t) == 4:
        return (
            f"skews heavily toward {_display_term(t[0])} and {_display_term(t[1])}, "
            f"with strong {_display_term(t[2])} and {_display_term(t[3])} representation."
        )
    return (
        f"skews heavily toward {_display_term(t[0])} and {_display_term(t[1])}, "
        f"with strong {_display_term(t[2])}, {_display_term(t[3])}, and {_display_term(t[4])} representation."
    )
