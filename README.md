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
- **Edit Your Palate:** From the landing page, open *Your palate* to inline-edit your style summary, taste markers, top varietals/regions, preferred descriptors, avoided styles, and average spend; or "Start over" by re-uploading CellarTracker, re-seeding from a few wines, or reverting to the last backup
- **LLM-Powered Recommendations:** Structured wine recommendations via Claude (Anthropic API, tool use)
- **Structured Output:** JSON-validated recommendations (default top-3, configurable) with per-wine reasoning, confidence scores, enrichment fields (grape, region, aroma wheel, structure bars, food pairings), and list quality assessment
- **Why This Fits You:** Each recommendation surfaces 2–3 short tags grounding the pick in concrete signals from your taste profile (top regions, preferred descriptors, avoided styles, taste markers)
- **Cellar Anchor Lead-in:** The first sentence of each wine's reasoning is surfaced prominently — highlighted in accent colour when it references a wine already in your cellar ("Like your…"), otherwise shown as a soft profile-fit note
- **Grounding Badge:** In winelist mode each card shows `✓ on list` or `⚠ not verified` below the price so you know at a glance which recommendations are confirmed on the actual menu
- **Structure Comparison Strip:** Below the wine cards, a 5 × N matrix (tannin · acidity · body · sweetness · oak) renders SVG bars coloured per wine palette so you can compare structure across the flight at a glance
- **One-Click Refine:** After results render, tap a chip ("Under $80", "More adventurous", "Food match first", "Safer crowd-pleaser") to re-rank the same wine list against a different lens — no re-upload
- **Post-Flight Feedback Chips:** Rate the flight ("Too bold", "Over budget", "Off profile", "Perfect") with one tap; feedback is saved to the flight record and surfaces a nudge to refine your palate on the Profile page
- **One-Tap Profile Deepening:** If the top-ranked wine's grape isn't yet in your profile, a callout prompts you to add it with a single tap — keeping your profile in sync with what you're actually enjoying
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

# Generate and set JWT_SECRET (required for auth)
python -c "import secrets; print(secrets.token_hex(32))"
# Copy the output and add to .env as: JWT_SECRET=<value>

# Set ANTHROPIC_API_KEY in .env

# Run the API
python -m uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Check the OpenAPI docs at `/docs`.

**Important:** The backend now requires `JWT_SECRET` to be set in `.env`. If missing, the app will fail to start with a clear error message.

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

### 1. Register or Login

**First time?** Click **Register** on the login page.
- Enter an email and password.
- You'll be logged in automatically and directed to create your first taste profile.
- If you have an existing wine list and profile from an earlier pre-auth deployment, they'll be automatically migrated to your new account.

**Returning user?** Click **Login** and enter your credentials.

### 2. Choose Your Profile & Pathway

Once logged in, you're in the **Profiles** view. Click **Create Profile** to add a new taste profile, or select an existing one.

For each profile, you can build a taste palate in two ways:
- **CellarTracker pathway** (highest fidelity) — upload your cellar + tasting-history TSV exports
- **Seed-bottle pathway** (60 seconds) — name 3–7 wines you love (and optionally a few you dislike); Claude infers your palate.

### 3a. CellarTracker pathway — Upload Wine Inventory

- Go to your active profile's **Inventory** tab.
- Upload a CellarTracker TSV export (export from cellartracker.com → Downloads → List), or skip.
- The app parses your cellar and extracts style preferences.

### 3b. CellarTracker pathway — Upload Taste Profile (Optional)

- Still in the **Inventory** tab, optionally upload a CellarTracker **"Notes"** export to add tasting notes.
- Wines with low ratings inform the `avoided_styles` field.
- You can skip this; recommendations work with inventory alone.

### 3c. Seed-bottle pathway — Name Your Wines

- In the **Palette** tab, click **Seed from bottles**.
- Enter producer, wine, and (optional) vintage for 3–7 loved bottles.
- Add up to 3 disliked bottles to sharpen the signal.
- Submit; the inferred profile renders inline with style descriptors, grapes, regions, and a confidence tag.
- The profile is marked `seed_bottles` and per-recommendation confidence is capped at `medium`.

### 4. Get Recommendations

