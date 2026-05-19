# CLAUDE.md — Wine List Recommender

Portfolio-grade web app: upload restaurant wine list (PDF/OCR) + CellarTracker taste profile → ranked top-3 recommendations. Pre-booking research tool, not at-the-table lookup.

## Tech Stack
- **Backend:** Python/FastAPI, PyMuPDF/fitz (PDF), pytesseract + PIL (OCR), Anthropic API (Claude, tool use), SQLite (cache), JSON (inventory + profile)
- **Frontend:** React 19 + TypeScript + Tailwind CSS v4 + Vite + react-router-dom, old-world editorial design system (Vinothèque)

## Data Flow
```
Auth (JWT bearer; passlib bcrypt + PyJWT, HS256, 7-day expiry):
  /auth/register {email, password} → claims orphan default profile if any,
                                     else creates a fresh empty default profile
  /auth/login    {email, password} → token + default (or only) profile
  /auth/me                          → user + all owned profiles
  Every other endpoint:  Authorization: Bearer <jwt>  +  X-Profile-Id: <uuid>
  (dependencies.py: get_current_user reads JWT; get_current_profile reads header,
   validates ownership against the JWT user)

Per-profile data (each named palate has its own dir/files/flights):
  backend/profiles/{profile_id}/profile_data.json   ← palate state
  backend/profiles/{profile_id}/inventory.json      ← cellar
  cellar.db: flights.profile_id scopes history per profile
             users + profiles tables hold accounts and named palates
             response_cache + parse_cache remain global (content-addressed)

Legacy migration (idempotent, runs once at startup):
  backend/profile_data.json + inventory.json + flights(profile_id NULL)
  → backend/profiles/{ORPHAN_PROFILE_ID}/{profile_data,inventory}.json
  → flights.profile_id = ORPHAN_PROFILE_ID
  → orphan row inserted with user_id=NULL; first /auth/register claims it

Profile source (one of, per profile):
  (a) CellarTracker TSV (inventory)       → profiles/{pid}/inventory.json
      CellarTracker TSV (tasting history) → profiles/{pid}/profile_data.json
      → /upload-profile triggers synthesize_palate_from_notes (single Claude call
         on raw notes grouped by score tier) → profile_data.json["_synthesized"]
         (rich palate: multi-word descriptors, taste_markers 1-5, palate_persona,
          style_summary, inference_confidence; falls back to deterministic
          frequency tokens if synthesis fails)
  (b) 3-7 named seed bottles → /seed-profile → Claude (infer) → profile_data.json["_inferred"]
→ optional manual edits via PATCH /profile → profile_data.json["_overrides"]
  (layered on top of synthesized/inferred/derived profile by build_taste_profile;
   short-circuit precedence: _synthesized > _inferred > deterministic;
   cleared whenever /upload-profile or /seed-profile replaces the underlying state)
→ wine list upload (PDF/photo) → parser.py → Claude (enrich profile; skipped if seed-derived or synthesized)
→ Claude (recommend) → top-N recommendations (default 3; configurable via bottle_count)
  (system prompt surfaces taste_markers numerically and quotes palate_persona verbatim;
   per-wine confidence capped at "medium" for seed-derived; color derived server-side post-validation)
→ auto-saved to flights table with profile_id (cellar.db) → retrievable via GET /history scoped to active profile
```
**Modules:** `main.py` (composition root — env, logging, middleware, router includes, legacy migration), `bootstrap.py` (.env + constants — JWT_SECRET, PROFILES_DIR, ORPHAN_PROFILE_ID), `auth.py` (password hashing + JWT utilities; FastAPI-free), `dependencies.py` (get_current_user, get_current_profile FastAPI deps), `logging_setup.py`, `middleware.py` (request log + exception handlers), `rate_limit.py`, `cellar_terms.py` (cellar character helpers), `routes/{auth,profiles,inventory,profile,recommend,debug,history}.py` (HTTP endpoints), `parser.py` (PDF/OCR), `models.py` (Pydantic — incl. User/Profile/TokenResponse), `recommender.py` (LLM), `inventory.py` (cellar; profile_id-keyed), `profile.py` (taste; profile_id-keyed), `seed_profile.py` (seed-bottle onboarding; profile_id-keyed), `prompt.py` (prompt), `scorer.py` (scoring), `cache.py` (SQLite — users/profiles/flights + global response/parse cache + legacy migration helper), `test_fixtures.py` (canned `RecommendationResponse` fixtures for TEST_MODE) — all in `backend/`

