# Teacher-Assistant

Teacher-Assistant turns teaching sources and materials into a structured preparation pipeline:

1. ingest source materials
2. extract and cluster topics
3. curate curriculum outlines
4. generate lesson plans
5. produce course notes and slide drafts

## Project Layout

- `backend/` - FastAPI backend for parsing, topic extraction, curriculum, lessons, and slides.
- `frontend/` - Next.js frontend for upload, topic review, curriculum editing, lessons, and slide views.
- `AGENTS.md` - stable project rules for AI coding agents.

## Local Development

Backend:

```bash
cd backend
poetry run uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm run dev
```

## Work Mode

This repo follows the Codex #07 project work mode.

- Start a session with `開工` to run `startup-sync`.
- End a session with `收工` to run `shutdown-sync`.
- Use `新專案初始化` only to inspect and fill missing setup items.
- Progress and next steps live in the Obsidian dashboard: `Teacher-Assistant/專案工作流程.md`.

## Deployment

The GitHub repo is public and GitHub Pages is the intended deployment target. A Pages build/deploy workflow has not been configured yet.

## Safety

Do not commit API keys, tokens, passwords, private credentials, `.env*`, `.codex/`, or student names. Use class codes and seat numbers for formal student data.