Once your profile is set up:
- Go to the **Flight** tab (or **Get Recommendations** from the home page).
- Choose a restaurant wine list (PDF, JPEG, PNG, or similar).
- Describe your meal (e.g., "Pan-seared duck breast with cherry gastrique").
- Optionally override style preferences (e.g., "mineral whites, grower champagne").
- Click **"Get Recommendations"**.
- Receive a ranked top-3 with specific reasoning tied to your profile.
- Use the **Refine** chips above the results to re-rank against a different lens (budget, adventurousness, food-first, crowd-pleaser) without re-uploading the list.

### 5. Manage Your Profiles

- Click the **Profiles** link in the header to switch between taste profiles or create new ones.
- Each profile has its own inventory, taste data, and recommendation history.
- Logout with the logout button in the header.

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
| `routes/auth.py` | `/auth/register`, `/auth/login`, JWT validation & profile dependency |
| `routes/profiles.py` | `/profiles` (list/create), `/profiles/{id}` (get/update/delete) |
| `routes/inventory.py` | `/upload-inventory`, `/inventory` (requires auth + profile) |
| `routes/profile.py` | `/upload-profile`, `/seed-profile`, `/profile/revert`, `/profile-summary`, `/profile` PATCH (requires auth + profile) |
| `routes/recommend.py` | `/recommend` pipeline (requires auth + profile) |
| `routes/history.py` | `/history` (list/detail/feedback/delete) (requires auth + profile) |
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

## Authentication

**Registration & Login**

The app now uses JWT bearer token authentication. Account registration is open — no invite required.

1. **Register a new account** — `POST /auth/register` with `email` and `password`. Returns a JWT bearer token and creates a default `default` profile automatically.
2. **Login** — `POST /auth/login` with `email` and `password`. Returns a JWT bearer token.
3. **Multiple profiles** — Use `POST /profiles` to create additional named taste profiles (e.g., "Whites", "Under $50"). Each profile maintains its own inventory, taste data, and flight history.
4. **Switching profiles** — The frontend passes the active profile ID via the `X-Profile-Id` header (or select it from `/profiles` to list your profiles).

**JWT Bearer Tokens**

All authenticated endpoints require:
- `Authorization: Bearer <jwt>` header (obtained at registration/login)
- `X-Profile-Id` header specifying the active profile UUID

The first registered account on a fresh deployment automatically inherits any pre-existing profile data (single legacy `profile_data.json` and `inventory.json`). Subsequent users start with empty profiles.

**Setup**

Generate a JWT secret for production use:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Add it to `.env` as:
```
JWT_SECRET=<generated-value>
```

## Design Principles

- **Multi-Account, Single-Tenant Architecture:** User accounts with JWT tokens; each user can create multiple named taste profiles scoped to their account. Pre-auth profile data migrated on first login.
- **Fail Loudly:** Parse errors surface to the user rather than passing garbage to the LLM
- **Schema-Driven:** Pydantic models define the contract; endpoints validate strictly
- **Portfolio-Legible:** Code is readable to a technical hiring audience; no clever abstractions that obscure intent
- **API-First:** Anthropic Claude handles enrichment, seed-bottle inference, vision extraction, and recommendations — no local model required

---

## Environment Variables

Create a `.env` file in the `backend/` directory (or copy from `.env.example`):

```
JWT_SECRET=<32+ hex chars>                # Required — generate with: python -c "import secrets; print(secrets.token_hex(32))"
ANTHROPIC_API_KEY=sk-ant-...              # Required — Anthropic API key
ANTHROPIC_MODEL=claude-sonnet-4-6        # Model to use (default: claude-sonnet-4-6)
```

**Authentication Setup**

The app uses JWT bearer tokens for authentication. Generate a secure secret:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and add it to `.env` as `JWT_SECRET=<value>`. If `JWT_SECRET` is not set, the backend will refuse to start.

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

## Future Ideas (v3+)

- Vivino OAuth import as a profile source
- Food pairing as a first-class input (e.g., "duck + cherry gastrique" → style recommendations)
- Restaurant wine list caching + historical price tracking
- Team/cellar sharing — invite other users to view/edit a profile
- Analytics dashboard — flavor trends, recommendation accuracy, spending patterns across flights

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
