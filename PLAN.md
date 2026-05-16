# Teacher-assistant Improvement Plan

> **For AI coding agents**: This document is the single source of truth for all planned improvements.
> Work through phases **in order**. Do not start a later phase until all items in the current phase pass their verification gate.
> Each task has a checkbox — mark it done (`[x]`) when complete.
> Run `bash scripts/verify-local.sh` after every phase before moving on.

---

## Phase 0 — Security & Hygiene (Do First, No Exceptions)

> **Gate**: All items below must be complete before ANY new feature work begins.
> These are live security risks on any non-local deployment.

### 0-A  Fix dangerous default config

**File**: `backend/app/core/config.py`

- [ ] Change `DEBUG` default from `True` → `False`
- [ ] Change `CORS_ALLOWED_ORIGINS` default from `"*"` → `""` (empty string forces explicit configuration)
- [ ] Change `LLM_MODEL` default from `"openrouter/free"` → `"openai/gpt-4o-mini"` (stable, well-supported)
- [ ] Update `get_cors_origins()`: if `DEBUG is False` AND origins is empty, raise `RuntimeError("CORS_ALLOWED_ORIGINS must be set in production")` instead of silently returning `[]`

**Verification**: `cd backend && poetry run pytest tests/test_review_fixes.py`

### 0-B  Add missing backend `.env.example`

**File**: `backend/.env.example` (create new)

```
OPENAI_API_KEY=your_openrouter_key_here
DATABASE_URL=sqlite:///./dev.db
CORS_ALLOWED_ORIGINS=http://localhost:3000
DEBUG=false
LLM_MODEL=openai/gpt-4o-mini
MAX_FILE_SIZE=52428800
```

- [ ] Create `backend/.env.example` with content above
- [ ] Verify `.env` is in `.gitignore` (already present — confirm only)

### 0-C  Delete redundant startup scripts

The following files are all duplicates of `poetry run uvicorn app.main:app --reload`.
Delete every one — they cause confusion about the canonical entry point.

- [ ] Delete `backend/debug_server.py`
- [ ] Delete `backend/hypercorn_server.py`
- [ ] Delete `backend/run.bat`
- [ ] Delete `backend/run.py`
- [ ] Delete `backend/run_server.bat`
- [ ] Delete `backend/run_uvicorn.py`
- [ ] Delete `backend/run_with_log.py`
- [ ] Delete `backend/start_server.py`
- [ ] Delete `backend/test_server.bat`

**Canonical start command** (document in README after deletion):
```bash
cd backend && poetry run uvicorn app.main:app --reload
```

### 0-D  Update README with corrected setup steps

**File**: `README.md`

- [ ] Replace the "Local Development" section to reflect the deleted scripts
- [ ] Add note: "GitHub Pages cannot host the FastAPI backend. Production deployment requires a server (Railway, Render, Fly.io, or VPS). See Deployment section."
- [ ] Remove or correct the "GitHub Pages is the intended deployment target" line

---

## Phase 1 — LLM Layer Hardening

> **Gate**: All existing tests must still pass. Add new tests for retry and validation behaviour.

### 1-A  Add LiteLLM and Tenacity

**File**: `backend/pyproject.toml`

- [ ] Add `litellm = "^1.40.0"` to `[tool.poetry.dependencies]`
- [ ] Add `tenacity = "^8.2.0"` to `[tool.poetry.dependencies]`
- [ ] Run `poetry lock && poetry install`

### 1-B  Create `primitives.py` — single source of truth for all data shapes

**File**: `backend/app/core/primitives.py` (create new)

All `service.py` files and all LLM prompt builders must import from here.
Never redefine data shapes inline in service or router files.

```python
from pydantic import BaseModel, Field

class SubtopicPrimitive(BaseModel):
    name: str = Field(..., max_length=80)
    summary: str = Field(..., max_length=300)

class TopicPrimitive(BaseModel):
    name: str = Field(..., max_length=50)
    summary: str = Field(..., max_length=200)
    tags: list[str] = []
    subtopics: list[SubtopicPrimitive] = []

class LessonItem(BaseModel):
    title: str
    objectives: list[str]
    timeline: list[dict]   # [{"time": "0-10min", "activity": "..."}]
    topics: list[str]

class LessonPlanPrimitive(BaseModel):
    title: str
    lessons: list[LessonItem]

class OutlineItem(BaseModel):
    type: str              # "topic" | "header" | "section"
    topic_id: int | None = None
    title: str | None = None
```

- [ ] Create `backend/app/core/primitives.py` with the models above

### 1-C  Rewrite `llm.py` with LiteLLM + retry + schema validation

**File**: `backend/app/core/llm.py` (rewrite)

Key requirements:
- Use `litellm.completion()` instead of `OpenAI(base_url=...)`. Model switching is now just changing `LLM_MODEL` env var.
- Wrap every LLM call with `@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))`
- Strip markdown fences before parsing: `raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()`
- Validate all structured outputs against `primitives.py` models. On `ValidationError`, log the raw output and raise `RuntimeError` — never silently return `[]`

