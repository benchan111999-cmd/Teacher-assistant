# Architecture

> **Audience**: AI coding agents and human contributors.
> This file documents the *system-level* structure of Teacher-Assistant. Update it whenever module responsibilities, data flows, or infrastructure change.

---

## 1. System Overview

Teacher-Assistant is a **modular monolith** — one backend, one frontend — that turns raw teaching materials into a structured preparation pipeline:

```
Materials (PDF/PPTX/DOCX/XLSX)
  └─► documents  →  topics  →  curriculum  →  lessons  →  slides
                                                              └─► HTML Deck
```

All inter-module communication is internal Python function calls (not HTTP). The only external surface is the FastAPI REST layer consumed by the Next.js frontend.

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| Backend language | Python 3.11+ |
| Backend framework | FastAPI |
| ORM | SQLModel (preferred) / SQLAlchemy 2.0+ |
| Database (dev) | SQLite |
| Database (prod) | PostgreSQL |
| Vector store | ChromaDB (local-first) |
| Template engine | Jinja2 (YAML → HTML) |
| Migrations | Alembic |
| Frontend framework | Next.js (React + TypeScript) |
| Styling | Tailwind CSS or CSS Modules |
| Node runtime | Node.js 20+ |
| Package manager | pnpm (preferred) / npm |
| Containerisation | Docker (local dev) |
| LLM (primary) | External API — cheap, long-context model |
| LLM (optional) | Local model via Ollama / llama.cpp |
| Deployment target | GitHub Pages (not yet configured) |

---

## 3. Repository Layout

```
Teacher-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entrypoint (exports main:app)
│   │   ├── core/                # Config, DB session, logging
│   │   └── modules/
│   │       ├── documents/       # File ingestion & parsing
│   │       ├── topics/          # Topic extraction, embeddings, clustering
│   │       ├── curriculum/      # Version diff & outline CRUD
│   │       ├── lessons/         # Lesson plan generation
│   │       └── slides/          # YAML schema, generation & HTML rendering
│   └── tests/                   # pytest-asyncio tests (mirrors modules)
├── frontend/
│   ├── app/ (or src/)
│   ├── features/
│   │   ├── upload/
│   │   ├── topics/
│   │   ├── curriculum/
│   │   ├── lessons/
│   │   └── slides/
│   ├── components/              # Shared UI components
│   └── tests/
├── docs/
│   ├── Architecture.md          # ← this file
│   ├── Design.md                # UI/UX design rules
│   └── prompts.md               # Reusable LLM prompt templates
├── scripts/                     # Dev scripts (verify-local.sh, migrations, etc.)
├── AGENTS.md                    # AI agent rules (source of truth for agents)
└── README.md
```

---

## 4. Domain Model

```
CurriculumVersion
  └─► Material  (file_name, file_type, status)
        └─► Section  (title, body, position)
              └─► Topic  (name, summary, tags[], cluster_id)
                    └─► CurriculumOutline  (ordered items[])
                          └─► LessonPlan  (objectives[], timeline[])
                                └─► LessonSlides  (yaml, html)
```

### Key Entity Reference

| Entity | Key Fields |
|---|---|
| `CurriculumVersion` | id, name, year, notes |
| `Material` | id, curriculum_version_id, file_name, file_type, parsed_at, status |
| `Section` | id, material_id, title, body, position |
| `Topic` | id, curriculum_version_id, name, summary, tags[], source_section_ids[], cluster_id |
| `CurriculumOutline` | id, items[] |
| `LessonPlan` | id, outline_id, title, objectives[], timeline[], topics[] |
| `LessonSlides` | lesson_id, yaml, html |

---

## 5. Module Responsibilities

### `documents` — File Ingestion
- Accepts: PDF, PPTX, DOCX, XLSX uploads.
- Produces: Normalised `Section` records linked to a `Material`.
- **No LLM calls.** Pure parsing only.
- On failure: set `Material.status = failed`, log error, do not crash.

### `topics` — Semantic Extraction
- Calls LLM to produce: topic name, summary, tags.
- Generates embeddings (default: `text-embedding-3-small`).
- Clusters topics via cosine similarity + union-find (explainable first).
- Stores vector ID + metadata in ChromaDB.

### `curriculum` — Version & Outline
- Groups topics by `CurriculumVersion`.
- Computes common vs. unique topics across versions via `curriculum.diff`.
- CRUD for final `CurriculumOutline` via `curriculum.outline`.
- Supports AI-suggested initial outline; always allows manual edit.

### `lessons` — Lesson Plan Generation
- Input: final outline + constraints (n lessons, duration, audience).
- Output: structured `LessonPlan` with objectives, timeline, activities.
- Provides APIs for regenerate / split / merge.

### `slides` — YAML & HTML Output
- YAML must validate against `schema.yaml`.
- HTML rendered from YAML via Jinja2 templates (theme-agnostic).
- **No LLM calls at render time.**

---

## 6. Data Flow (End-to-End)

```
[Teacher] ──upload──► /documents/upload
                          │
                    parse & normalise
                          │
                       Section[]  ──►  /topics/extract
                                           │
                                     LLM + embed
                                           │
                                        Topic[]  ──►  /curriculum/diff
                                                           │
                                                    common/unique view
                                                           │
                                                    [Teacher curates]
                                                           │
                                                 CurriculumOutline  ──►  /lessons/generate
                                                                               │
                                                                         LessonPlan[]  ──►  /slides/generate
                                                                                                  │
                                                                                           YAML  ──►  HTML
```

---

## 7. LLM Usage Rules

1. **Deterministic structure** — all LLM outputs must validate against a schema (YAML/JSON).
2. **Centralised prompts** — store in `docs/prompts.md` or a dedicated `prompts` module.
3. **RAG retrieval** — feed only relevant `Section` chunks, never full documents.
4. **Separation of concerns**:
   - Parsing & HTML rendering → no LLM.
   - Semantics (topics, lesson plans, YAML) → LLM.
5. **Cost control** — default to cheaper models; fall back to local Ollama if needed.

---

## 8. Infrastructure

- **Local dev**: Docker-based; `.env` for secrets.
- **Frontend** defaults to `http://127.0.0.1:8000`; override with `NEXT_PUBLIC_API_URL`.
- **Verification**: `bash scripts/verify-local.sh` before every handoff.
- **Firebase**: used for some features; do not add credentials or schema changes without explicit request.
- **GitHub Pages**: intended deployment target; workflow not yet configured.

---

## 9. Non-Goals (v1)

- Multi-tenant SaaS (accounts, billing).
- Real-time collaborative editing.
- Complex analytics dashboards.
- Heavy slide animation.
- Full JWT/OAuth authentication.
