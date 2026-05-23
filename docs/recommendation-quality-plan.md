# Recommendation Quality Plan

Status: items 1–3, 5–7 shipped; item 4 deferred
Owner: bradleybosher
Last updated: 2026-05-23

This plan addresses concrete weaknesses observed when analysing the default profile's recommendation pipeline (102 tasting notes; synthesized palate emphasising high-acidity, low-oak, value-driven, low-intervention wines). Each section names the gap, the proposed change, the file(s) involved, and a rough effort estimate.

The fixes are ordered by ROI — the retrieval rebuild is the highest-leverage single change because it currently strips most of the personalisation before Claude ever sees the candidate list.

---

## 1. Retrieval pre-filter — synonym/grape/producer expansion ✅ SHIPPED

**Gap.** [backend/retrieval.py](backend/retrieval.py) scores wine-list lines by literal substring match against `preferred_grapes`, `preferred_regions`, `preferred_styles`, and `avoided_styles`. For this profile:
- `avoided_styles` are full sentences ("heavily oaked fruit-forward Chardonnay without balancing acidity"); the `-2.0` penalty almost never fires against a typical one-line wine entry.
- Positive terms like `"coastal region"` or `"white blend"` will miss `"Mullineux Old Vines White, Swartland"`.
- `top_producers` is empty even though "The Wine Society", "Domaine Coillot", "Alheit" and similar grower/own-label names recur heavily in the notes.
- No synonym expansion: `Burgundy` does not imply `Marsannay / Côte de Nuits / Côte de Beaune`; `Chablis ≠ Chardonnay`; `Pinot Noir ≠ Spätburgunder`.

