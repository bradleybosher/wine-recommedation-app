# Plan — Implement the "Vinothèque" Editorial Redesign

## Context

The current Wine Recommender frontend is a generic glassmorphism SPA: dark purple gradient blobs, white-on-glass cards, sans-serif type. The design handoff in `Wine Recommender/design_handoff_wine_recommender/` ("Vinothèque" — Direction A) replaces this with an old-world editorial direction — cream paper, all-serif typography (Cormorant Garamond + EB Garamond), oxblood ink, and a wine-specific signal system (flavor wheel, structure bars, region map, drinking-window timeline, per-wine colour tinting). The redesign covers four screens — Preferences → Flight → Detail → Compare — built on a shared atoms library.

This is a high-fidelity redesign: colours, type sizes, spacing, and proportions in the handoff are the source of truth. The current backend `WineRecommendation` model lacks most of the fields the design needs (coords, bars, wheel, nose, palate, fits, pairs, critic score, drink window, color palette, appellation, ABV), so the backend recommender must be extended in parallel. The existing onboarding (CellarTracker / seed bottles) is retained but re-skinned. The product gains a **dual mode** on the Preferences screen: recommend from the user's own cellar, or from an uploaded restaurant wine list.

User-confirmed decisions:
- **Wine data:** extend backend recommender to return the full structured record.
- **Scope:** full replacement of the glass design system; re-skin onboarding too.
- **Routing:** introduce `react-router-dom`.
- **Delivery:** stage incrementally — land each phase reviewable.
- **Product:** dual mode (cellar source OR wine list upload) on Preferences.

## Phased Delivery

Each phase produces a reviewable, mergeable change. Phases 1–2 do not break existing functionality; Phase 3 swaps the active route; Phase 4 finishes the migration; Phase 5 extends the backend.

---

### Phase 1 — Design tokens, fonts, and core atoms ✓ COMPLETE

**Goal:** Stand up the new design system in isolation. Nothing user-facing changes yet — the new tokens live alongside the old ones, and the atoms are reachable only via a temporary `/design-preview` route for visual QA.

**Files to add:**
- `frontend/src/design/tokens.ts` — exported constants for `PAPER`, `PAPER_DEEP`, `INK`, `INK_SOFT`, `RULE`, `OXBLOOD`, and the three per-wine palettes (Brunello / Barolo / Chablis). Source of truth values are the hex codes listed in `README.md` lines 56–75.
- `frontend/src/index.css` — extend `@theme` with the new tokens (`--color-paper`, `--color-ink`, `--color-oxblood`, etc.) and add `@font-face` / Google Fonts import for Cormorant Garamond + EB Garamond (weights per `README.md` lines 84–87).
- `frontend/src/design/atoms/` — one file per atom, mirroring `Wine Recommender/design_handoff_wine_recommender/design_files/atoms.jsx`:
  - `Masthead.tsx`
  - `FlavorWheel.tsx`
  - `StructureBars.tsx`
  - `RegionMap.tsx` (port `COUNTRY_BOX` and SVG paths verbatim; add countries beyond Italy/France only as needed)
  - `GlassPour.tsx`
  - `Bottle.tsx` (Bordeaux + Burgundy shapes)
  - `Fleuron.tsx`
  - `RuleDouble.tsx`
  - `DrinkingWindow.tsx`
- `frontend/src/design/PaperFrame.tsx` — page-frame wrapper (cream background, paper-texture radial-gradient noise, 1px inset border, inset shadow) per `README.md` lines 125–131.
- `frontend/src/design/Field.tsx` — the reusable form field used on Preferences (label + value with bottom rule, `inkAccent` variant) per `README.md` lines 154–158.
- `frontend/src/pages/DesignPreview.tsx` — temporary route rendering every atom against sample data from `wine-data.js`. Removed in Phase 4.

