# CLAUDE.md — Wine List Recommender

Portfolio-grade web app: upload restaurant wine list (PDF/OCR) + CellarTracker taste profile → ranked top-3 recommendations. Pre-booking research tool, not at-the-table lookup.

## Tech Stack
- **Backend:** Python/FastAPI, PyMuPDF/fitz (PDF), pytesseract + PIL (OCR), Ollama (local LLM), SQLite (cache), JSON (inventory + profile)
- **Frontend:** React 19 + TypeScript + Tailwind CSS v4 + Vite, glassmorphism design system

## Data Flow
```
CellarTracker TSV → inventory.json | CellarTracker export → profile_data.json
→ wine list upload (PDF/photo) → parser.py → Ollama (enrich profile) → Ollama (recommend) → top-3
```
**Modules:** `main.py` (routes), `parser.py` (PDF/OCR), `models.py` (Pydantic), `recommender.py` (LLM), `inventory.py` (cellar), `profile.py` (taste), `prompt.py` (prompt), `cache.py` (SQLite) — all in `backend/`

## Recommendation Logic
- Full wine list + enriched taste profile in one prompt; reason on **style fit**, not region/varietal
- Profile enriched via preliminary Ollama call (`profile.build_enriched_profile_text()`) before main call
- Per-wine reasoning; list quality assessment; structured JSON output via Pydantic

## Docs
- `docs/llm/MEMORY.md` — master index; `docs/llm/context-guide.md` — task-to-doc mapping
- **After every task:** update `docs/llm/`, `CLAUDE.md`, and `README.md` to reflect reality before closing

## Principles
- Fail loudly; schema-driven (Pydantic is the contract); no auth; SQLite + JSON for local persistence; portfolio-legible

---

## Claude Code Rules

### 1. Context Sources
- **HUMAN_NOTES.md:** Read-only. Use it to understand current thinking, active tasks, and known bugs. Never edit it.
- Full paths from root (e.g., `frontend/src/pages/App.tsx`). No `ls -R`, `pwd`, or `tree`.
- Only read files directly involved in the logic. Flag debt immediately.

### 2. API & Data Contract
- **SDK Only:** ALL backend calls via `frontend/src/client/sdk.gen.ts`. No manual `fetch`/`axios`.
- **Type Safety:** Use `src/client/types.gen.ts`. Do not redefine types locally.
- **Sync Protocol:** After Python changes, STOP — ask user to run `sync_types.bat` before any frontend updates.

### 3. Command Execution (Windows)
- **Sequential Only:** Never use `&&` or `;` — separate Bash tool calls only.
- **No `cd`:** Use absolute paths from project root; backslashes in shell commands.
- **Venv:** `.\backend\.venv\Scripts\python.exe -m [module]` for all backend tasks.

### 4. Python & Backend
- All Pydantic models: `ConfigDict(alias_generator=to_camel, populate_by_name=True)`.
- `/recommend` and `/upload-inventory` require `FormData` in the frontend.

### 5. Frontend & Styling
- **Imports:** `@/` alias only. No relative `../../` paths. Do not modify `vite.config.ts`.
- **Cards:** `<GlassCard>` only — no `bg-white` containers.
- **Background:** `<VibrantBackground>` in `App.tsx`; no background-color on page containers.
- **Icons:** `lucide-react` only; always `strokeWidth={1.5}`; no inline SVGs.
- **Colour:** Wine palette + glass tokens from `src/index.css @theme`. No hardcoded hex/rgba.
- **Text on glass:** White-based only (`text-white/70` minimum). No `text-gray-*` in `GlassCard`.