**Change.**
1. Introduce `backend/synonyms.py` mapping canonical grape/region tokens to expansion lists (start small: Burgundy/Champagne/Loire/Rhône appellations, the user's actual repeat regions).
2. Distil `avoided_styles` into single-token markers (`oaky`, `jammy`, `high-alcohol`, `flabby`, `sweet-sparkling`) and store both the sentence and the tokens on `_synthesized`.
3. Compute `top_producers` from the notes during synthesis — repeat-purchase signal is the strongest positive we have.
4. Score-weight: producer hit `+2.0`, region/appellation hit `+1.5`, grape hit `+1.0`, avoided token `-2.0`, ambiguous `+0.25` (so all-zero lines don't fall to the bottom purely on length).

**Files.** `backend/retrieval.py`, new `backend/synonyms.py`, `backend/profile.py` (synthesis output schema), `backend/models.py` (extend `TasteProfile`), `docs/llm/modules/retrieval.md`.

**Effort.** Medium (1–2 days). No new LLM calls.

---

## 2. Statistical palate features — extract what one-shot synthesis misses ✅ SHIPPED

**Gap.** `synthesize_palate_from_notes` is a single Claude call. With 102 rows of structured data there are signals it routinely flattens:
- **QPR sensitivity.** Notes repeatedly read "great value", "above what you can pay for comparable burgundy", "for the price fantastic" — yet `budget` is barely surfaced and the retrieval budget penalty is only `-0.5`.
- **Low-intervention bias.** Pét Nat, Brut Nature, Brut Zéro, Jura, grower-Champagne all recur — never captured as a marker.
- **Aging preference.** "needed more time in bottle", "would like to try with some age" — recurring, absent.
- **Dislike-by-varietal/region correlation.** Notes containing "too oaky / unbalanced / too alcoholic" are tied to specific varietals/regions that should be down-weighted.
- **Confidence floor.** `inference_confidence: "medium"` with 102 notes is needlessly humble — should scale with `note_count`.

**Change.**
1. New `backend/palate_stats.py` (pure-Python, no LLM) that runs *before* the Claude synthesis call and produces:
   - `producer_frequency`, `region_frequency`, `varietal_frequency` with quality-weighting (positive vs negative note sentiment from a small keyword lexicon).
   - `price_distribution` (median, p25, p75) per colour/category.
   - `style_signals` — boolean markers derived from note keywords: `natural_wine_affinity`, `oxidative_affinity`, `aging_preference`.
2. Pass that struct into the synthesis prompt as evidence so the LLM is constrained to ground its narrative in counts, not vibes.
3. Persist both the stats and the persona on `_synthesized`. Stats feed retrieval (item 1) and reasoning (item 5).
4. Make `inference_confidence` a function of `note_count` (≥ 50 notes ⇒ at least `high`).

**Files.** new `backend/palate_stats.py`, `backend/profile.py`, `backend/models.py`, `docs/llm/modules/profile.md`, `docs/llm/modules/palate_stats.md`.

**Effort.** Medium-high (2–3 days).

---

## 3. Separate cellar (intent) from consumed (habit) ✅ SHIPPED

**Gap.** Synthesis runs over the consumed notes only. The cellar inventory represents what the user actively bought — an intent signal — which can diverge meaningfully from drinking habits and is currently invisible.

**Change.** In `palate_stats.py`, compute parallel distributions over `inventory.json`. Expose a small `aspirational_skew` block on `_synthesized` highlighting categories over-represented in the cellar vs. consumed (e.g. "buys Burgundy at 2× the rate they currently drink it"). Pipe a one-line summary into the system prompt so Claude can favour aspirational categories when a list offers something rare.

**Files.** `backend/palate_stats.py`, `backend/prompt.py`.

**Effort.** Small (half day on top of item 2).

---

## 4. Feedback loop — flight history into next synthesis ⏸ DEFERRED

**Gap.** Flights are saved but `insights.compute_drift_suggestions()` only surfaces *gap* directions (varietals Claude recommends that the profile doesn't list). There is no *rejection* direction — if Claude keeps recommending Bordeaux blends and the user keeps marking them down, nothing catches it. Synthesis also never re-runs after the initial upload.

**Change.**
1. Extend the `flights` table with optional `user_rating` (1–5) and `user_note` text fields; wire a minimal post-recommendation rating UI.
2. Add `insights.compute_rejection_signals()` — for each recommended varietal/region/producer, compare avg user rating to baseline; surface persistent under-performers.
3. Re-run `synthesize_palate_from_notes` automatically when `note_count` has grown by ≥ 20 since the last synthesis (record `synthesized_at` and `synthesized_note_count` on `_synthesized`).

**Files.** `backend/cache.py` (schema), `backend/insights.py`, `backend/profile.py`, `backend/routes/history.py`, `backend/routes/insights.py`, frontend rating component, `docs/llm/modules/insights.md`.

**Effort.** Medium (2–3 days, mostly UI + migration).

---

## 5. Reasoning grounded in actual tasting notes ✅ SHIPPED

**Gap.** The `"Like your [Producer + Wine], but…"` opener is good, but `reasoning` is freeform and the model can drift toward plausible-sounding but unverifiable claims. The user's own `ConsumptionNote` strings are the highest-signal evidence available and are never quoted.

**Change.**
1. Add an `evidence_quotes: list[str]` field to the recommendation tool schema in [backend/recommender.py](backend/recommender.py): 1–2 short quotes from the user's history that justify the pick (e.g. `"From your Crémant du Jura note: 'nutty oxidative notes yet not too round'"`).
2. Pass a curated subset of high-signal notes (top-rated and bottom-rated, deduplicated by varietal/region) into the system prompt as a `**TASTING NOTE LIBRARY**` block so the model has source material to quote.
3. Validate post-hoc that each quote substring appears in `profile_data.json["consumed"][*]["ConsumptionNote"]`; drop quotes that don't match exactly to prevent fabrication.

**Files.** `backend/recommender.py`, `backend/prompt.py`, `backend/models.py`, `backend/profile.py` (note-curation helper), `docs/llm/modules/recommender.md`.

**Effort.** Medium (1–2 days).

---

## 6. Ground bars/wheel/abv against a reference table ✅ SHIPPED

**Gap.** Per-wine `bars`, `wheel`, `abv` are LLM-asserted. The promise of "match the wine's acidity against your acidity 5/5 marker" is undermined when both sides are model-generated and uncalibrated.

**Change.** Add `backend/data/wine_reference.json` — a small seed table of canonical bars per appellation/grape pair (Chablis, Barolo, Marsannay, Bandol Rosé, etc.; ~80 entries to start). After validation in `_attempt_recommendation`, blend Claude's bars 50/50 with the reference when an appellation/grape match exists; otherwise keep Claude's. Log when blending happens for later audit.

**Files.** new `backend/data/wine_reference.json`, `backend/recommender.py`, `docs/llm/modules/recommender.md`.

**Effort.** Small-medium (1 day to seed table, half day for blending).

---

## 7. Diversity slot — force one "stretch" pick ✅ SHIPPED

**Gap.** Three picks all anchored to the persona produce three near-identical Marsannays. For an exploratory user (the notes repeatedly say "keen to try more X", "want to try more rounded champagne") this is the wrong default.

**Change.** When `bottle_count >= 3`, instruct the prompt that the final slot is a *stretch* pick: adjacent to but outside the safe persona zone, with reasoning that explicitly names the dimension being stretched ("higher tannin than you usually go for, but the freshness keeps it in your lane"). Surface this on the frontend with a `stretch: true` flag on `WineRecommendation`.

**Files.** `backend/prompt.py`, `backend/models.py`, `backend/recommender.py`, frontend recommendation card.

**Effort.** Small (half day backend, small frontend).

---

## Sequencing

1. Items **1 + 2** ship together — retrieval expansion depends on the statistical features being available on `_synthesized`. Biggest single quality jump.
2. Item **5** next — visible win, low risk, leverages data already on disk.
3. Items **3 + 6 + 7** — incremental polish, any order.
4. Item **4** last — needs UI work and schema migration; deferred until the recommendation half is solid enough that ratings are meaningful signal.

## Out of scope (for now)

- Embedding-based retrieval reranker (only worth doing once item 1's lexical scoring is exhausted).
- External critic API integration for wine bars (item 6 is the lighter alternative).
- Restaurant-context-aware strategy switching (high-end vs bistro list) — interesting but no clear evaluation signal yet.