**Files to modify:**
- `frontend/package.json` — add `react-router-dom`. No charting library — keep hand-rolled SVG to preserve the editorial restraint (the handoff suggests Recharts, but the atom implementations in `atoms.jsx` are already SVG-native and pixel-tuned; lifting them is faster and fidelity is higher).
- `frontend/src/main.tsx` — wrap `<App />` in `<BrowserRouter>`. Add a stub `/design-preview` route alongside `/*` rendering existing `App`.

**Out of scope this phase:** No existing screen changes. CLAUDE.md not edited yet (Phase 4).

**Verification:**
- `npm run dev` → navigate to `/design-preview`, eyeball every atom against the prototype at `Wine Recommender/design_handoff_wine_recommender/design_files/index.html` (open in browser).
- Run `npm run typecheck` and `npm run lint`.

---

### Phase 2 — Preferences screen (intake) ✓ COMPLETE

**Goal:** Build Screen 01 — the new intake form, dual mode (cellar | wine list).

**Files to add:**
- `frontend/src/pages/Preferences.tsx` — implements layout from `README.md` lines 138–174 (`VinPreferences` in `vinotheque.jsx`). Uses `PaperFrame`, `Masthead`, `Fleuron`, `Field`. Two-column 1fr 1.4fr grid; absolute footer band with the 4-column "what's in this issue" folio.

**Form fields** (state held locally; on submit, POST to backend and navigate to `/flight`):
- Source mode toggle (new — not in design): pill toggle "From my cellar" / "From a wine list". When wine list is selected, render a `FileUploader` styled to match the editorial look (cream paper drop zone with hairline border, italic eyebrow). The toggle sits above the existing fields with the same `Field` label treatment.
- Occasion, Menu, Cellar leanings (rendered OXBLOOD italic), Temperament, Ceiling, Bottles — all as `Field` instances per `README.md` line 163–169.
- Submit button: Cormorant 14px, letter-spacing 3, uppercase, `padding: 10px 22px`, bg `INK`, fg `PAPER`. Label: "Compose the flight →".

**Routing:**
- Add `/preferences` route in `main.tsx` (or a new `routes.tsx`).
- After Phase 1's onboarding completion check in `App.tsx`, redirect populated users to `/preferences` instead of the current `RecommendationScreen`. Old screen remains reachable at `/legacy` during transition.

**Backend wiring (minimal — full extension in Phase 5):**
- Send existing `recommend` body shape for now; map Preferences form fields into `meal` (concatenated occasion+menu) and `style_terms` (cellar leanings + temperament). Wine list mode still posts the uploaded file. This keeps the screen functional before the backend is extended.

**Files to modify:**
- `frontend/src/App.tsx` — replace the inline state machine return with route-driven rendering. Onboarding stays at `/onboarding`; `/preferences` is the post-onboarding landing.

**Verification:**
- Dev server, complete onboarding (or arrive with inventory), land on `/preferences`. Fill the form, click submit. Confirm navigation to `/flight` (stubbed empty page acceptable until Phase 3).
- Compare side-by-side with the prototype's Preferences artboard.

---

### Phase 3 — Flight screen (recommendations) + Detail screen ✓ COMPLETE

**Goal:** Replace the current `RecommendationResults` with the Flight screen (Screen 02), and add Detail (Screen 03). Detail is reached from a Flight list entry.

