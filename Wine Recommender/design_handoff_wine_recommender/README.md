# Handoff: Wine Recommender — Old-World Editorial Redesign

## Overview

This is a redesign of an existing wine recommendation web app. The previous UI was generic — dark purple cards with sans-serif text — and gave no sense of the product's subject matter. This handoff replaces it with a custom **old-world editorial direction**: cream paper, all-serif typography, oxblood ink, and a system of wine-specific signals (flavor wheel, structure bars, region map with locator dot, drinking-window timeline, per-wine colour tinting).

The redesign covers the full prototype loop across four screens:

1. **Preferences** — intake form ("What will you open tonight?")
2. **The Flight** — three composed recommendations (replaces the original card list)
3. **Detail** — full review of one bottle
4. **Compare** — two bottles weighed side-by-side

A reusable design system of "wine signals" is shared across all four screens.

---

## About the Design Files

The files in `design_files/` are **design references created in HTML** — React prototypes built with inline JSX and Babel — showing the intended look, structure, and behaviour. They are **not production code**. The task is to recreate these designs in the target codebase's existing environment (React/Next/Vue/etc.) using its established patterns, component library, design tokens, and routing.

If no environment exists yet, pick a modern React stack (Next.js or Vite + React) and use a serif-friendly type loader (Google Fonts is fine for now). Use a real charting library (e.g. Recharts, Visx, D3) for the flavor wheel and structure bars rather than hand-rolled SVG.

The HTML prototype lives in two design directions side-by-side on a design canvas. **Build only Direction A ("Vinothèque")** as documented below, with one cross-pollination from Direction B for the flight screen (called out explicitly).

---

## Fidelity

**High-fidelity.** Colours, typography, spacing, and proportions are deliberate. Recreate pixel-faithfully. Where exact pixel values are listed below, treat them as the source of truth.

The HTML prototype uses inline styles for fidelity. In the target codebase, lift these values into the existing token system / styled-components / Tailwind config rather than inlining.

---

## Direction: "Vinothèque" (Direction A)

The canonical visual direction. A Wine-Spectator-style editorial magazine.

- Cream paper background, oxblood/ink accents, all-serif type.
- Each screen reads as a folio of a printed cellar review.
- Masthead at the top of every page; folio numeral at the bottom.
- Each wine carries its **actual colour** (garnet, brick, straw) into the page accents, bottle, glass pour, and structural-bar fills.

### Cross-pollination from Direction B

On **the flight screen (02)**, the left column of each list entry uses Direction B's **"terroir cartouche"** instead of the big italic numeral + tinted glass that Direction A originally used. The cartouche stacks: small editorial № numeral → hairline rule → region map with locator dot → region name in italic small caps. This was a user-requested swap during design review. The detail and compare screens retain Direction A's treatment unchanged.

---

## Design Tokens

### Colours

```
PAPER          #f3e8d4   — primary background (cream)
PAPER_DEEP     #ecdfc4   — gradient base for hero areas
INK            #1f120a   — primary text & rules (near-black with brown warmth)
INK_SOFT       #3a261b   — secondary text, captions
RULE           rgba(31,18,10,0.5)
OXBLOOD        #5e1418   — global accent (folio numerals, banner overrides)
```

**Per-wine palette** — driving page accents, bottle, glass, and chart fills:

```
Brunello di Montalcino (Sangiovese)
  glass   #7d1f24   tint #f4dcd3   ink #3a0d10   accent #9a2a30

Barolo Cannubi (Nebbiolo)
  glass   #8a2a2e   tint #f3dad4   ink #3d1014   accent #a83339

Chablis Grand Cru "Les Clos" (Chardonnay)
  glass   #d9b743   tint #f5ecc8   ink #5a4612   accent #b89826
```

`glass` = the colour you'd see in a poured glass. `tint` = a pale wash used as gradient end-stop on tinted pages. `accent` = the colour used for active strokes / fills in charts and key numerals on light backgrounds.

### Typography

Load from Google Fonts:

```
Cormorant Garamond — weights 400, 500, 600, 700 + italic 400/500/600
EB Garamond        — weights 400, 500, 600 + italic 400/500
```

