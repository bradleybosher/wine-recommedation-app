# Wine List Recommender

A portfolio-grade web application for pre-dinner wine list analysis. Users upload a restaurant wine list (PDF primary, photo/vision fallback), configure a taste profile, and receive ranked wine recommendations (default top-3, configurable) with per-wine enrichment and reasoning.

**Designed for:** Pre-booking research. Not an at-the-table lookup tool.

---

## Features

- **Smart Wine Parsing:** Extract structured wine data from restaurant PDFs via PyMuPDF; scanned PDFs and photos route to Claude Haiku vision extraction automatically
- **Two Onboarding Paths:**
  - CellarTracker TSV import — highest-fidelity, grounded in your actual ratings.
  - **Seed-bottle onboarding** — name 3–7 wines you have loved (and a few you disliked); Claude infers your palate in 60 seconds. Profiles are tagged `medium`/`high` confidence and downstream recommendations are flagged as directional.
- **Taste Profile:** One-click CellarTracker import (TSV export) to understand user preferences
- **Profile Tab:** View your palate portrait, cellar stats, and heuristic taste-marker bars (acidity, tannin, body, oak) in a dedicated profile view
- **LLM-Powered Recommendations:** Structured wine recommendations via Claude (Anthropic API, tool use)
- **Structured Output:** JSON-validated recommendations (default top-3, configurable) with per-wine reasoning, confidence scores, enrichment fields (grape, region, aroma wheel, structure bars, food pairings), and list quality assessment
- **Why This Fits You:** Each recommendation surfaces 2–3 short tags grounding the pick in concrete signals from your taste profile (top regions, preferred descriptors, avoided styles, taste markers)
- **One-Click Refine:** After results render, tap a chip ("Under $80", "More adventurous", "Food match first", "Safer crowd-pleaser") to re-rank the same wine list against a different lens — no re-upload
- **Recommendation Scoring:** Every response is silently scored across four dimensions (confidence, completeness, grounding, budget fit) and logged to `logs/recommendations.jsonl` for analysis
- **Vinothèque Editorial UI:** React 19 + Tailwind CSS v4 + react-router-dom; old-world paper/serif editorial design system; four-screen flow (Preferences → Flight → Detail → Compare); works on desktop and tablet

---

## Tech Stack

### Backend
- **FastAPI** — REST API with structured logging and exception handling
- **Pydantic v2** — Data validation with camelCase aliases for frontend compatibility
- **PyMuPDF (`fitz`)** — PDF text extraction
- **Anthropic API (Claude)** — LLM inference for profile enrichment, seed-bottle onboarding, image/vision extraction, and recommendations; no local model required
- **pytesseract / Pillow** — OCR fallback for images when Tesseract is installed (optional)
- **SQLite** — Response caching and parse caching for identical requests

### Frontend
- **React 19** + **TypeScript** — Type-safe UI components
- **Vite** — Fast development and production builds
- **Tailwind CSS v4** — Utility-first base with Vinothèque editorial design tokens (ink, paper, oxblood)
- **react-router-dom** — Four-screen routed flow: Preferences → Flight → Detail → Compare
- **@hey-api/openapi-ts** — Auto-generated SDK from backend OpenAPI spec

### Data Contract
- OpenAPI 3.0 spec drives both backend and frontend code generation
- No manual type definitions; backend Pydantic models generate the contract

---

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/)

### 1. Backend Setup

```bash
cd wine-recommendation-app/backend

# Create virtual environment
python -m venv .venv

# Activate
# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and edit .env
cp .env.example .env
# Set ANTHROPIC_API_KEY in .env

# Run the API
python -m uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Check the OpenAPI docs at `/docs`.

### 2. Frontend Setup

```bash
cd wine-recommendation-app/frontend

npm install