```python
def _parse_json(raw: str) -> Any:
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)
```

- [ ] Rewrite `call_llm()` using LiteLLM with retry decorator
- [ ] Rewrite `call_extract_topics()` → validate against `list[TopicPrimitive]`
- [ ] Rewrite `call_generate_lesson_plan()` → validate against `LessonPlanPrimitive`
- [ ] Rewrite `call_suggest_outline()` → validate against `list[OutlineItem]`
- [ ] Rewrite `call_generate_yaml_slides()` → add retry, no Pydantic needed

### 1-D  Add LLM hardening tests

**File**: `backend/tests/test_llm_hardening.py` (create new)

- [ ] Test: `call_extract_topics` raises `RuntimeError` when LLM returns non-JSON (mock)
- [ ] Test: markdown fence stripping works correctly before JSON parsing
- [ ] Test: retry decorator fires on `APIError` (mock raises twice, succeeds third time)
- [ ] Test: `TopicPrimitive` rejects `name` longer than 50 chars

**Verification**: `cd backend && poetry run pytest tests/test_llm_hardening.py -v`

---

## Phase 2 — Pipeline Stage Gates

> **Inspired by**: `teaching-site-skills` Stage Gate pattern (`teaching-site/SKILL.md`).
> Each pipeline stage must verify prerequisites are met before proceeding.
> Reference: https://github.com/kevintsai1202/teaching-site-skills

### 2-A  Stage Gate in `topics/service.py`

**File**: `backend/app/modules/topics/service.py`

- [ ] At start of `extract_topics_from_sections()`, add:
  ```python
  if not sections or len(sections) < 2:
      raise ValueError(
          "Stage Gate: requires ≥2 sections before topic extraction. "
          "Complete document parsing first."
      )
  ```

### 2-B  Stage Gate in `curriculum/service.py`

**File**: `backend/app/modules/curriculum/service.py`

- [ ] In `suggest_outline()`: replace `return []` on empty topics with:
  ```python
  raise ValueError(
      "Stage Gate: requires ≥5 topics before outline suggestion. "
      "Run topic extraction first."
  )
  ```
- [ ] Refactor `delete_version()` cascade logic into private `_cascade_delete_version()` helper (current function is too long)

### 2-C  Add pipeline readiness endpoint

**File**: `backend/app/modules/curriculum/router.py`

- [ ] Add `GET /curriculum/{version_id}/readiness` returning:
  ```json
  {
    "version_id": 1,
    "stages": {
      "documents": {"ready": true,  "count": 3,  "message": null},
      "topics":    {"ready": true,  "count": 12, "message": null},
      "outline":   {"ready": false, "count": 0,
                    "message": "Run outline suggestion first"},
      "lessons":   {"ready": false, "count": 0,
                    "message": "Outline required before lesson generation"}
    }
  }
  ```
- [ ] Add test in `backend/tests/test_api.py` for the readiness endpoint

---

## Phase 3 — CI/CD & Developer Experience

> **Gate**: Both CI jobs must be green before this phase is marked complete.

### 3-A  Add GitHub Actions CI

**File**: `.github/workflows/ci.yml` (create new)

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Tesseract
        run: sudo apt-get install -y tesseract-ocr
      - uses: abatilo/actions-poetry@v2
      - run: cd backend && poetry install
      - run: cd backend && poetry run pytest --tb=short
        env:
          OPENAI_API_KEY: test-key
          DATABASE_URL: sqlite:///./test.db
          DEBUG: "false"
          CORS_ALLOWED_ORIGINS: "http://localhost:3000"

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      - run: cd frontend && npm ci
      - run: cd frontend && npm run build
        env:
          NEXT_PUBLIC_API_URL: http://localhost:8000
```

- [ ] Create `.github/workflows/ci.yml` with content above
- [ ] Verify both jobs pass on a test branch before merging to main

### 3-B  Add ruff linter

**File**: `backend/pyproject.toml`

- [ ] Add `ruff = "^0.4.0"` to `[tool.poetry.group.dev.dependencies]`
- [ ] Add config block:
  ```toml
  [tool.ruff]
  line-length = 100
  select = ["E", "F", "I"]
  ```
- [ ] Run `poetry run ruff check . --fix` and commit fixes
- [ ] Add to CI: `- run: cd backend && poetry run ruff check .`

---

## Phase 4 — Deployment Readiness

### 4-A  Add Dockerfile + docker-compose

**File**: `backend/Dockerfile` (create new)

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y tesseract-ocr && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-dev
COPY app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**File**: `docker-compose.yml` (create at repo root)

```yaml
version: '3.9'
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: ./backend/.env
    volumes:
      - ./backend/dev.db:/app/dev.db
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on: [backend]
```

- [ ] Create `backend/Dockerfile`
- [ ] Create `docker-compose.yml` at repo root
- [ ] Test: `docker compose up --build` starts both services, `GET /health` returns 200

### 4-B  Add minimal API authentication

**File**: `backend/app/core/auth.py` (create new)

```python
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import get_settings