Pairing:
- **Display** — `'Cormorant Garamond', serif`
- **Body** — `'EB Garamond', 'Cormorant Garamond', serif`

Type scale used in the design:

| Role | Family | Size | Style | Tracking |
|---|---|---|---|---|
| Masthead "Vinothèque" | Cormorant | 56px (lg) / 36px (sm) | weight 500, line-height 0.95, letter-spacing -1 | — |
| Page H1 (wine name on detail) | Cormorant | 64px | weight 400, line-height 0.92, letter-spacing -1.5 | — |
| Page H1 (compare wine name) | Cormorant | 32px | weight 400, line-height 1.0, letter-spacing -0.5 | — |
| List entry wine name | Cormorant | 28px | weight 500, line-height 1.0, letter-spacing -0.5 | — |
| Preferences question | Cormorant | 44px | weight 400, line-height 0.96, letter-spacing -1 | — |
| Field value | Cormorant | 22px | weight 400 | — |
| Body copy | EB Garamond | 13–14px | regular, line-height 1.5–1.6 | — |
| Italic body | EB Garamond | 13px | italic | — |
| Caption / label | Cormorant | 10–11px | italic, uppercase | 3–6 (letter-spacing in px) |
| Folio numeral | Cormorant | 11px | italic | 2 |
| Drop cap on detail | Cormorant | 56px | weight 500, float left | — |
| Big editor's score (list) | Cormorant | 38px | italic, weight 500 | — |
| Big editor's score (detail) | Cormorant | 56px | weight 500, line-height 0.9 | — |
| Big rank "I/II/III" *(unused in final flight after B-swap)* | Cormorant | 88px | italic, weight 400, letter-spacing -3 | — |

### Spacing

| Token | Value |
|---|---|
| Page padding (vertical) | 20–28px |
| Page padding (horizontal) | 40–44px |
| Section gap | 18–24px |
| Field gap (within forms) | 14–18px |
| Card padding | 22–28px |
| Folio bottom inset | 14px |
| Compare divider gutter | 1px hairline |

### Borders & Rules

- **Hairline rule:** `1px solid INK` at 0.5 opacity → 1px solid `rgba(31,18,10,0.5)`
- **Double rule:** two stacked 1px / 0.5px lines with 2px gap (use `border-top: 1px solid INK; padding-top: 2px;` then a nested `border-top: 0.5px solid INK; margin-top: 2px;`)
- **Dotted bottom rule** (between list entries): `1px dotted INK`
- **Frame border** (paper edge): `1px solid rgba(80,40,10,0.12)` inset
- **Inset paper shadow:** `inset 0 0 80px rgba(80,40,10,0.06)`
- **Paper texture noise:** `radial-gradient(rgba(80,40,10,0.025) 1px, transparent 1px)` at `3px 3px`, `mix-blend-mode: multiply`

No drop shadows beyond the inset paper. No rounded corners anywhere — this is sheet music, not buttons.

---

## Screens

### Screen 01 — Preferences (Intake)

**File reference:** `vinotheque.jsx` → `VinPreferences`

**Purpose.** User describes the evening before the recommender runs. Submission button kicks off the recommendation flow → routes to screen 02.

**Layout.** Single page on a paper frame. Top: masthead. Two-column body (1fr 1.4fr): left holds the editorial prompt and a fleuron ornament; right holds the form fields. A double rule and 4-column "what's in this issue" footer band sits absolute at bottom.

**Components.**

- **Masthead** (re-used component, see Wine Signals → Masthead below).
- **Prompt block** (left column):
  - Eyebrow: italic Cormorant 14px `INK_SOFT` — "The Editor inquires:"
  - Headline: Cormorant 44px — `What will [italic]you[/italic] open tonight?`
  - Sub: italic EB Garamond 13px `INK_SOFT`, line-height 1.55, max-width comfortable for reading
  - Fleuron ornament (see Wine Signals)
- **Field** component (re-used; right column):
  - Label: Cormorant 9px, letter-spacing 3, uppercase, `INK_SOFT @ 0.85`
  - Value: Cormorant 22px (or 18px when `small`), bottom border `1px INK`, padding-bottom 4
  - When `inkAccent` is true, value renders italic in `OXBLOOD`
