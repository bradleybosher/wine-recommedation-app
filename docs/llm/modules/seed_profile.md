# backend/seed_profile.py

Seed-bottle onboarding: an alternative to the CellarTracker TSV pathway.
A user names 3–7 wines they have loved (and optionally 1–3 they disliked) and
Claude infers an aggregate taste profile shaped identically to the output of
`profile.build_taste_profile()` so the downstream recommender consumes it
unchanged.

## Purpose

Eliminate the cold-start cost for users without a CellarTracker account while
preserving the revealed-preference principle that differentiates this app from
a generic LLM wine chat. Quiz-style preferences are explicitly rejected: they
capture stated preference, not revealed preference, and degrade the
"Why This Fits You" panel into tautologies.

## Public functions

- `infer_profile_from_seeds(req: SeedProfileRequest, anthropic_api_key: str, anthropic_model: str) -> dict`
  Single Anthropic tool-use call (tool `infer_seed_profile`). Returns a dict
  matching `build_taste_profile()` output plus `style_summary`,
  `taste_markers` (acidity/tannin/body/oak, 1–5), `inference_confidence`,
  `profile_source="seed_bottles"`, and `seed_bottle_count`.

- `persist_seed_profile(inferred: dict) -> None`
  Overwrite `profile_data.json` with `{"_inferred": inferred}`. Wipes any
  legacy CellarTracker keys (`list`/`notes`/`consumed`/`purchases`) so the
  seed-bottle pathway never silently mixes sources.

- `load_inferred_profile() -> dict | None`
  Helper to read back the persisted inferred profile.

## Pipeline integration

- `profile.build_taste_profile()` short-circuits to the `_inferred` dict when
  present — no synthetic CT-shaped rows needed.
- `profile.build_taste_profile_pydantic()` propagates `profile_source` and
  (when seed-derived) `inference_confidence` into the `TasteProfile`.
- `profile.build_enriched_profile_text()` skips the redundant Anthropic
  enrichment call when the profile is already inferred (it carries its own
  `style_summary`).
- `prompt.build_system_prompt(..., profile_source=...)` prepends a one-line
  caveat ("inferred from a small set of seed bottles; treat as directional")
  when the source is `"seed_bottles"`.
- `scorer.score_recommendation(..., cap_confidence=True)` downgrades per-wine
  "high" → "medium" so the scoring composite cannot exceed the profile's own
  certainty.

## Invariants

- `loved` length validated at 3..7 by `SeedProfileRequest`.
- `disliked` length validated at 0..3.
- `_inferred` is the single source of truth for seed-derived profiles; the
  legacy CT keys are absent in this pathway.
