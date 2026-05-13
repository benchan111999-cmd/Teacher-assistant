# Design

> **Audience**: AI coding agents and frontend contributors.
> This file governs the *visual and interaction design* of the Teacher-Assistant frontend. Update it when colour tokens, typography, component patterns, or UX flows change.

---

## 1. Design Principles

1. **Teacher-first clarity** — the UI must be scannable and actionable for busy educators.
2. **Pipeline visibility** — always show where the user is in the 5-step pipeline.
3. **Progressive disclosure** — show the minimum needed; reveal detail on demand.
4. **Local-first confidence** — surface statuses (parsing, LLM processing) so teachers know what's happening.

---

## 2. Colour Tokens

Use CSS custom properties (or Tailwind config) so themes can be swapped.

```css
:root {
  /* Brand */
  --color-primary:       #3B82F6;  /* blue-500  — action buttons, links */
  --color-primary-dark:  #1D4ED8;  /* blue-700  — hover */
  --color-accent:        #10B981;  /* emerald-500 — success, complete steps */

  /* Neutrals */
  --color-bg:            #F9FAFB;  /* gray-50  — page background */
  --color-surface:       #FFFFFF;  /* white    — cards, panels */
  --color-border:        #E5E7EB;  /* gray-200 — dividers */
  --color-text-primary:  #111827;  /* gray-900 — headings */
  --color-text-secondary:#6B7280;  /* gray-500 — subtitles, captions */

  /* Status */
  --color-warning:       #F59E0B;  /* amber-500 */
  --color-error:         #EF4444;  /* red-500 */
  --color-info:          #6366F1;  /* indigo-500 */
}
```

---

## 3. Typography

| Token | Font | Size | Weight | Usage |
|---|---|---|---|---|
| `--text-h1` | system-ui / Inter | 1.875rem (30px) | 700 | Page titles |
| `--text-h2` | system-ui / Inter | 1.5rem (24px) | 600 | Section headers |
| `--text-h3` | system-ui / Inter | 1.25rem (20px) | 600 | Card/panel titles |
| `--text-body` | system-ui / Inter | 1rem (16px) | 400 | Body text |
| `--text-small` | system-ui / Inter | 0.875rem (14px) | 400 | Labels, captions |
| `--text-mono` | JetBrains Mono / monospace | 0.875rem (14px) | 400 | Code, YAML, prompts |

---

## 4. Spacing & Layout

- Base unit: **4px** (Tailwind default scale).
- Page max-width: **1280px** (Tailwind `max-w-7xl`).
- Content padding: `px-6 py-8` on mobile; `px-10 py-10` on desktop.
- Card padding: `p-6`.
- Section gap: `gap-6` (24px).
- Use a **12-column grid** for complex views (curriculum diff, lesson editor).

---

## 5. Component Library

All shared components live in `frontend/components/`. Prefer composition over inheritance.

### 5.1 PipelineSteps

A horizontal stepper always visible at the top of the app.

```
[ 1. Upload ] → [ 2. Topics ] → [ 3. Curriculum ] → [ 4. Lessons ] → [ 5. Slides ]
```

- Active step: `--color-primary` underline + bold label.
- Completed step: `--color-accent` check icon.
- Future step: `--color-text-secondary`.
- Clicking a completed step navigates to it; future steps are disabled.

### 5.2 StatusBadge

Used for `Material.status` and async job states.

| Status | Colour | Icon |
|---|---|---|
| `pending` | gray | clock |
| `processing` | indigo | spinner |
| `parsed` / `done` | emerald | check |
| `failed` | red | ✕ |

### 5.3 TopicCard

- Shows: topic name (bold), 1-line summary, tag chips, cluster badge.
- Hover: light blue border (`--color-primary` at 30% opacity).
- Selected: solid primary border + light primary fill.

### 5.4 CurriculumDiffPanel

- Two-column layout: left = version A topics, right = version B topics.
- Shared topics: highlighted with `--color-accent` background.
- Unique topics: neutral card background.
- User can drag topics to the `CurriculumOutline` drop zone below.

### 5.5 LessonPlanCard

- Header: lesson number + title.
- Body: objectives list, timeline table (time | activity | notes).
- Footer: "Regenerate" button (primary, outlined) + "Edit" icon.

### 5.6 SlidePreview

- Left panel: YAML code editor (monospace, syntax highlighted).
- Right panel: rendered HTML iframe (live preview on YAML change).
- Export button: downloads HTML file.

### 5.7 UploadDropzone

- Accepts: `.pdf`, `.pptx`, `.docx`, `.xlsx`.
- Shows file name, size, and `StatusBadge` after upload.
- Error state: red border + error message below.

---

## 6. Page / Route Map

| Route | Feature Folder | Purpose |
|---|---|---|
| `/` | — | Landing / pipeline overview |
| `/upload` | `features/upload/` | Upload & manage source materials |
| `/topics` | `features/topics/` | Browse, search, edit topics |
| `/curriculum` | `features/curriculum/` | Version diff + outline editor |
| `/lessons` | `features/lessons/` | Lesson plan list & editor |
| `/slides` | `features/slides/` | YAML editor + HTML preview & export |

---

## 7. Interaction & UX Rules

1. **Async feedback** — every LLM-triggered action must show a loading state (`StatusBadge: processing` or a spinner) within 300 ms.
2. **Optimistic UI** — for quick edits (rename topic, reorder outline item), update UI immediately and sync to backend in background.
3. **Error recovery** — if a backend call fails, show a toast with a "Retry" action. Never silently swallow errors.
4. **Keyboard nav** — all interactive elements must be focusable and operable by keyboard.
5. **Empty states** — each page must have a helpful empty state with a clear call-to-action (e.g., "Upload your first material to get started").

---

## 8. Slide HTML Theme

Jinja2 templates in `backend/app/modules/slides/` must:

- Be **theme-agnostic** — no hardcoded brand colours in the template.
- Inject colour tokens via a `<style>` block generated from the slide YAML's optional `theme` field.
- Default theme uses `--color-primary` and `--color-bg` from the design tokens above.
- Font: load system-ui stack; no external font CDN dependency for offline use.

---

## 9. Accessibility (A11y)

- Minimum contrast ratio: **4.5:1** for normal text, **3:1** for large text.
- All images / icons must have meaningful `alt` text or `aria-label`.
- Use semantic HTML (`<nav>`, `<main>`, `<article>`, `<section>`).
- Avoid colour as the sole indicator of status — always pair with an icon or text label.