- **Two half-width fields side by side** for "Ceiling" and "Bottles"
- **Submit button**: Cormorant 14px, letter-spacing 3, uppercase, `padding: 10px 22px`, background `INK`, color `PAPER`, no border. Label: "Compose the flight →"
- **Footer band** (absolute, left/right 44px, bottom 56px):
  - Double rule, then a 4-column grid of folio sections (I/II/III/IV) with Roman numeral in italic Cormorant 18px `OXBLOOD`, title in Cormorant 15px weight 500, sub in italic 11px `INK_SOFT`.

**Field content used in the prototype** (placeholder copy — implementer should hook to real form state):
- Occasion: "Anniversary supper, four guests"
- Menu: "Charred ribeye · porcini · Roquefort"
- Cellar leans toward: "Sangiovese · Nebbiolo · old-world reds" *(rendered in OXBLOOD italic)*
- Temperament: "Adventurous, within reason"
- Ceiling: "$200"
- Bottles: "3 selections"

**Behaviour.**
- Field values are editable inputs in production (the prototype renders them static).
- Submit posts to the recommender backend and routes to `/flight` (Screen 02).

---

### Screen 02 — The Flight (Recommendations)

**File reference:** `vinotheque.jsx` → `VinList`, `ListEntry`

**Purpose.** Show three composed wine recommendations. Replaces the original card-list screen from the existing app.

**Layout.** Paper frame. Top: masthead. Below masthead:
- Sub-header row (`padding: 20px 44px 16px`, flex-between): "The Flight" italic Cormorant 22px on the left; refine pills on the right in Cormorant 11px italic, uppercase, letter-spacing 2, divided by `·`. The active pill ("Under $200") has a 1px `INK` underline.
- Double rule.
- Vertically stacked list of three `ListEntry` rows, separated by `1px dotted INK`.

Absolute footer (left/right 44px, bottom 56px): editorial caption on left ("Composed by the Editor · drawing from 412 bottles on file"), action buttons on the right — `↻ Recompose` (ghost) and `Side by side ⇆` (filled).

**`ListEntry`** is a 3-column grid `108px 1fr 180px` with `gap: 22px`, `align-items: stretch`, `padding-bottom: 16px`, `border-bottom: 1px dotted INK`.

**Column 1 — Terroir cartouche (borrowed from Direction B):**
- Italic Cormorant 24px in wine's `accent` colour: `№ 01`, `№ 02`, `№ 03` (rank zero-padded).
- 28×0.5px ink-tinted hairline rule, 6px vertical margin.
- `RegionMap` atom at size 84 — country silhouette + locator dot at the wine's lat/lon (see Wine Signals).
- Region name in italic Cormorant 10px, uppercase, letter-spacing 2, `INK_SOFT`, `margin-top: -6px` to overlap the map's bottom slightly.

Centred align in the column.

**Column 2 — Editorial body:**
- Eyebrow: italic Cormorant 10px uppercase, letter-spacing 3, in wine's `accent`. Format: `<Region> · <Appellation>` (e.g. "Tuscany · Montalcino · DOCG").
- Wine name: Cormorant 28px weight 500, letter-spacing -0.5, `INK`.
- Producer + vintage: italic EB Garamond 14px `INK_SOFT`. Format: `<Producer> · <Vintage>`.
- Tasting note: EB Garamond 12.5px line-height 1.45, `INK`, max-width 95%. Open with an oversized italic Cormorant 22px quotation mark in wine's `accent`, then the first sentence of the wine's palate description.
- Fit tags row: 3 chips in Cormorant 11px uppercase, letter-spacing 1, `INK_SOFT`, each prefixed with `✦` in wine's `accent`. Gap 14px.

**Column 3 — Score / structure / price:**
- Top group: "THE EDITOR" eyebrow (Cormorant 9px uppercase letter-spacing 3 `INK_SOFT`), then big italic Cormorant 38px score in wine's `accent` with a small `/100` at 14px opacity 0.7, then italic EB Garamond 11px `INK_SOFT` "per Galloni" (critic source).
- Centre: condensed `StructureBars` showing tannin, acidity, body only (see Wine Signals).
- Bottom: right-aligned line — "cellar price" italic Cormorant 11px `INK_SOFT`, then Cormorant 22px weight 500 `INK` price.

