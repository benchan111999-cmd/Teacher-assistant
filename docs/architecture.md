# Teacher-Assistant Architecture

This document records the current application shape and the target boundaries from `AGENTS.md`. It should be updated when module responsibilities, data flow, or API contracts change.

## Current Status

Teacher-Assistant is a prototype modular monolith. The backend exposes the core domain modules through FastAPI routers, and the frontend provides Next.js pages for each main workflow area.

The app is not yet a fully functioning end-to-end teaching assistant. The current implementation supports basic CRUD-like flows and service stubs, while several target capabilities remain incomplete:

- Document parsing can create `Section` records, but parser quality varies by file type and scanned PDFs may require OCR dependencies.
- Topic extraction, outline suggestion, lesson generation, and slide YAML generation depend on LLM helper functions with fallback behavior.
- Topic clustering is represented through `cluster_id`, but embeddings and automatic clustering are not yet implemented.
- Slide HTML rendering is currently a minimal YAML-in-HTML wrapper, not a themeable Jinja2 renderer.
- Persistent storage uses SQLModel tables through the configured database engine; migrations are not yet present.

## Backend Layout

Backend entrypoint:

- `backend/app/main.py`
  - Creates the FastAPI app.
  - Creates SQLModel tables on startup.
  - Adds request size limiting and optional CORS.
  - Includes domain routers.

Core:

- `backend/app/core/config.py`
  - Owns settings, database engine/session setup, allowed file types, CORS origins, and max upload size.
- `backend/app/core/models.py`
  - Defines the SQLModel entities listed in `AGENTS.md`.
- `backend/app/core/llm.py`
  - Owns external LLM calls for semantic generation tasks.
- `backend/app/core/json_utils.py`
  - Serializes and deserializes list/dict fields stored as JSON strings.

Domain modules:

- `documents`
  - Uploads materials.
  - Validates allowed file types.
  - Parses PDF, PPTX, DOCX, and XLSX files into `Section` records.
  - Does not call LLMs.
- `topics`
  - Creates topics manually.
  - Extracts topics from sections through the LLM helper.
  - Groups topics by `cluster_id`.
- `curriculum`
  - Creates curriculum versions.
  - Creates and updates curriculum outlines.
  - Computes version diffs using `cluster_id` or topic name fallback.
  - Suggests outlines through the LLM helper.
- `lessons`
  - Creates and updates lesson plans.
  - Generates lesson plans from an outline through the LLM helper.
- `slides`
  - Generates YAML slide drafts through the LLM helper.
  - Stores YAML on a lesson.
  - Renders minimal HTML from stored YAML.

## Domain Model

The current backend uses integer primary keys for all entities:

- `CurriculumVersion`
  - `id`, `name`, `year`, `notes`, `created_at`
- `Material`
  - `id`, `curriculum_version_id`, `file_name`, `file_type`, `parsed_at`, `status`
- `Section`
  - `id`, `material_id`, `title`, `body`, `position`
- `Topic`
  - `id`, `curriculum_version_id`, `name`, `summary`, `tags`, `source_section_ids`, `cluster_id`
- `CurriculumOutline`
  - `id`, `curriculum_version_id`, `items`
- `LessonPlan`
  - `id`, `outline_id`, `title`, `objectives`, `timeline`, `topics`
- `LessonSlides`
  - `id`, `lesson_id`, `yaml`, `html`

Several structured fields are currently stored as JSON strings rather than normalized tables:

- `Topic.tags`
- `Topic.source_section_ids`
- `CurriculumOutline.items`
- `LessonPlan.objectives`
- `LessonPlan.timeline`
- `LessonPlan.topics`

This is acceptable for the prototype, but any query-heavy behavior should revisit the schema before expanding features.

## Target Data Flow

The intended data flow remains:

