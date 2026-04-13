# Wine List Recommender

A portfolio-grade web application for pre-dinner wine list analysis. Users upload a restaurant wine list (PDF primary, photo/OCR fallback), configure a taste profile, and receive a ranked top-3 recommendation with specific reasoning for each wine.

**Designed for:** Pre-booking research. Not an at-the-table lookup tool.

---

## Features

- **Smart Wine Parsing:** Extract structured wine data from restaurant PDFs via PyMuPDF
- **Taste Profile:** One-click CellarTracker import (TSV export) to understand user preferences
<<<<<<< HEAD
<<<<<<< HEAD
- **Profile Tab:** View your palate portrait, cellar stats, and heuristic taste-marker bars (acidity, tannin, body, oak) in a dedicated profile view
=======
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
- **Profile Tab:** View your palate portrait, cellar stats, and heuristic taste-marker bars (acidity, tannin, body, oak) in a dedicated profile view
>>>>>>> b169158 (Added my profile tab)
- **LLM-Powered Recommendations:** Structured wine recommendations via local Ollama inference
- **Structured Output:** JSON-validated top-3 recommendations with reasoning, confidence scores, and quality assessment
- **Offline-First:** Runs entirely locally (Ollama-based); no external API keys or account required
- **Responsive UI:** React 19 + Tailwind CSS; works on desktop and tablet

---

## Tech Stack

### Backend
- **FastAPI** — REST API with structured logging and exception handling
- **Pydantic v2** — Data validation with camelCase aliases for frontend compatibility
- **PyMuPDF (`fitz`)** — PDF text extraction
- **Ollama** — Local LLM inference (no API keys, runs on-device)
- **SQLite** — Response caching for identical requests

### Frontend
- **React 19** + **TypeScript** — Type-safe UI components
- **Vite** — Fast development and production builds
- **Tailwind CSS** — Utility-first styling
- **@hey-api/openapi-ts** — Auto-generated SDK from backend OpenAPI spec

### Data Contract
- OpenAPI 3.0 spec drives both backend and frontend code generation
- No manual type definitions; backend Pydantic models generate the contract

---

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Ollama (download from [ollama.ai](https://ollama.ai))

### 1. Install and Run Ollama

```bash
# Download Ollama from https://ollama.ai
# Start the Ollama service (runs on http://127.0.0.1:11434 by default)
ollama serve
```

In another terminal, pull a model:
```bash
ollama pull llama3.2:3b
```

### 2. Backend Setup

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

# Copy and edit .env if needed
cp .env.example .env

# Run the API
python -m uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Check the OpenAPI docs at `/docs`.

### 3. Frontend Setup

```bash
cd wine-recommendation-app/frontend

npm install

# Start dev server (runs on http://127.0.0.1:5173)
npm run dev
```

Open http://127.0.0.1:5173 in your browser.

---

## Usage Walkthrough

### 1. Upload Wine Inventory
- Click **"Start"** on the onboarding screen
- Upload a CellarTracker TSV export (export from cellartracker.com → Downloads → List)
- The app parses your cellar and extracts style preferences

### 2. Upload Taste Profile (Optional)
- Upload a CellarTracker **"Notes"** export to add tasting notes
- Wines with low ratings inform the `avoided_styles` field
- You can skip this; recommendations work with inventory alone

### 3. Get Recommendations
- Choose a restaurant wine list (PDF, JPEG, PNG, or similar)
- Describe your meal (e.g., "Pan-seared duck breast with cherry gastrique")
- Optionally override style preferences (e.g., "mineral whites, grower champagne")
- Click **"Get Recommendations"**
- Receive a ranked top-3 with specific reasoning tied to your profile

---

## Architecture

```
User uploads wine list (PDF/photo)
    ↓
Parser extracts text (parser.py) — PyMuPDF for PDF, pytesseract OCR for images
    ↓
Load cellar inventory + taste profile from prior uploads
    ↓
Enrich taste profile via Ollama (profile.py) — converts raw frequency data to natural-language palate description
    ↓
Build system prompt with:
  - Enriched taste profile (from CellarTracker history)
  - Cellar character summary (top varietals/regions)
  - Relevant owned bottles (for context)
    ↓
Send to Ollama (local LLM) + wine list text + meal description
    ↓
Validate JSON schema (WineRecommendation[])
    ↓
Cache response for identical inputs → return structured recommendations
```

### Key Modules

| File | Purpose |
|---|---|
| `main.py` | FastAPI app, routes, request logging, middleware |
| `parser.py` | PDF extraction (PyMuPDF) |
| `recommender.py` | LLM call + JSON parsing with error handling |
| `prompt.py` | System prompt construction + schema definition |
| `profile.py` | CellarTracker parsing, taste profile building |
| `inventory.py` | Cellar inventory loading, style-based filtering |
| `cache.py` | SQLite response caching |

---

## Design Principles

- **Stateless First:** No user accounts, logins, or persistent sessions (v1)
- **Fail Loudly:** Parse errors surface to the user rather than passing garbage to the LLM
- **Schema-Driven:** Pydantic models define the contract; endpoints validate strictly
- **Portfolio-Legible:** Code is readable to a technical hiring audience; no clever abstractions that obscure intent
- **Local-First:** Ollama runs locally; no external API keys or latency dependencies

---

## Environment Variables

Create a `.env` file in the `backend/` directory (or copy from `.env.example`):

```
OLLAMA_URL=http://127.0.0.1:11434        # Ollama API endpoint
OLLAMA_MODEL=llama3.2:3b                 # Model to use
```

---

## Development

### Running Tests

```bash
cd backend
python -m pytest tests/
```

### Regenerating Frontend Types

If the backend OpenAPI spec changes, regenerate the TypeScript SDK:

```bash
cd frontend
npm run generate-types
```

This reads the backend OpenAPI spec and regenerates `src/client/types.gen.ts`.

### Debugging

**Backend:** Logs are written to `backend/logs/api.log` and stdout. Request IDs are included for tracing.

**Frontend:** Enable the debug panel by setting `VITE_SHOW_DEBUG=true` in your `.env` (frontend root):
```
VITE_SHOW_DEBUG=true
```

The debug panel shows:
- Current inventory (bottles, freshness)
- Parsed taste profile
- System prompt used for the last recommendation

---

## Known Constraints

- **OCR Quality:** Phone photos vary in legibility; PDFs are preferred
- **Wine List Formats:** Parser handles common formats but may fail on unusual layouts
- **LLM Quality:** Recommendations are only as good as the local Ollama model (llama3.2:3b is reasonable but not state-of-art)
- **One Call Per Recommendation:** No multiple attempts; costs matter even locally

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
- LLM integration with structured output validation
- Practical error handling and caching strategies
- Clean architecture and portfolio-readable code

Perfect for discussing software engineering practices in interviews.