All text right-aligned in column 3.

**Wine data used** — see "Sample Wine Data" section at the end.

**Behaviour.**
- Each `ListEntry` is a link to Screen 03 (Detail) for that wine.
- Refine pills update the recommendation query.
- "Side by side ⇆" → Screen 04 (Compare) with the top two wines preselected.
- "↻ Recompose" re-runs the recommender with the same preferences.

---

### Screen 03 — Detail (A Bottle, Examined)

**File reference:** `vinotheque.jsx` → `VinDetail`, `Panel`

**Purpose.** Full editorial review of a single wine. All wine signals on display.

**Layout.** Paper frame with subtle gradient toward the wine's `tint` color in the bottom half. Top: small masthead. Then three vertical bands:

**Band 1 — Hero (`padding: 26px 40px 14px`, grid `1fr 1.6fr` gap 24):**
- Left: centred column. `Bottle` atom (size 68, shape = Burgundy if `region === "Burgundy"` else Bordeaux) at top. Then italic Cormorant 11px caption "in the glass — <#HEX>" letter-spacing 1, then `GlassPour` atom at size 86 with fill 0.5.
- Right: editorial review.
  - Eyebrow: italic Cormorant 11px uppercase letter-spacing 4 in wine's `accent`. Format: `Review № 01 · <Appellation>`.
  - Title: Cormorant 64px weight 400, line-height 0.92, letter-spacing -1.5, `INK`. Wine name.
  - Subtitle: italic Cormorant 22px `INK_SOFT`. `<Producer> · <Vintage>`.
  - Body: two-column EB Garamond 14px line-height 1.55, column-gap 18, column-rule `0.5px solid INK`. Opens with an oversized Cormorant 56px drop cap (weight 500, line-height 0.85, margin-right 6, margin-top 4) in wine's `accent`. Body text = the wine's full palate description.

**Double rule across page.**

**Band 2 — Triptych (`padding: 20px 40px 24px`, grid `1fr 1px 1fr 1px 1fr`):**

Three `Panel` cells separated by 1px `INK @ 0.18` vertical rules. Each `Panel` is centred:
- Caption: italic Cormorant 11px uppercase letter-spacing 3 `INK_SOFT` (`aroma compass`, `structure`, `Tuscany, Italy`)
- Title: Cormorant 22px `INK`, margin-bottom 14 (`In the Nose`, `On the Palate`, `Terroir`)
- Body:
  - **In the Nose** → `FlavorWheel` at size 210 with wine's palette.
  - **On the Palate** → `StructureBars` (full: tannin/acidity/body/sweetness/oak) and beneath it the wine's `nose` string in italic EB Garamond 12px `INK_SOFT` centred.
  - **Terroir** → `RegionMap` at size 150 with appellation label, then grape (e.g. "Sangiovese (Brunello clone)") in Cormorant 11px uppercase letter-spacing 2 `INK_SOFT` centred.

**Band 3 — Absolute footer (left/right 40px, bottom 56px):**
- Double rule.
- 3-column grid `1.4fr 1fr 0.8fr`, gap 24, margin-top 16:
  - **Pairing**: eyebrow + italic EB Garamond 14px `INK` line-height 1.5, pairs joined by ` · `.
  - **Drinking Window**: eyebrow + `DrinkingWindow` atom (see Wine Signals).
  - **The Editor**: eyebrow + Cormorant 56px weight 500 score in wine's `accent`, line-height 0.9, then italic EB Garamond 12px `INK_SOFT` "$185 · 14.5% abv".

**Behaviour.**
- Detail is reached from a list entry click in Screen 02.
- "Add to cellar" / "Buy" actions are NOT shown in this design — confirm with product whether they should live in the footer band.

---

### Screen 04 — Compare (Side by Side)

**File reference:** `vinotheque.jsx` → `VinCompare`

**Purpose.** Two wines weighed against each other. Reached from "Side by side ⇆" on Screen 02 or a future multi-select.