**Files to add:**
- `frontend/src/pages/Flight.tsx` — implements `README.md` lines 177–221 (`VinList`). Uses the **Direction B terroir cartouche** (column 1) per the explicit cross-pollination in lines 46–48; reference `vinotheque.jsx` for column 2/3 and `almanac.jsx` (Direction B) only for the cartouche shape.
- `frontend/src/components/Flight/ListEntry.tsx` — the 3-column row (terroir cartouche · editorial body · score/structure/price). Per-wine palette drives accent, bottle, glass, chart fills.
- `frontend/src/pages/Detail.tsx` — implements `README.md` lines 224–262 (`VinDetail`). Three bands: Hero (Bottle + GlassPour + drop-cap body), Triptych (FlavorWheel · StructureBars · RegionMap inside three `Panel` cells), absolute footer (Pairing · DrinkingWindow · Editor's score).
- `frontend/src/components/Detail/Panel.tsx` — reusable triptych cell.
- `frontend/src/state/recommendationStore.tsx` — a tiny React Context holding the current recommendation response so Flight → Detail navigation doesn't re-fetch. Hydrated by the Preferences submit handler. Keep it minimal — no Zustand/Redux.

**Routing:**
- `/flight` — Flight screen.
- `/detail/:wineId` — Detail screen; looks up the wine by id from context, 404s gracefully if direct-loaded without context (acceptable for v1).

**Per-wine palette derivation:**
- Until Phase 5 lands the backend palette, derive it client-side in `frontend/src/design/wineColor.ts`: a small map keyed by varietal/region (Nebbiolo→Barolo palette, Sangiovese→Brunello palette, Chardonnay→Chablis palette, with sensible fallbacks). This is the only piece the user said is OK to derive client-side; it gets superseded by backend-provided `color` in Phase 5.

**Out of scope:** Compare screen lands in Phase 4.

**Verification:**
- Submit Preferences in test mode (`TEST_MODE=true`, fixture=`happy`) → confirm Flight renders 3 entries with proper per-wine accents. Click each → Detail loads with all wine signals.
- Visually QA against prototype Flight + Detail artboards.

---

### Phase 4 — Compare screen + onboarding re-skin + retire glassmorphism ✓ COMPLETE

**Goal:** Finish the new flow with Compare (Screen 04), re-skin the onboarding screens in the editorial style, then delete the old design system and update `CLAUDE.md`.

**Files to add:**
- `frontend/src/pages/Compare.tsx` — implements `README.md` lines 265–287 (`VinCompare`). 2-column grid with vertical hairline rule; verdict band (INK background, PAPER text) absolute at bottom.

**Routing:**
- `/compare?a=<id>&b=<id>` — pre-selects from query params. "Side by side ⇆" button on Flight links here with the top two wine ids.

**Onboarding re-skin:**
- Modify in place (preserve flow logic, replace presentation):
  - `frontend/src/components/UploadFlow.tsx` — wrap in `PaperFrame` + `Masthead`. Choice cards become editorial `Field`-style entries with hairline rules; "Choose your path" eyebrow.
  - `frontend/src/components/UploadCellarInventoryScreen.tsx`, `UploadTastingHistoryScreen.tsx`, `SeedBottlesScreen.tsx` — re-skin to paper/serif. Drop zones become hairline-bordered cream rectangles with italic eyebrow labels.
  - `frontend/src/components/RecommendationScreen.tsx`, `RecommendationResults.tsx` — DELETE (functionality moved to Preferences + Flight). `MealDescriptionInput.tsx` — DELETE.
  - `frontend/src/components/ProfileTab.tsx`, `ProfileSummaryView.tsx` — re-skin to editorial. Profile becomes a "Cellar Almanac" page at `/profile`.
  - `frontend/src/components/FileUploader.tsx` — keep, restyle for paper aesthetic.

**Retire glass system:**
- DELETE `frontend/src/components/ui/GlassCard.tsx`, `VibrantBackground.tsx`.
- DELETE `--color-glass-*` tokens and `blob-drift` keyframes from `index.css`. Keep wine palette tokens (`--color-wine-*`) — they're still referenced semantically in the new palettes.
- DELETE the temporary `/design-preview` route + page from Phase 1.

**CLAUDE.md updates:**
- Replace the "Frontend & Styling" section (rules 5) with new rules: `PaperFrame` not `VibrantBackground`; serif typography (Cormorant/EB Garamond); no glassmorphism; ink-on-paper text colors; hairline rules; no rounded corners; no drop shadows beyond inset paper.
- Update "Tech Stack" line: add `react-router-dom`; replace "glassmorphism design system" with "old-world editorial design system (Vinothèque)".
- Update Modules line if frontend module list changes meaningfully.

**Docs updates** (per the auto-memory `feedback_docs.md` and CLAUDE.md Documentation Update Protocol):
- `docs/llm/modules/` — update any module docs whose corresponding files changed.
- `docs/llm/interfaces.md` — refresh public signatures.
- `README.md` — update user-facing description (dual mode, four-screen flow).

**Verification:**
- Full happy-path walkthrough: clean state → onboarding (both paths) → Preferences (both modes) → Flight → Detail → Compare. All screens render in the editorial style; no glass artefacts remain.
- `git grep -E "(GlassCard|VibrantBackground|backdrop-blur|glass-surface)"` returns nothing.
- `npm run typecheck && npm run lint && npm run test`.

---

### Phase 5 — Backend recommender extension

**Goal:** Replace client-derived/mocked wine fields with real backend data. This phase can land in parallel with Phase 3 if desired, but is listed last because Phases 1–4 deliver visible UX value with placeholder data.

**Files to modify:**
- `backend/models.py` — extend `WineRecommendation` (and add nested models) with: `appellation: str | None`, `country: str | None`, `coords: Coords` (lat/lon), `grape: str | None`, `abv: float | None`, `drink: DrinkWindow` (from/peak/until), `color: WineColor` (glass/tint/ink/accent), `bars: StructureBars` (tannin/acidity/body/sweetness/oak 0–10), `wheel: dict[str, int]` (~8 aroma spokes 0–10), `nose: str`, `palate: str`, `fits: list[str]` (already exists as `fitMarkers` — rename/extend), `pairs: list[str]`, `critic: Critic` (score/source). Maintain `ConfigDict(alias_generator=to_camel, populate_by_name=True)` per CLAUDE.md rule 4.
- `backend/prompt.py` — update the recommender system prompt to request this fuller structured payload. Add few-shot examples grounded in real wines so Claude grounds bars/wheel/pairs realistically.
- `backend/recommender.py` — adapt parsing/validation to the new schema.
- `backend/test_fixtures.py` — extend canned fixtures (`happy`, `sparse`, etc.) to include the new fields so frontend Phase 1–4 work continues to function in TEST_MODE.
- `backend/routes/recommend.py` — accept the new Preferences form (occasion, menu, cellar leanings, temperament, ceiling, count, source mode) instead of (or in addition to) the current `meal` + `style_terms`. Keep a compat path for the legacy shape until frontend cutover is verified.

**Frontend follow-up:**
- After regenerating types: STOP and ask the user to run `sync_types.bat` per CLAUDE.md rule 2 (Sync Protocol). Do not edit `frontend/src/client/` by hand.
- Once types regenerate, replace client-derived palette/coords lookups in `frontend/src/design/wineColor.ts` with reads from the backend payload. Remove the stub map; keep a tiny fallback only for missing data.

**Docs:**
- `docs/llm/modules/models.md`, `recommender.md`, `prompt.md`, `test_fixtures.md`, `routes/recommend.md` — update for new fields/shape.
- `docs/llm/interfaces.md` — refresh.
- `CLAUDE.md` — update Data Flow section to reflect the richer payload.

**Verification:**
- `TEST_MODE=true` → submit Preferences → confirm fixture data populates every visual signal end-to-end (wheel spokes, bars, drinking window, pairings).
- `TEST_MODE=false` with real Anthropic key → submit a real preferences set → confirm Claude returns a schema-valid payload with non-degenerate bars/wheel/coords.
- Backend tests: `.\backend\.venv\Scripts\python.exe -m pytest backend/`.

---

## Critical Files Referenced

### From the design handoff (read-only references)
- `Wine Recommender/design_handoff_wine_recommender/README.md` — token + spec source of truth
- `Wine Recommender/design_handoff_wine_recommender/design_files/vinotheque.jsx` — Direction A screens
- `Wine Recommender/design_handoff_wine_recommender/design_files/almanac.jsx` — terroir cartouche only
- `Wine Recommender/design_handoff_wine_recommender/design_files/atoms.jsx` — atom implementations to port
- `Wine Recommender/design_handoff_wine_recommender/design_files/wine-data.js` — sample data shape

### To modify
- Frontend entry: `frontend/src/App.tsx`, `frontend/src/main.tsx`, `frontend/src/index.css`, `frontend/package.json`
- Frontend components (re-skin or delete): `frontend/src/components/UploadFlow.tsx`, `UploadCellarInventoryScreen.tsx`, `UploadTastingHistoryScreen.tsx`, `SeedBottlesScreen.tsx`, `RecommendationScreen.tsx` (DELETE), `RecommendationResults.tsx` (DELETE), `MealDescriptionInput.tsx` (DELETE), `FileUploader.tsx`, `ProfileTab.tsx`, `ProfileSummaryView.tsx`, `ui/GlassCard.tsx` (DELETE), `ui/VibrantBackground.tsx` (DELETE)
- Backend: `backend/models.py`, `backend/prompt.py`, `backend/recommender.py`, `backend/test_fixtures.py`, `backend/routes/recommend.py`
- Docs: `CLAUDE.md`, `README.md`, `docs/llm/modules/*.md`, `docs/llm/interfaces.md`

### To add
- `frontend/src/design/{tokens.ts, PaperFrame.tsx, Field.tsx, wineColor.ts}`
- `frontend/src/design/atoms/{Masthead,FlavorWheel,StructureBars,RegionMap,GlassPour,Bottle,Fleuron,RuleDouble,DrinkingWindow}.tsx`
- `frontend/src/pages/{Preferences,Flight,Detail,Compare,DesignPreview}.tsx` (DesignPreview removed in Phase 4)
- `frontend/src/components/{Flight/ListEntry,Detail/Panel}.tsx`
- `frontend/src/state/recommendationStore.tsx`

## Reused Existing Functionality

- **SDK calls** — all backend interaction stays in `frontend/src/client/sdk.gen.ts` per CLAUDE.md rule 2. No manual `fetch`.
- **Inventory bootstrap** — `getInventoryInventoryGet()` flow in `App.tsx` is preserved; only the screens it routes to change.
- **Onboarding logic** — `UploadFlow`'s state machine (`choose | cellartracker | seed | complete`) is preserved; only presentation is replaced.
- **Test fixtures** — `backend/test_fixtures.py` continues to short-circuit `/recommend` in TEST_MODE; extended (not replaced) in Phase 5.
- **Pydantic camelCase aliasing** — `ConfigDict(alias_generator=to_camel, populate_by_name=True)` pattern preserved on all new models (CLAUDE.md rule 4).

## End-to-End Verification (final)

1. Reset to clean state: delete `backend/inventory.json` and `backend/profile_data.json`.
2. Start backend: `.\backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload`.
3. Start frontend: `cd frontend; npm run dev`.
4. Visit app → land on onboarding (editorial style). Run both paths (CellarTracker upload + seed bottles) in two sessions.
5. After onboarding → land on `/preferences`. Verify Masthead, fleuron, all six fields, footer folio band, submit button.
6. Toggle source mode → wine list upload appears; upload a sample PDF.
7. Toggle back to cellar mode → submit. Land on `/flight`. Verify three entries with correct per-wine palette tinting and terroir cartouche.
8. Click each Flight entry → `/detail/:id`. Verify all wine signals render (FlavorWheel, StructureBars, RegionMap, DrinkingWindow, GlassPour, Bottle, drop cap, double rules).
9. Back to Flight → click "Side by side ⇆" → `/compare?a=&b=`. Verify two panes, vertical hairline, verdict band.
10. Backend tests: `.\backend\.venv\Scripts\python.exe -m pytest backend/`.
11. Frontend checks: `npm run typecheck && npm run lint && npm run build`.
12. Pixel-compare each screen against the prototype HTML in `Wine Recommender/design_handoff_wine_recommender/design_files/index.html`.
