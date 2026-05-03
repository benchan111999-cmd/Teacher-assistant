# AGENTS.md

 Primary audience AI coding agents (OpenAI, Claude, etc.) working on this repo.
 本檔案主要給 AI 協助開發本專案時參考，用「單一總控檔 + 模組化程式結構」的方式設計。

---

## 0. #07 project work mode

This repo uses the Codex #07 classroom-tool work mode.

- Project name: `Teacher-Assistant`
- Purpose: Turn sources/materials -> topic extraction -> curriculum -> lesson plans -> course notes.
- Primary working tree: `/home/dicatobear/projects/Teacher-assistant`
- GitHub repo: `https://github.com/benchan111999-cmd/Teacher-assistant`
- Default branch: `main`
- Obsidian vault: `/mnt/c/Users/User/iCloudDrive/iCloud~md~obsidian/2ndBrain`
- Obsidian dashboard: `Teacher-Assistant/專案工作流程.md`
- Firebase: used, but do not add credentials or schema changes unless explicitly requested.
- Deployment target: GitHub Pages; deployment workflow is not configured yet.

Open work:

- Use `startup-sync`.
- Read this file and the Obsidian dashboard.
- Check git status.
- Do not automatically pull, commit, or push.

Close work:

- Use `shutdown-sync`.
- Update the Obsidian dashboard with progress and next steps.
- Update this file only when stable rules, paths, or project boundaries changed.
- Commit or push only after explicit approval, and stage only relevant files.

Project initialization:

- Use `project-init-sync`.
- For this existing repo, inspect first and fill only missing pieces. Do not overwrite existing app code, Firebase settings, or Git history.

Safety:

- Do not commit `.codex/`, `.opencode/`, `.env*`, API keys, tokens, passwords, or private credentials.
- Do not store student names; formal student data should use class codes and seat numbers.

## 1. Project overview

This repository implements a teaching preparation assistant with the following pipeline

1. Ingest multi-version teaching materials (PDF, PPTX, DOCX, XLSX).
2. Parse and normalize them into structured sections.
3. Extract and cluster topics across versions to find
   - Common topics across versions.
   - Unique topics per version.
4. Let the teacher curate a final curriculum outline.
5. Generate lesson plans (objectives, timing, activities, references).
6. Generate YAML slide drafts for each lesson.
7. Render HTML slide decks from the YAML.

The app is a modular monolith one backend and one frontend, but clearly separated into domain modules.

---

## 2. Tech stack (target  preference)

You MAY refactor as needed, but default to this stack unless explicitly instructed otherwise

- Backend
  - Language: Python 3.11+
  - Framework: FastAPI
  - ORM: SQLModel (preferred for Pydantic integration) or SQLAlchemy 2.0+
  - Database: PostgreSQL (production)  SQLite (dev)
  - Vector store: ChromaDB (default for local dev, easier to embed)
  - Templates: Jinja2 (for YAML → HTML)
  - Migrations: Alembic
- Frontend
  - Framework: Next.js (React, TypeScript)
  - Styling: Tailwind CSS or simple CSS Modules
  - Node Version: 20+
- Infra
  - Local-first, Docker-based dev environment
  - Later optional deployment to a PaaS (not required for initial development)
- LLM usage
  - Primary: External LLM API (cheap, long-context model) for
    - Topic extraction
    - Curriculum summarization
    - Lesson plan + YAML generation
  - Optional: local LLMs for privacy and cost optimization
  - Security: Store API keys in .env file. Never hardcode keys

If you propose changing the stack, FIRST explain the trade-offs in a short comment, then apply changes.

---

## 3. Repository layout (target structure)

Keep the repo organized as a modular monolith. Each module is a directory with its own internal structure.

Backend

- `backend/`
  - `app/main.py` – FastAPI entrypoint (Ensure main:app is exported)
  - `app/core/` – config, DB session, logging
  - `app/modules/`
    - `documents/`
      - Uploading & parsing PDF/PPTX/DOCX/XLSX into `Section` records
    - `topics/`
      - Topic extraction (LLM), embeddings, clustering, vector search
    - `curriculum/`
      - Curriculum versions, diff (common vs unique topics), final outline
    - `lessons/`
      - Lesson plan generation & editing
    - `slides/`
      - YAML slide schema, YAML generation, YAML → HTML rendering
  - `tests/` – backend tests (mirrors modules, use pytest-asyncio)

Frontend

- `frontend/`
  - `app/` or `src/` – Next.js application
  - `features/`
    - `upload/` – file upload & status UI
    - `topics/` – topic viewer & search
    - `curriculum/` – diff view & outline editor
    - `lessons/` – lesson plan list & editor
    - `slides/` – YAML/HTML preview & export
  - `components/` – shared UI components
  - `tests/` – frontend tests

Shared

- `docs/`
  - `architecture.md` – deeper system architecture details
  - `prompts.md` – prompt patterns for LLM tasks
- `.claudeskills` – task-specific playbooks for Claude (optional)
- `scripts` – utility scripts (migrations, dev setup, data import)

If you add new modules, keep this structure consistent and update this file and `docs/architecture.md`.

---

## 4. Domain model (key entities)

You MUST respect and reuse these entities across modules

- `CurriculumVersion`
  - `id`, `name`, `year`, `notes`
- `Material`
  - `id`, `curriculum_version_id`, `file_name`, `file_type`, `parsed_at`, `status` (e.g., pending, parsed, failed)
- `Section`
  - `id`, `material_id`, `title`, `body`, `position`