**Layout.** Paper frame. Top: small masthead. Body is a 2-column grid (`1fr 1px 1fr`) with a vertical `INK @ 0.4` rule separating the panes. Each pane (`padding: 22px 28px`) contains:

- Top row (`flex justify-between baseline`):
  - Left: eyebrow (`À gauche · <Appellation>` for left pane, `À droite · <Appellation>` for right) in italic Cormorant 10px uppercase letter-spacing 3, wine's `accent`. Wine name in Cormorant 32px line-height 1 letter-spacing -0.5. Producer + vintage in italic EB Garamond 13px `INK_SOFT`.
  - Right: `Bottle` atom size 36, Burgundy or Bordeaux shape based on region.
- `FlavorWheel` at size 170 centred (padding-top 4).
- Full `StructureBars` (all 5 dimensions: tannin/acidity/body/sweetness/oak).
- Tasting note pull-quote: EB Garamond 12.5px line-height 1.55 `INK`, wrapped in italic Cormorant accent quotation marks.
- Bottom row (`margin-top auto`, flex justify-between baseline): score + price in Cormorant 32px (score in `accent`, ` · $185` in 12px `INK_SOFT @ 0.7`); peak year in italic Cormorant 12px `INK_SOFT`.

**Verdict band** — absolute (left 0, right 0, bottom 0), `padding: 14px 40px 44px`, background `INK`, text `PAPER`:
- Eyebrow: italic Cormorant 9px uppercase letter-spacing 4 opacity 0.7 — "The Editor's Verdict".
- Body: italic Cormorant 18px line-height 1.35, margin-top 4. Wine names highlighted in their respective `tint` colours.

**Behaviour.**
- Pre-selected wines populate from the route (`/compare?a=brunello&b=barolo`).
- Future: allow the user to swap either pane via a chooser.

---

## Wine Signals (Shared Atoms)

These are the reusable components driving the design system. All accept a `palette` prop with `{ ink, paper, accent, glass, tint }` for per-wine theming. Source in `atoms.jsx`.

### `Masthead`

**File reference:** `vinotheque.jsx` → `Masthead`

A centred 3-row block with a 2px solid `INK` bottom border:
- Row 1: "Volume XII · Number IV" — Cormorant 10px letter-spacing 6 uppercase `INK_SOFT`
- Row 2: "Vinothèque" — Cormorant 56px (`small=false`) or 36px (`small=true`), weight 500, letter-spacing -1, line-height 0.95, `INK`
- Row 3: flex-between baseline — left: italic EB Garamond 11px `INK_SOFT` dateline (e.g. "A Private Cellar Review"); right: "Est. MMXIV" — Cormorant 10px letter-spacing 3 uppercase `INK_SOFT`

Padding: `28px 40px 14px` (or `18px 32px 12px` small).

### `FlavorWheel`

A radar/spider chart of named aroma spokes (8 typical) on concentric rings.

- `size` (default 220), `rings` (default 4), `palette`, `data` (object of `{ "Dried Cherry": 9, ... }`, values 0–10).
- Rings: `n` evenly-spaced circles, stroke `palette.ink @ 0.12`, stroke-width 0.6.
- Spokes: from centre to outer ring at each entry's angle, stroke `palette.ink @ 0.18`, stroke-width 0.6.
- Polygon: connects each entry's point at `(v/10) * maxR`, fill `palette.accent @ 0.18`, stroke `palette.accent` stroke-width 1.2.
- Dots: 2px circles on each polygon vertex in `palette.accent`.
- Labels: Cormorant 9px uppercase letter-spacing 0.5 `palette.ink` 14px outside the outer ring; text-anchor `start`/`end`/`middle` chosen by spoke angle.

`maxR = size * 0.34`.

### `StructureBars`

Old-print scales for tannin / acidity / body / sweetness / oak.

- Three-column grid per row: `74px 1fr 18px`, gap 10, align centre.
- Left: italic EB Garamond 13px lowercase label, `palette.ink @ 0.78`.
- Centre: 200×12 viewBox SVG (or 200×10 when `compact`):
  - Baseline: `line 0,6→200,6` stroke `ink @ 0.25` width 0.6
  - 11 tick marks at x=0,20,40…200, y from 2 to 10, stroke `ink @ 0.4` (every 5th) or `0.2`, width 0.6
  - Fill bar: rect `(0, 4, v*20, 4)` fill `accent` opacity 0.85
  - Knob: 3px circle at `(v*20, 6)` fill `accent`, stroke `palette.paper` width 1