1. Create a `CurriculumVersion`.
2. Upload one or more `Material` files for that version.
3. Parse materials into ordered `Section` records.
4. Extract `Topic` records from selected sections.
5. Cluster topics across versions.
6. Compare curriculum versions through topic clusters.
7. Curate a `CurriculumOutline`.
8. Generate or manually create `LessonPlan` records.
9. Generate YAML drafts as `LessonSlides`.
10. Render YAML into HTML slides.

Current runnable path:

1. Create a curriculum version.
2. Upload/parse a supported file or create records through service/API calls.
3. Create topics manually or call LLM-backed extraction.
4. Create an outline.
5. Create a lesson manually or call LLM-backed generation.
6. Set YAML manually or call LLM-backed YAML generation.
7. Render minimal HTML.

## API Surface

Current backend routers:

- `GET /health`
- `GET /`
- `POST /curriculum/version`
- `GET /curriculum/version/list`
- `GET /curriculum/version/{version_id}`
- `POST /curriculum/outline`
- `GET /curriculum/outline/{outline_id}`
- `GET /curriculum/outline/list/{curriculum_version_id}`
- `PUT /curriculum/outline/{outline_id}`
- `GET /curriculum/diff/{version_a_id}/{version_b_id}`
- `POST /curriculum/outline/suggest/{curriculum_version_id}`
- `POST /documents/{curriculum_version_id}/upload`
- `GET /documents/{material_id}`
- `GET /documents/{material_id}/sections`
- `GET /documents/list/{curriculum_version_id}`
- `DELETE /documents/{material_id}`
- `POST /topics/extract`
- `POST /topics/create`
- `GET /topics/list/{curriculum_version_id}`
- `GET /topics/clusters/{curriculum_version_id}`
- `POST /lessons/generate`
- `POST /lessons/create`
- `GET /lessons/{lesson_id}`
- `GET /lessons/list/{outline_id}`
- `PUT /lessons/{lesson_id}`
- `POST /slides/generate/{lesson_id}`
- `PUT /slides/yaml/{lesson_id}`
- `POST /slides/render/{lesson_id}`
- `GET /slides/{lesson_id}`

## LLM Boundaries

LLM usage must stay out of the `documents` module. Parsing and storage should remain deterministic.

Allowed LLM-backed operations:

- Extract topics from sections.
- Suggest curriculum outlines from topics.
- Generate lesson plans from outlines and constraints.
- Generate YAML slide drafts from lesson plans.

All reusable prompt patterns belong in `docs/prompts.md` or in a dedicated prompt module if the app later needs runtime prompt loading.

## Frontend Layout

The frontend is a Next.js app under `frontend/src`.

Current pages:

- `frontend/src/app/page.tsx`
- `frontend/src/app/upload/page.tsx`
- `frontend/src/app/topics/page.tsx`
- `frontend/src/app/curriculum/page.tsx`
- `frontend/src/app/lessons/page.tsx`
- `frontend/src/app/slides/page.tsx`

Shared frontend code:

- `frontend/src/components/Layout.tsx`
- `frontend/src/components/ui.tsx`
- `frontend/src/lib/api.ts`
- `frontend/src/lib/apiClient.ts`
- `frontend/src/types/api.ts`

The frontend should remain aligned with backend API contracts. If an endpoint response changes, update `frontend/src/types/api.ts` and the consuming page in the same change.

## Verification Expectations

Before changing behavior:

- Run backend tests from `backend/`.
- Run frontend build or tests from `frontend/` when frontend code changes.
- Add or update tests for new behavior in the matching module.

Useful commands:

```bash
cd backend
poetry run pytest
```

```bash
cd frontend
npm run build
```

## Near-Term Priorities

1. Verify the current minimal pipeline end to end with tests.
2. Add focused regression tests for any broken endpoint or service behavior.
3. Replace placeholder slide rendering with schema-validated YAML and a real template renderer.
4. Add explainable topic clustering before building curriculum diff features further.
5. Introduce migrations before production-like database use.