# Start dev server (runs on http://127.0.0.1:5173)
npm run dev
```

Open http://127.0.0.1:5173 in your browser.

---

## Usage Walkthrough

### 1. Choose Your Pathway
On first launch, pick how you want to build a taste profile:
- **I use CellarTracker** — upload your cellar + tasting-history TSV exports (highest fidelity).
- **Name a few wines I love** — type 3–7 wines you have loved (and optionally a few you disliked). No exports required. Claude infers your palate via a single tool-use call.

### 2a. CellarTracker pathway — Upload Wine Inventory
- Upload a CellarTracker TSV export (export from cellartracker.com → Downloads → List), or skip.
- The app parses your cellar and extracts style preferences.

### 2b. CellarTracker pathway — Upload Taste Profile (Optional)
- Upload a CellarTracker **"Notes"** export to add tasting notes
- Wines with low ratings inform the `avoided_styles` field
- You can skip this; recommendations work with inventory alone

### 2c. Seed-bottle pathway — Name Your Wines
- Enter producer, wine, and (optional) vintage for 3–7 loved bottles.
- Add up to 3 disliked bottles to sharpen the signal.
- Submit; the inferred profile renders inline with style descriptors, grapes, regions, and a confidence tag. The profile is marked `seed_bottles` and per-recommendation confidence is capped at `medium`.

### 3. Get Recommendations
- Choose a restaurant wine list (PDF, JPEG, PNG, or similar)
- Describe your meal (e.g., "Pan-seared duck breast with cherry gastrique")
- Optionally override style preferences (e.g., "mineral whites, grower champagne")
- Click **"Get Recommendations"**
- Receive a ranked top-3 with specific reasoning tied to your profile
- Use the **Refine** chips above the results to re-rank against a different lens (budget, adventurousness, food-first, crowd-pleaser) without re-uploading the list

---

## Architecture

```
User uploads wine list (PDF/photo)
    ↓
Parser dispatches by content type (parser.py)
  — PDF: PyMuPDF text layer; if sparse/food-menu detected → Claude Haiku vision extraction
  — Image: Claude Haiku vision extraction
    ↓
Load cellar inventory + taste profile from prior uploads
    ↓
Enrich taste profile via Anthropic Claude (profile.py)
  — tool-use call; converts raw frequency data to natural-language palate description
  — skipped when profile_source == "seed_bottles" (already enriched at onboarding)
    ↓
Parse meal description (meal_parser.py) → pairing hints string
    ↓
Build system prompt (prompt.py):
  — Enriched taste profile
  — Cellar character summary (top varietals/regions)
  — Relevant owned bottles
  — Meal pairing hints
    ↓
Claude (Anthropic API, tool use) → WineRecommendation[] (validated via Pydantic)
    ↓
Score recommendation silently (scorer.py) — 4 dimensions, 0–1 float
Log event to logs/recommendations.jsonl (logging_utils.py)
    ↓
Cache response in SQLite → return to frontend
```

### Key Modules

| File | Purpose |
|---|---|
| `main.py` | Composition root: env bootstrap, logging, middleware, router includes |
| `bootstrap.py` | Loads .env; exposes `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `MAX_UPLOAD_BYTES` |
| `logging_setup.py` | Configures the `sommelier` logger tree (rotating file + stderr) |
| `middleware.py` | Request-logging middleware + exception handlers (request ID, elapsed_ms) |
| `rate_limit.py` | IP-based 10-req/60s limiter for `/recommend` |
| `cellar_terms.py` | Frequency-ranked cellar terms + character phrase helpers |
| `routes/inventory.py` | `/upload-inventory`, `/inventory` |
| `routes/profile.py` | `/upload-profile`, `/seed-profile`, `/profile/revert`, `/profile-summary` |
| `routes/recommend.py` | `/recommend` pipeline |
| `routes/debug.py` | Diagnostics endpoints (health, status, logs, cache) |
| `parser.py` | PDF/text/image dispatch; PyMuPDF + Claude Haiku vision |
| `models.py` | Pydantic schemas (camelCase JSON mapping) |
| `recommender.py` | Anthropic Claude tool-use call, retry logic, Pydantic validation |
| `prompt.py` | System prompt construction + schema definition |
| `profile.py` | CellarTracker parsing, taste profile building, Anthropic enrichment |
| `seed_profile.py` | Seed-bottle onboarding: Claude tool-use inference from 3–7 named wines |
| `meal_parser.py` | Meal description → `MealProfile` dataclass → pairing hints string |
| `inventory.py` | Cellar loading/saving, relevance filtering, wine-list pre-filtering |
| `scorer.py` | 4-dimension recommendation quality scorer; `ScoringResult` dataclass |
| `logging_utils.py` | JSONL event logger to `logs/recommendations.jsonl` |
| `retry_utils.py` | Generic retry helper with exponential backoff |
| `cache.py` | SQLite response + parse caching |