- Right: Cormorant 12px value `palette.ink @ 0.6` right-aligned.

`compact=true` reduces row gap from 10 to 4 and SVG height from 14 to 10.

### `RegionMap`

A stylised country silhouette with locator dot and dashed leader line to a labelled appellation.

- `country` keys to a hand-tuned SVG path (Italy, France currently — extend with more as needed).
- `lat`, `lon` project onto the silhouette's roughed-in lat/lon ranges (see `COUNTRY_BOX` in `atoms.jsx`).
- Drawing inside `viewBox="0 0 100 100"`:
  - Path: country silhouette, stroke `palette.ink @ 0.55` width 0.8 stroke-linejoin round, fill none.
  - Concentric locator: 6px ring stroke `accent @ 0.4`, 2.5px filled dot in `accent`.
  - Leader: 1px dashed line from dot to right edge `(92, cy)`, stroke `ink @ 0.35` stroke-dasharray "1 2" width 0.5.
  - Optional label at `(94, cy+2)`: italic EB Garamond 6px text-anchor end `ink`.

If you replace with a real geo library, keep the visual restraint — line art only, no fills, dashed leader, italic label.

### `GlassPour`

A wine-glass silhouette with the wine's `glass` colour filled to a given level.

- `size` 100, `fill` 0–1 (default 0.55).
- Bowl: cubic path forming an ellipse with stem and base; clipPath used to confine the wine fill to the bowl interior.
- Wine fill: filled rect through clipPath, opacity 0.85.
- Glass outline: stroke `ink @ 0.6` width 0.8.

### `Bottle`

A bottle silhouette with a coloured label panel. Two shapes:
- **Bordeaux** — straight shoulders.
- **Burgundy** — sloped shoulders.

Body filled in `palette.glass` opacity 0.92 with `ink @ 0.5` 0.6-width stroke. Label panel from `(0.08, 0.55)` to `(0.92, 0.83)` in `palette.tint` with thin `ink @ 0.3` stroke and 2–3 dummy text lines.

### `DrinkingWindow`

A horizontal timeline showing drink-from / peak / drink-until plus the current year as a downward triangle marker.

- `drink = { from, peak, until }`, optional `currentYear` (defaults to 2026).
- Range padding: `start = drink.from - 2`, `end = drink.until + 2`.
- Top track: 2px line `ink @ 0.2`.
- Active band: between `drink.from` and `drink.until`, 8px tall `accent @ 0.25` block + 2px `accent` line at centre.
- Peak: 1px `accent` vertical bar at `drink.peak`, with italic 10px `accent` "peak" label above.
- Current year: 5×7 triangle pointing down in `ink`.
- Year ticks every 5 years below the track at 10px `ink @ 0.6`.

### `Fleuron`

A printer's ornament for decorative rules. SVG: short horizontal rules left and right of a vertical "leaf" diamond shape with three small dots. `size = 26`, defaults `color = INK`.

### `RuleDouble`

The double horizontal rule used between bands. Implement as a `div` with `border-top: 1px solid INK`, `opacity 0.5`, nested div with `border-top: 0.5px solid INK; margin-top: 2px`.

---

## Interactions & Behaviour

- **Navigation**: Preferences → submit → Flight → click entry → Detail; "Side by side" from Flight → Compare.
- **Refine pills**: client-side update of recommender query → re-render Flight.
- **Score / score-out-of-100**: pulled from a critic source per wine.
- **Per-wine colour**: every page tint, accent, chart fill, glass, and bottle colour is driven by the wine's `color` palette. Do NOT theme by wine type ("red"/"white" buckets) — use the actual colour values.
- **No motion / animation** is specified in this iteration; the design reads as static printed editorial. If transitions are added between routes, prefer a slow page-turn / cross-fade over slides or scales.
- **Empty states / error states** are NOT designed yet. Confirm with product before shipping.
- **Responsive behaviour** is NOT designed yet. The prototype is fixed at desktop widths (780–840px artboards). A mobile layout will need to:
  - Stack the detail triptych vertically.
  - Collapse the list entry from 3 columns to 1 with the terroir cartouche moving to a small inline strip.
  - Drop the absolute-positioned footer in favour of an inline section.

