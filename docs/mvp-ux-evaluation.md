# MVP UX Evaluation & Differentiation Plan

## Current UX Snapshot (What works / where friction is)

### What is already strong
- **Clear onboarding intent**: users are pushed through cellar upload → optional tasting history → recommendation flow, which is coherent for first-time setup.
- **Attractive visual design**: the wine-themed color system and glass-card motif feel premium and emotionally aligned with wine discovery.
- **Structured output**: top recommendations include confidence, pricing, and reasoning, which is better than raw LLM chat output.

### Highest-friction gaps
- **No “decision confidence” context for each recommendation**: users get confidence labels, but not *why confidence is high/low* based on parse quality, profile depth, or meal clarity.
- **Minimal interaction loop after first result**: there is no quick way to iterate (“more adventurous”, “lower budget”, “white only”) without re-uploading and retyping.
- **Profile value is hidden at decision time**: profile exists in a separate tab, but users can’t easily see *which profile traits drove each recommendation* while choosing a bottle.
- **No practical “restaurant action mode”**: copy button exists, but there is no concise “what to ask the sommelier” snippet, which is the key real-world handoff.

---

## 5 Most Impactful MVP Changes (Fit existing architecture)

## 1) Add a **Why This Fits You** micro-panel per recommendation

**User value**
- Differentiates from generic LLM output by grounding each pick in user-specific taste signals.
- Increases trust and reduces "black-box" feel.

**MVP implementation**
- Extend each recommendation card with 2–3 short bullet tags sourced from existing data:
  - “Matches your high-acidity preference”
  - “Aligned with your top region: Northern Rhône”
  - “Avoids oaky profile you often down-rate”
- Data can be generated in backend prompt output as an additional optional field (e.g. `fit_markers: string[]`) with fallback inference from `reasoning` if missing.

**Why this fits current architecture**
- You already return structured recommendation objects and a profile summary; this is a schema extension, not a new system.

---

## 2) Add **One-click re-rank chips** after results (no re-upload)

**User value**
- Creates an iterative decision loop that feels productized vs. a one-shot LLM query.
- Mimics how wine choices evolve in real time.

**MVP implementation**
- Add quick chips above results:
  - “Under $80”
  - “More adventurous”
  - “Food match first”
  - “Safer crowd-pleaser”
- Clicking a chip re-submits with appended `style_terms` and/or a small “selection mode” flag.
- Reuse existing `recommend` endpoint contract by augmenting request body with optional strategy hints.

**Why this fits current architecture**
- Existing API already accepts style overrides and handles repeated calls; no new persistence layer required.

---

## 3) Add a **Sommelier Ask** action per recommended wine

**User value**
- Bridges digital recommendation to in-restaurant execution, where apps often fail.
- Gives immediately usable language users can speak verbatim.

**MVP implementation**
- Replace/augment "Copy to clipboard" with:
  - “Copy Sommelier Ask” text block, e.g. "I usually like high-acid, savory reds with moderate tannin — is this producer’s style in that direction?"
- Build snippet from existing recommendation + profile summary fields client-side.

**Why this fits current architecture**
- Pure frontend composition from existing response fields; optional backend enhancement later.

---

## 4) Add **Input quality feedback before submit**

**User value**
- Reduces bad outputs by nudging better meal and list inputs.
- Makes app feel more intelligent than generic upload+prompt flow.

**MVP implementation**
- Add lightweight pre-submit checks in UI:
  - Meal text too short (“add sauce/cooking style for better pairing”)
  - File appears image-based (“consider clearer photo / crop glare”)
- Add compact quality meter: `Meal Detail: Low/Medium/High`.

**Why this fits current architecture**
- Frontend-only heuristics first; optional backend parse metrics can be surfaced later via existing response wrapper.

---

## 5) Add a **Contrast View** for top 2 picks

**User value**
- Helps users decide between finalists quickly (“A is brighter/mineral, B is richer/spiced”).
- This is a strong differentiator from standard LLM lists.

**MVP implementation**
- Add “Compare Top 2” toggle rendering a small side-by-side matrix:
  - Style profile
  - Risk level/confidence
  - Best meal scenario
  - Price positioning
- Populate from current recommendation fields + short generated contrast sentence.

**Why this fits current architecture**
- Pure presentation layer with optional single extra field (`contrast_note`) from backend.

---

## Suggested Build Order (fastest learning per effort)

1. **Why This Fits You panel** (high trust impact, low-medium effort)
2. **One-click re-rank chips** (high engagement impact, low effort)
3. **Sommelier Ask action** (high real-world utility, low effort)
4. **Input quality feedback** (quality uplift, low effort)
5. **Contrast View** (decision UX differentiation, medium effort)

---

## What this does better than “just ask an LLM”

These changes move the product from a single prompt wrapper to a **decision workflow**:
- grounded personalization signals,
- iterative control loops,
- real-world execution support,
- and explicit tradeoff comparisons.

That is exactly where product UX can beat a standalone chat query in an MVP stage.