## Recommendation Logic
- Full wine list + enriched taste profile in one prompt; reason on **style fit**, not region/varietal
- For CellarTracker uploads the palate is synthesized at upload time by `profile.synthesize_palate_from_notes()` (one Claude call on raw notes); the per-recommendation `build_enriched_profile_text()` short-circuits when a synthesized profile is present, so the recommendation prompt sees rich multi-word descriptors, taste_markers, and a `palate_persona` paragraph
- Per-wine reasoning; list quality assessment; structured JSON output via Pydantic
- Per-wine enrichment fields (coords, grape, bars, wheel, nose, palate, pairs, critic) returned by Claude; `color` (WineColor palette) derived server-side post-validation — never in Claude tool schema
- `source_mode="cellar"` skips wine list entirely; Claude recommends from profile knowledge alone

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
- Fail loudly; schema-driven (Pydantic is the contract); JWT auth (single-tenant learning project, open self-registration); per-profile SQLite + JSON persistence; portfolio-legible

## Authentication & Profiles
- **Auth**: JWT bearer tokens (HS256). Open registration at `POST /auth/register`. Login at `POST /auth/login`. `GET /auth/me` returns the user + their profiles.
- **Profile selection**: every authenticated endpoint (except `/auth/*`, `/profiles/*`, `/debug/health`, `/debug/ping`) requires an `X-Profile-Id` header. The backend validates that the profile is owned by the current user.
- **Storage layout**: `backend/profiles/{profile_id}/profile_data.json` and `backend/profiles/{profile_id}/inventory.json`. SQLite tables `users`, `profiles`, and `flights` (latter scoped via `profile_id` column).
- **Frontend wiring**: `frontend/src/state/authStore.tsx` (`useAuth`) and `frontend/src/state/profileStore.tsx` (`useProfiles`). The SDK auto-injects `Authorization` + `X-Profile-Id` headers via `client/configure.ts` interceptors. `AuthGuard` redirects unauthenticated routes to `/login`; `ProfileSwitcher` in the global header (`AuthenticatedHeader`) toggles the active profile.
- **Required env**: `JWT_SECRET` (fail-loud at bootstrap). Generate with `python -c "import secrets; print(secrets.token_hex(32))"`. Optional: `JWT_ALGORITHM` (default `HS256`), `JWT_EXPIRY_DAYS` (default 7).

## Test Mode
- Set `TEST_MODE=true` in `backend/.env` to enable. While active, `/recommend` accepts an optional `test_fixture` form field; supplying one of `happy | sparse | long_reasoning | low_confidence | two_wines` short-circuits the route to a canned response in `backend/test_fixtures.py` — no Anthropic calls are made. Unknown name → 400. Default is `TEST_MODE=false`; the field is ignored unless the flag is on.

---

## Claude Code Rules

### 1. Context Sources
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
- **Use** Gitbash and do **not** use Powershell.

### 4. Python & Backend
- All Pydantic models: `ConfigDict(alias_generator=to_camel, populate_by_name=True)`.
- `/recommend` and `/upload-inventory` require `FormData` in the frontend.

### 5. Frontend & Styling
- **Imports:** `@/` alias only. No relative `../../` paths. Do not modify `vite.config.ts`.
- **Layout:** `<PaperFrame>` as page wrapper (not VibrantBackground, not GlassCard). No glassmorphism.
- **Typography:** Cormorant Garamond (display) + EB Garamond (body). All font references via inline `fontFamily` strings.
- **Icons:** `lucide-react` only; always `strokeWidth={1.5}`; no inline SVGs.
- **Colour:** Import named tokens from `@/design/tokens` (INK, INK_SOFT, PAPER, OXBLOOD, RULE). No hardcoded hex/rgba; no `text-white`, `text-gray-*`, or `bg-wine-*` Tailwind classes.
- **Style delivery:** Inline `CSSProperties` objects for all component styling. Tailwind utility classes only for stateful helpers (e.g. `animate-spin`, `hidden`).
- **Decoration:** Hairline rules (1px solid RULE), no rounded corners, no drop shadows beyond inset paper.

## Visual debugging workflow
- Dev server runs on localhost:5173
- To check rendering: `npx playwright screenshot http://localhost:5173 /tmp/screen.png`
- Read the screenshot before and after any CSS/layout changes