---

## State Management

Minimum state needed per screen:

- **Preferences**: occasion, menu, cellar leanings (multi), temperament, ceiling, count → posts to recommender backend.
- **Flight**: list of recommended wines + active refine pill + recommendation rationale.
- **Detail**: full wine record (see "Sample Wine Data") including flavor wheel data, structure bars, drinking window, pairings, critic score.
- **Compare**: two wine records by id.

The HTML prototype hard-codes wine data in `wine-data.js`. In production, wines come from your wine DB; the *recommendation* (rank, fit reasons, palate copy) comes from the recommender service.

---

## Sample Wine Data

The full structure each wine record uses in the prototype is in `design_files/wine-data.js`. Reproduced for reference:

```js
{
  id: 'brunello',
  rank: 1,
  name: 'Brunello di Montalcino',
  producer: 'Biondi-Santi',
  vintage: 2016,
  region: 'Tuscany',
  country: 'Italy',
  appellation: 'Montalcino · DOCG',
  coords: { lat: 43.05, lon: 11.49 },
  grape: 'Sangiovese (Brunello clone)',
  price: 185,
  abv: 14.5,
  drink: { from: 2024, peak: 2030, until: 2042 },
  color: { glass: '#7d1f24', tint: '#f4dcd3', ink: '#3a0d10', accent: '#9a2a30' },
  confidence: 'high',
  confidenceNote: 'Strong style overlap with cellar favourites',
  bars: { tannin: 8, acidity: 7, body: 8, sweetness: 1, oak: 6 },  // each 0–10
  wheel: { 'Dried Cherry': 9, 'Leather': 6, /* ... 8 spokes */ },  // each 0–10
  nose: 'dried cherry · leather · tobacco · forest floor',
  palate: 'A structured Sangiovese…',
  fits: ['structured tannin', 'savoury earth', 'dried cherry', 'long finish'],
  pairs: ['Bistecca alla Fiorentina', 'Aged pecorino', 'Wild boar ragù'],
  critic: { score: 96, source: 'Galloni' },
}
```

---

## Assets

No bitmap or vector assets ship with this design. Everything is SVG-drawn:
- Bottle, glass, region map, fleuron, flavor wheel, structure bars, drinking window are all rendered inline from the data in `wine-data.js`.
- Type is loaded from Google Fonts (Cormorant Garamond + EB Garamond).
- No icons or photographs are used. If marketing wants real wine bottle photography on the detail page, it should sit alongside (not replace) the SVG bottle / glass — those carry the per-wine colour signal.

---

## Files

In `design_files/`:

| File | What it contains |
|---|---|
| `index.html` | Prototype host — loads React/Babel, mounts the design canvas with all four screens (A and B side-by-side), Tweaks panel |
| `vinotheque.jsx` | **Direction A — implement this.** All four screens (`VinPreferences`, `VinList`, `VinDetail`, `VinCompare`) + sub-components |
| `almanac.jsx` | **Direction B — reference only.** Used only to source the "terroir cartouche" for Screen 02 |
| `atoms.jsx` | Shared wine signals — `FlavorWheel`, `StructureBars`, `RegionMap`, `GlassPour`, `Bottle`, `Fleuron`, `RuleDouble`, `DrinkingWindow` |
| `wine-data.js` | Sample wine records — three wines used throughout the prototype |

---

## Open Questions for Product

1. **Empty / error / loading states** — not designed yet. Recommender failure? No wines match filters? Cellar not yet uploaded?
2. **Add-to-cellar / buy actions** — should they live on the Detail footer band? Or float as a sticky action bar?
3. **Mobile breakpoint** — not designed. Highest priority screens?
4. **More than two wines in Compare** — should the layout extend to 3, or does Compare cap at 2?
5. **Refine pills on the flight** — are these a fixed set, or dynamic per query?
6. **Critic source** — is the "Editor's Score" the recommender's own confidence, an external critic, or both?
