# CLAUDE.md — Wine List Recommender

Portfolio-grade web app: upload restaurant wine list (PDF/OCR) + CellarTracker taste profile → ranked top-3 recommendations. Pre-booking research tool, not at-the-table lookup.

## Tech Stack
<<<<<<< HEAD
<<<<<<< HEAD
- **Backend:** Python/FastAPI, PyMuPDF/fitz (PDF), pytesseract + PIL (OCR), Ollama (local LLM), SQLite (cache), JSON (inventory + profile)
=======
- **Backend:** Python/FastAPI, PyMuPDF/fitz (PDF), pytesseract + PIL (OCR), Ollama (local LLM inference), SQLite (response cache), JSON files (inventory + profile)
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
- **Backend:** Python/FastAPI, PyMuPDF/fitz (PDF), pytesseract + PIL (OCR), Ollama (local LLM), SQLite (cache), JSON (inventory + profile)
>>>>>>> faa3422 (Commit despite broken recommendation engine)
- **Frontend:** React 19 + TypeScript + Tailwind CSS v4 + Vite, glassmorphism design system

## Data Flow
```
<<<<<<< HEAD
<<<<<<< HEAD
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

### Documentation Update Protocol (mandatory — complete before closing any task)

For every file modified, update the corresponding docs:

| Modified file | Update these docs |
|---|---|
| `backend/<module>.py` | `docs/llm/modules/<module>.md` + `docs/llm/interfaces.md` |
| Data flow or module list changed | `CLAUDE.md` (Data Flow + Modules line) |
| User-facing behaviour changed | `README.md` |

**Checklist (run through this before marking a task done):**
1. Does `docs/llm/modules/<module>.md` reflect the current function signatures and behaviour?
2. Does `docs/llm/interfaces.md` list all current public function signatures with correct parameters?
3. Are new constants, data structures, or pipelines documented?
4. Is `CLAUDE.md` still accurate (data flow, module list, recommendation logic)?
5. Is `README.md` still accurate for users?

## Principles
- Fail loudly; schema-driven (Pydantic is the contract); no auth; SQLite + JSON for local persistence; portfolio-legible
=======
CellarTracker TSV → inventory.json (cellar bottles)
CellarTracker export (any type) → profile_data.json (taste profile)
→ restaurant wine list upload (PDF/photo) → parsed text (parser.py)
→ Ollama (profile enrichment) → enriched taste profile text
→ Ollama (wine list + enriched profile + cellar context) → ranked top-3 + reasoning
=======
CellarTracker TSV → inventory.json | CellarTracker export → profile_data.json
→ wine list upload (PDF/photo) → parser.py → Ollama (enrich profile) → Ollama (recommend) → top-3
>>>>>>> faa3422 (Commit despite broken recommendation engine)
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
<<<<<<< HEAD
- Fail loudly (surface parse errors, don't pass noise to LLM); schema-driven (Pydantic is the contract)
- No user accounts or auth; SQLite cache + JSON files for local persistence (no external DB)
- Portfolio-legible; no premature generalisation; no auth/feedback loop in v1
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
- Fail loudly; schema-driven (Pydantic is the contract); no auth; SQLite + JSON for local persistence; portfolio-legible
>>>>>>> faa3422 (Commit despite broken recommendation engine)

---

## Claude Code Rules

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> faa3422 (Commit despite broken recommendation engine)
### 1. Context Sources
- **HUMAN_NOTES.md:** Read-only. Use it to understand current thinking, active tasks, and known bugs. Never edit it.
- Full paths from root (e.g., `frontend/src/pages/App.tsx`). No `ls -R`, `pwd`, or `tree`.
- Only read files directly involved in the logic. Flag debt immediately.

### 2. API & Data Contract
<<<<<<< HEAD
=======
### 1. API & Data Contract
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
>>>>>>> faa3422 (Commit despite broken recommendation engine)
- **SDK Only:** ALL backend calls via `frontend/src/client/sdk.gen.ts`. No manual `fetch`/`axios`.
- **Type Safety:** Use `src/client/types.gen.ts`. Do not redefine types locally.
- **Sync Protocol:** After Python changes, STOP — ask user to run `sync_types.bat` before any frontend updates.

<<<<<<< HEAD
<<<<<<< HEAD
### 3. Command Execution (Windows)
=======
### 2. Command Execution (Windows)
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
### 3. Command Execution (Windows)
>>>>>>> faa3422 (Commit despite broken recommendation engine)
- **Sequential Only:** Never use `&&` or `;` — separate Bash tool calls only.
- **No `cd`:** Use absolute paths from project root; backslashes in shell commands.
- **Venv:** `.\backend\.venv\Scripts\python.exe -m [module]` for all backend tasks.

<<<<<<< HEAD
<<<<<<< HEAD
### 4. Python & Backend
- All Pydantic models: `ConfigDict(alias_generator=to_camel, populate_by_name=True)`.
- `/recommend` and `/upload-inventory` require `FormData` in the frontend.

### 5. Frontend & Styling
=======
### 3. Python & Backend
- All Pydantic models: `ConfigDict(alias_generator=to_camel, populate_by_name=True)`.
- `/recommend` and `/upload-inventory` require `FormData` in the frontend.

### 4. Frontend & Styling
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
### 4. Python & Backend
- All Pydantic models: `ConfigDict(alias_generator=to_camel, populate_by_name=True)`.
- `/recommend` and `/upload-inventory` require `FormData` in the frontend.

### 5. Frontend & Styling
>>>>>>> faa3422 (Commit despite broken recommendation engine)
- **Imports:** `@/` alias only. No relative `../../` paths. Do not modify `vite.config.ts`.
- **Cards:** `<GlassCard>` only — no `bg-white` containers.
- **Background:** `<VibrantBackground>` in `App.tsx`; no background-color on page containers.
- **Icons:** `lucide-react` only; always `strokeWidth={1.5}`; no inline SVGs.
- **Colour:** Wine palette + glass tokens from `src/index.css @theme`. No hardcoded hex/rgba.
- **Text on glass:** White-based only (`text-white/70` minimum). No `text-gray-*` in `GlassCard`.
<<<<<<< HEAD
<<<<<<< HEAD
=======

### 5. Context Control
- Full paths from root (e.g., `frontend/src/pages/App.tsx`). No `ls -R`, `pwd`, or `tree`.
- Only read files directly involved in the logic. Flag debt immediately.
>>>>>>> 6caf2d0 (Initial commit: Setting up project structure)
=======
>>>>>>> faa3422 (Commit despite broken recommendation engine)
