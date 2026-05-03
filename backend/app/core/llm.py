import json
from typing import List, Optional, Dict, Any
from openai import OpenAI
from app.core.config import get_settings


def get_llm_client() -> OpenAI:
    settings = get_settings()
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OPENAI_API_KEY not configured")
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )


def call_llm(
    prompt: str,
    system_prompt: str = "You are a helpful teaching assistant.",
    temperature: float = 0.7,
    response_format: Optional[Dict] = None,
    model: Optional[str] = None,
) -> Any:
    client = get_llm_client()
    settings = get_settings()
    model = model or settings.LLM_MODEL
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if response_format:
        kwargs["response_format"] = response_format
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


def extract_topics_from_sections_prompt(sections: List[dict]) -> str:
    content = []
    for i, section in enumerate(sections):
        content.append(f"Section {i + 1}: {section.get('title', 'Untitled')}")
        body = section.get('body', '')[:500]
        content.append(f"Content: {body}\n")
    return "\n".join(content)


def call_extract_topics(sections: List[dict]) -> List[dict]:
    """Extract topics from sections using LLM."""
    system_prompt = """You are a teaching curriculum expert. Analyze teaching material sections and extract key topics.
For each topic, provide:
- name: short descriptive name (max 50 chars)
- summary: brief explanation (max 200 chars)
- tags: relevant keywords (array of strings)
- subtopics: optional array of smaller teaching points, each with name and summary

Output as JSON array."""
    content = extract_topics_from_sections_prompt(sections)
    prompt = f"""Extract 5-15 key topics from these teaching material sections:

{content}

Return ONLY a JSON array like:
[{{"name": "Topic Name", "summary": "...", "tags": ["tag1", "tag2"], "subtopics": [{{"name": "Subtopic", "summary": "..."}}]}}]
No other text."""
    result = call_llm(prompt, system_prompt=system_prompt, temperature=0.3)
    try:
        topics = json.loads(result)
        return topics if isinstance(topics, list) else []
    except json.JSONDecodeError:
        return []


def call_generate_lesson_plan(
    outline_items: List[dict],
    num_lessons: int,
    duration_minutes: int,
    target_audience: str,
) -> dict:
    """Generate lesson plan from outline using LLM."""
    system_prompt = """You are an expert curriculum planner. Create detailed lesson plans from curriculum outlines."""
    prompt = f"""Create {num_lessons} lesson plan(s) for a {duration_minutes}-minute class targeting {target_audience}.

Outline items:
{json.dumps(outline_items, indent=2)}

Return JSON:
{{
  "title": "Overall title",
  "lessons": [
    {{
      "title": "Lesson title",
      "objectives": ["objective 1", "objective 2"],
      "timeline": [{{"time": "0-10min", "activity": "..."}}],
      "topics": ["topic 1", "topic 2"]
    }}
  ]
}}"""
    result = call_llm(prompt, system_prompt=system_prompt, temperature=0.5)
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {"title": "", "lessons": []}


def call_generate_yaml_slides(
    lesson_title: str,
    objectives: List[str],
    topics: List[str],
) -> str:
    """Generate YAML slide content from lesson plan using LLM."""
    system_prompt = """You are a presentation expert. Create structured YAML slide content for teaching lessons."""
    prompt = f"""Create YAML slide deck for lesson: {lesson_title}

Objectives: {json.dumps(objectives)}
Topics: {json.dumps(topics)}

Return YAML content (no markdown fences):
---
title: {lesson_title}
slides:
  - type: title
    content: {lesson_title}
  - type: objectives
    content: {{objectives}}
  - type: content
    content: Topic 1
  - type: content
    content: Topic 2
  - type: summary
    content: Key takeaways"""
    result = call_llm(prompt, system_prompt=system_prompt, temperature=0.3)
    return result or ""


def call_suggest_outline(topics: List[dict]) -> List[dict]:
    """Suggest curriculum outline based on topics using LLM."""
    system_prompt = """You are a curriculum expert. Organize topics into a logical teaching sequence."""
    prompt = f"""Organize these {len(topics)} topics into a recommended teaching outline.

Topics:
{json.dumps([{"name": t.get("name", ""), "summary": t.get("summary", "")} for t in topics], indent=2)}

Return JSON array (each item has "type": "topic" or "type": "header" or "type": "section"):
[{{"type": "topic", "topic_id": 1}}, {{"type": "header", "title": "Module 1"}}]

Sequence the topics logically for teaching."""
    result = call_llm(prompt, system_prompt=system_prompt, temperature=0.4)
    try:
        outline = json.loads(result)
        return outline if isinstance(outline, list) else []
    except json.JSONDecodeError:
        return []
