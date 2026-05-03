# Teacher-Assistant Prompt Patterns

This document records prompt contracts for LLM-backed tasks. Prompts should favor structured, deterministic output over polished prose.

The current code calls LLM helper functions from `backend/app/core/llm.py`. Keep these prompt patterns aligned with those helpers if prompt text is moved into code or loaded at runtime.

## General Rules

- Return JSON or YAML that can be validated.
- Do not invent source material beyond the provided sections, topics, or outline items.
- Prefer short names, concise summaries, and explicit arrays.
- Preserve teaching constraints such as lesson count, duration, and target audience.
- Keep reusable prompts here or in a dedicated prompt module.
- Do not include API keys, student names, or private identifiers in prompts.

## Topic Extraction

Purpose:

- Convert parsed `Section` records into candidate `Topic` records.

Input shape:

```json
{
  "sections": [
    {
      "title": "Section title",
      "body": "Section text"
    }
  ]
}
```

Expected output shape:

```json
[
  {
    "name": "Short topic name",
    "summary": "One or two sentence summary grounded in the section text.",
    "tags": ["tag-one", "tag-two"],
    "subtopics": [
      {
        "name": "Focused subtopic name",
        "summary": "One sentence summary grounded in the section text."
      }
    ]
  }
]
```

Prompt pattern:

```text
You are helping a teacher prepare curriculum materials.

Extract teaching topics from the provided sections.

Rules:
- Use only the provided section content.
- Merge duplicate or near-duplicate ideas.
- Keep topic names short and suitable for a curriculum outline.
- Include subtopics for smaller teaching points under each main topic when the source text supports them.
- Write concise summaries.
- Return valid JSON only.

Sections:
{sections_json}

Return JSON in this exact shape:
[
  {
    "name": "Short topic name",
    "summary": "Grounded summary.",
    "tags": ["tag"],
    "subtopics": [
      {
        "name": "Focused subtopic name",
        "summary": "Grounded summary."
      }
    ]
  }
]
```

## Curriculum Outline Suggestion

Purpose:

- Turn existing topics into an initial editable curriculum outline.

Input shape:

```json
{
  "topics": [
    {
      "name": "Topic name",
      "summary": "Topic summary"
    }
  ]
}
```

Expected output shape:

```json
[
  {
    "type": "section",
    "title": "Unit title"
  },
  {
    "type": "topic",
    "title": "Topic title",
    "topic_name": "Existing topic name"
  }
]
```

Prompt pattern:

```text
You are helping a teacher draft an editable curriculum outline.

Create a logical outline from the provided topics.

Rules:
- Use only the provided topics.
- Group related topics under clear section headings.
- Keep the outline editable and concise.
- Return valid JSON only.

Topics:
{topics_json}

Return JSON in this exact shape:
[
  {
    "type": "section",
    "title": "Unit title"
  },
  {
    "type": "topic",
    "title": "Topic title",
    "topic_name": "Existing topic name"
  }
]
```

## Lesson Plan Generation

Purpose:

- Generate lesson plans from a curated outline and teaching constraints.

Input shape:

```json
{
  "outline_items": [
    {
      "type": "topic",
      "title": "Topic title"
    }
  ],
  "num_lessons": 1,
  "duration_minutes": 45,
  "target_audience": "general"
}
```

Expected output shape:

```json
{
  "lessons": [
    {
      "title": "Lesson title",
      "objectives": ["Objective"],
      "timeline": [
        {
          "time": "10 min",
          "activity": "Activity description"
        }
      ],
      "topics": ["Topic title"]
    }
  ]
}
```

Prompt pattern:

```text
You are helping a teacher create practical lesson plans.

Generate lesson plans from the provided outline and constraints.

Rules:
- Use only the provided outline items.
- Create exactly {num_lessons} lesson plans.
- Each lesson should fit within {duration_minutes} minutes.
- Match the target audience: {target_audience}.
- Use measurable objectives.
- Return valid JSON only.

Outline:
{outline_items_json}

Return JSON in this exact shape:
{
  "lessons": [
    {
      "title": "Lesson title",
      "objectives": ["Objective"],
      "timeline": [
        {
          "time": "10 min",
          "activity": "Activity description"
        }
      ],
      "topics": ["Topic title"]
    }
  ]
}
```

## YAML Slide Draft Generation

Purpose:

- Generate structured YAML slide drafts from a `LessonPlan`.

Input shape:

```json
{
  "lesson_title": "Lesson title",
  "objectives": ["Objective"],
  "topics": ["Topic"]
}
```

Expected YAML shape:

```yaml
lesson_title: "Lesson title"
slides:
  - title: "Slide title"
    type: "content"
    bullets:
      - "Key point"
```

Prompt pattern:

```text
You are helping a teacher draft lesson slides.

Create a concise YAML slide draft for the lesson.

Rules:
- Use only the provided lesson title, objectives, and topics.
- Keep slides teachable, not verbose.
- Use simple YAML only.
- Do not include Markdown fences.

Lesson title: {lesson_title}
Objectives: {objectives_json}
Topics: {topics_json}

Return YAML in this exact shape:
lesson_title: "Lesson title"
slides:
  - title: "Slide title"
    type: "content"
    bullets:
      - "Key point"
```

## Future Validation

Before relying on generated content in the UI, add schema validation for:

- Topic extraction JSON.
- Outline suggestion JSON.
- Lesson plan JSON.
- Slide YAML.

Validation failures should return clear errors and should not silently write invalid structured content to the database.