---

## Design Principles

- **Stateless First:** No user accounts, logins, or persistent sessions (v1)
- **Fail Loudly:** Parse errors surface to the user rather than passing garbage to the LLM
- **Schema-Driven:** Pydantic models define the contract; endpoints validate strictly
- **Portfolio-Legible:** Code is readable to a technical hiring audience; no clever abstractions that obscure intent
- **API-First:** Anthropic Claude handles enrichment, seed-bottle inference, vision extraction, and recommendations — no local model required

---

## Environment Variables

Create a `.env` file in the `backend/` directory (or copy from `.env.example`):

```
ANTHROPIC_API_KEY=sk-ant-...              # Required — Anthropic API key
ANTHROPIC_MODEL=claude-sonnet-4-6        # Model to use (default: claude-sonnet-4-6)
```

---

## Development

### Running Tests

```bash
cd backend
python -m pytest tests/
```

The test suite covers scorer edge cases, meal parser synonym normalisation, text extraction, and OpenAPI schema sync (27 tests). LLM-dependent routes are not unit-tested.

### Regenerating Frontend Types

If the backend OpenAPI spec changes, regenerate the TypeScript SDK:

```bash
cd frontend
npm run generate-types
```

This reads the backend OpenAPI spec and regenerates `src/client/types.gen.ts`.

### Debugging

**Backend:** Logs are written to `backend/logs/api.log` and stdout. Request IDs are included for tracing. Recommendation events (meal, score breakdown, wine names) are appended to `backend/logs/recommendations.jsonl`.

**Frontend:** Enable the debug panel by setting `VITE_SHOW_DEBUG=true` in your `.env` (frontend root):
```
VITE_SHOW_DEBUG=true
```

The debug panel shows:
- Current inventory (bottles, freshness)
- Parsed taste profile
- Cache stats and diagnostic endpoints

---

## Known Constraints

- **OCR Quality:** Phone photos vary in legibility; PDFs are preferred. Claude Haiku vision is the primary image extraction path; pytesseract is an optional fallback.
- **Wine List Formats:** Parser handles common formats but may fail on unusual layouts
- **LLM Quality:** Recommendations depend on the configured Anthropic model (`claude-sonnet-4-6` default)
- **Rate Limiting:** `/recommend` is limited to 10 requests per IP per 60 seconds
- **Accent Folding:** Only handles Latin wine regions; Cyrillic/CJK region names may not match correctly

---

## Future Ideas (v2+)

- Feedback loop: user ratings → profile refinement over time
- Vivino OAuth import as a profile source
- Food pairing as a first-class input (e.g., "duck + cherry gastrique" → style recommendations)
- Restaurant wine list caching + historical price tracking

---

## License

Portfolio project. Use freely for educational and hiring demonstration purposes.

---

## Questions?

This app demonstrates:
- Full-stack API design with Pydantic + FastAPI
- Type-safe frontend code generation from OpenAPI specs
- LLM integration with structured output via Anthropic tool use
- Practical error handling, scoring, and caching strategies
- Clean architecture and portfolio-readable code

Perfect for discussing software engineering practices in interviews.