security = HTTPBearer(auto_error=False)

def require_api_key(
    credentials: HTTPAuthorizationCredentials | None = Security(security)
) -> None:
    settings = get_settings()
    if not settings.API_KEY:   # not set → dev mode, allow all
        return
    if credentials is None or credentials.credentials != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
```

- [ ] Add `API_KEY: Optional[str] = None` to `Settings` in `config.py`
- [ ] Add `API_KEY=` line to `backend/.env.example`
- [ ] Create `backend/app/core/auth.py`
- [ ] Add `Depends(require_api_key)` to all routers: documents, topics, curriculum, lessons, slides
- [ ] Test: unauthenticated request returns 401 when `API_KEY` is set

---

## Phase 5 — RAG Enhancement (Optional, High Value)

> Only begin after Phases 0–3 are complete and CI is green.

### 5-A  Wire up ChromaDB (config placeholder already exists)

`CHROMA_PERSIST_DIRECTORY` is defined in `config.py` but never used. This phase activates it.

- [ ] Add `chromadb = "^0.5.0"` to `pyproject.toml` dependencies
- [ ] Create `backend/app/core/vectorstore.py`:
  - `get_chroma_client()` → persistent `chromadb.Client`
  - `upsert_sections(material_id, sections)` → embeds and stores section bodies
  - `search_similar(query, n_results=5)` → returns top-N relevant sections
- [ ] In `topics/service.py`: use `search_similar()` to retrieve relevant sections before LLM call (reduces tokens, improves focus)
- [ ] Add `EMBEDDING_MODEL: str = "text-embedding-3-small"` to `Settings`

### 5-B  Fix silent section truncation

**File**: `backend/app/core/llm.py`

Currently `extract_topics_from_sections_prompt()` silently truncates section body to 500 chars.

- [ ] Log `WARNING` when truncation occurs: `logger.warning(f"Section '{title}' truncated from {len(body)} to 500 chars")`
- [ ] Add `LLM_SECTION_BODY_LIMIT: int = 500` to `Settings` (make configurable)

---

## Verification Gates Summary

| After Phase | Command | Must pass |
|---|---|---|
| 0 | `bash scripts/verify-local.sh` | All tests green, build succeeds |
| 1 | `cd backend && poetry run pytest -v` | All tests + new LLM tests green |
| 2 | `cd backend && poetry run pytest -v` | Stage gate tests green |
| 3 | Push to GitHub → Actions tab | Both CI jobs green |
| 4 | `docker compose up --build` | Both services start, `/health` → 200 |
| 5 | Upload PDF → `GET /topics/` | Topics extracted via RAG path |

---

## Required Environment Variables (Complete Reference)

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | ✅ Yes | — | OpenRouter API key |
| `LLM_MODEL` | No | `openai/gpt-4o-mini` | LiteLLM model string |
| `DATABASE_URL` | No | `sqlite:///./dev.db` | SQLAlchemy URL |
| `CORS_ALLOWED_ORIGINS` | ✅ In prod | — | Comma-separated origins |
| `DEBUG` | No | `false` | Never `true` in production |
| `MAX_FILE_SIZE` | No | `52428800` | Bytes (default 50 MB) |
| `API_KEY` | No | — | Bearer token (set in production) |
| `CHROMA_PERSIST_DIRECTORY` | No | `./chroma_db` | Vector DB path (Phase 5) |
| `LLM_SECTION_BODY_LIMIT` | No | `500` | Prompt truncation limit (Phase 5) |
| `NEXT_PUBLIC_API_URL` | Frontend | `http://127.0.0.1:8000` | Backend URL for frontend |

---

## Integration Path with teaching-site-skills

Once Phases 1–2 are complete, Teacher-assistant output can feed directly into
[`kevintsai1202/teaching-site-skills`](https://github.com/kevintsai1202/teaching-site-skills)
to generate interactive teaching websites from parsed documents.

**The bridge**: export curriculum outline as `course-data.js`-compatible JSON,
then hand off to the `static-spa-conversion` skill.

- [ ] (Future) Add `GET /curriculum/{version_id}/export/course-data-js` that serialises
  the outline + lessons into `window.COURSE = { ... }` format compatible with
  teaching-site-skills' `_shared/domain-primitives.md` schema
- [ ] (Future) Document the handoff procedure in `README.md`

---

## What NOT to Do

- ❌ Do not add new features before Phase 0 is complete
- ❌ Do not skip Phase 0-C (redundant scripts confuse future agents and developers)
- ❌ Do not deploy to GitHub Pages (static hosting cannot run FastAPI)
- ❌ Do not set `DEBUG=true` in any `.env` committed to the repo
- ❌ Do not merge a PR if CI is red (after Phase 3 is set up)
- ❌ Do not call LLM functions without the retry decorator (Phase 1 adds this)
- ❌ Do not redefine data shapes outside `primitives.py` (create it in Phase 1-B first)