- `Topic`
  - `id`, `curriculum_version_id`, `name`, `summary`, `tags[]`, `source_section_ids[]` (JSON or assoc table), `cluster_id`
- `CurriculumOutline`
  - `id`, `items[]` (each item is a topic, group header, or section marker)
- `LessonPlan`
  - `id`, `outline_id`, `title`, `objectives[]`, `timeline[]`, `topics[]`
- `LessonSlides`
  - `lesson_id`, `yaml`, `html`

When adding fields, keep names descriptive. Ensure id fields use UUID or Auto-increment integers consistently.

---

## 5. Responsibilities of each backend module

### `documents` module

Purpose

- Handle all file ingestion and parsing.
- Convert PDFs, PPTX, DOCX, XLSX into normalized `Section` objects.

Rules

- Do NOT call LLMs directly here.
- Each parser should be a small, testable function
  - `parse_pdf(...)`
  - `parse_pptx(...)`
  - `parse_docx(...)`
  - `parse_xlsx(...)`
- Always associate parsed `Section` with the originating `Material`.
- Error Handling: If parsing fails, update Material.status to failed and log the error. Do not crash the pipeline.

### `topics` module

Purpose

- Derive semantic topics from sections.
- Manage embeddings, clustering, and topic-level search.

Rules

- LLM calls for:
  - Topic name
  - Short summary
  - Tags
- Embeddings
  - Use a single embedding model for consistency (e.g., text-embedding-3-small).
  - Store vector id + metadata so topics can be retrieved for later generation.
- Clustering
  - Implement a simple, explainable approach first (e.g., cosine similarity threshold + union-find).

### `curriculum` module

Purpose

- Provide a curriculum-centric view
  - Group topics by version.
  - Compute common vs unique topics.
  - Maintain a curated final outline.

Rules

- `curriculum.diff`
  - Uses topic clusters from `topics` to find shared/unique content.
- `curriculum.outline`
  - Provides CRUD for the final outline.
  - Supports AI-suggested initial outline, but always allows manual editing.

### `lessons` module

Purpose

- Turn the final curriculum outline into lesson plans.

Rules

- `generate_lesson_plan_batch`
  - Inputs outline, constraints (number of lessons, duration, target audience).
  - Output structured lesson plans with objectives, timeline, activities.
- Provide APIs for
  - Regenerating a lesson with new constraints.
  - Splitting/merging lessons.

### `slides` module

Purpose

- Generate structured YAML slide drafts and final HTML slides.

Rules

- YAML
  - Must follow a strict schema (define it in `schema.yaml`).
  - All slide generation is based on a `LessonPlan`.
- HTML
  - Rendered from YAML via templates (Jinja2 or similar).
  - Keep templates theme-agnostic so they can be swapped later.

---

## 6. LLM usage guidelines

When you (the agent) call or design code that calls LLMs

1. Prefer deterministic structure over fancy prose.
   - YAML/JSON outputs must validate against a schema.
2. Keep prompts in shared locations.
   - Store reusable prompt templates under `docs/prompts.md` or a dedicated `prompts` module.
3. Minimize context cost.
   - Use RAG-style retrieval to feed only relevant sections, not entire documents.
4. Separation of concerns.
   - Parsing & storage: no LLM.
   - Semantics (topics, clustering, lesson plans, YAML): LLM.
   - Rendering (HTML): no LLM.
5. Cost Control.
   - Default to cheaper models for generation tasks.

---

## 7. Coding conventions

- Backend (Python)
  - Use type hints everywhere.
  - Follow PEP8.
  - One module = one clear responsibility.
  - Use pytest-asyncio for testing.
- Frontend (TypeScript/React)
  - Prefer functional components and hooks.
  - Co-locate component, styles, and tests in feature folders.
  - Use explicit types, avoid `any`.
- General
  - Small, focused functions.
  - No “god” modules; keep cross-module logic in the appropriate domain module.
  - Update tests and this AGENTS.md when you change module responsibilities.

---

## 8. Development & testing

### Local dev

- Backend
  - `cd backend`
  - `poetry run uvicorn app/main.py --reload` (or equivalent)
- Frontend
  - `cd frontend`
  - `pnpm dev` (or `npm run dev`)

### Tests

- Backend
  - `pytest` (Ensure pytest-asyncio is configured)
- Frontend
  - `pnpm test` or `npm test`

When you add new behavior, add or update tests in the corresponding `tests` folder.

---

## 9. How to approach new tasks (for agents)

When receiving a request, follow this workflow

1. Identify the module.
   - Parsing  file formats → `documents`
   - Topic/embedding logic → `topics`
   - Version diff & outline → `curriculum`
   - Lesson planning → `lessons`
   - YAML/HTML slides → `slides`
   - Cross-cutting (infra, auth) → `core` or `shared`
2. Check existing code and tests in that module before creating new files.
3. Maintain data flow.
   - Do not introduce shortcuts that bypass domain entities.
4. Document changes.
   - If you change behavior or add a new module, update
     - This `AGENTS.md` (scope & mapping)
     - `docs/architecture.md` (detailed flow)

Keep changes small, incremental, and fully wired from backend to frontend where reasonable.

---

## 10. Non-goals (for now)

To keep scope under control, you SHOULD NOT implement these unless explicitly requested

- Multi-tenant SaaS features (accounts, billing, etc.).
- Real-time collaborative editing.
- Complex analytics dashboards.
- Heavy custom slide animation beyond basic HTML/JS capabilities.
- Authentication: Basic local dev auth is fine; complex JWT/OAuth is not required for v1.

Focus first on a robust pipeline from materials → topics → outline → lesson plans → YAML → HTML.