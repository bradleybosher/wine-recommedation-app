# CLAUDE.md — Wine List Recommender

Portfolio-grade web app: upload restaurant wine list (PDF/OCR) + CellarTracker taste profile → ranked top-3 recommendations. Pre-booking research tool, not at-the-table lookup.

## Tech Stack
- **Backend:** Python/FastAPI, PyMuPDF/fitz (PDF), pytesseract + PIL (OCR), Ollama (local LLM inference), SQLite (response cache), JSON files (inventory + profile)
- **Frontend:** React 19 + TypeScript + Tailwind CSS v4 + Vite, glassmorphism design system

## Data Flow
```
CellarTracker TSV → inventory.json (cellar bottles)
CellarTracker export (any type) → profile_data.json (taste profile)
→ restaurant wine list upload (PDF/photo) → parsed text (parser.py)
→ Ollama (profile enrichment) → enriched taste profile text
→ Ollama (wine list + enriched profile + cellar context) → ranked top-3 + reasoning
```
**Modules:** `backend/main.py` (routes), `backend/parser.py` (PDF/OCR), `backend/models.py` (Pydantic schemas), `backend/recommender.py` (Ollama LLM), `backend/inventory.py` (TSV parse, cellar load/save), `backend/profile.py` (taste profile), `backend/prompt.py` (system prompt), `backend/cache.py` (SQLite cache)

## Recommendation Logic (`recommender.py`)
- Full parsed wine list + enriched taste profile in a single prompt; reason on **style fit**, not region/varietal
- Profile enriched via a preliminary Ollama call in `profile.build_enriched_profile_text()` before the main recommendation call
- Specific per-wine reasoning; include list quality assessment; structured JSON output via Pydantic

## Docs
`docs/llm/MEMORY.md` — master index; `docs/llm/context-guide.md` — task-to-doc mapping

## Principles
- Fail loudly (surface parse errors, don't pass noise to LLM); schema-driven (Pydantic is the contract)
- No user accounts or auth; SQLite cache + JSON files for local persistence (no external DB)
- Portfolio-legible; no premature generalisation; no auth/feedback loop in v1

---

## Claude Code Rules

### 1. API & Data Contract
- **SDK Only:** ALL backend calls via `frontend/src/client/sdk.gen.ts`. No manual `fetch`/`axios`.
- **Type Safety:** Use `src/client/types.gen.ts`. Do not redefine types locally.
- **Sync Protocol:** After Python changes, STOP — ask user to run `sync_types.bat` before any frontend updates.

### 2. Command Execution (Windows)
- **Sequential Only:** Never use `&&` or `;` — separate Bash tool calls only.
- **No `cd`:** Use absolute paths from project root; backslashes in shell commands.
- **Venv:** `.\backend\.venv\Scripts\python.exe -m [module]` for all backend tasks.

### 3. Python & Backend
- All Pydantic models: `ConfigDict(alias_generator=to_camel, populate_by_name=True)`.
- `/recommend` and `/upload-inventory` require `FormData` in the frontend.

### 4. Frontend & Styling
- **Imports:** `@/` alias only. No relative `../../` paths. Do not modify `vite.config.ts`.
- **Cards:** `<GlassCard>` only — no `bg-white` containers.
- **Background:** `<VibrantBackground>` in `App.tsx`; no background-color on page containers.
- **Icons:** `lucide-react` only; always `strokeWidth={1.5}`; no inline SVGs.
- **Colour:** Wine palette + glass tokens from `src/index.css @theme`. No hardcoded hex/rgba.
- **Text on glass:** White-based only (`text-white/70` minimum). No `text-gray-*` in `GlassCard`.

### 5. Context Control
- Full paths from root (e.g., `frontend/src/pages/App.tsx`). No `ls -R`, `pwd`, or `tree`.
- Only read files directly involved in the logic. Flag debt immediately.
