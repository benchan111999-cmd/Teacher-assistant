import logging
from typing import List, Optional
import json

from sqlmodel import select
from sqlalchemy.orm import Session
from app.core.models import LessonPlan, CurriculumOutline, Topic
from app.core.llm import call_generate_lesson_plan
from app.core.json_utils import serialize_json, deserialize_json


logger = logging.getLogger(__name__)


class LessonService:
    def __init__(self, db: Session):
        self.db = db

    def generate_lesson_plan(
        self,
        outline_id: int,
        title: str,
        num_lessons: int = 1,
        duration_minutes: int = 45,
        target_audience: str = "general",
    ) -> LessonPlan:
        outline = self.db.get(CurriculumOutline, outline_id)
        if not outline:
            logger.error(f"Outline {outline_id} not found")
            raise ValueError(f"Outline {outline_id} not found")
        
        try:
            items = deserialize_json(outline.items)
        except Exception as e:
            logger.error(f"Failed to parse outline items: {e}")
            items = []
        
        try:
            result = call_generate_lesson_plan(
                items, num_lessons, duration_minutes, target_audience
            )
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            result = {"title": title, "lessons": []}
        
        created_lessons = []
        for lesson_data in result.get("lessons", []):
            lesson = self.create_lesson(
                outline_id=outline_id,
                title=lesson_data.get("title", title),
                objectives=lesson_data.get("objectives"),
                timeline=lesson_data.get("timeline"),
                topics=lesson_data.get("topics"),
            )
            created_lessons.append(lesson)
        
        return created_lessons[0] if created_lessons else None

    def create_lesson(
        self,
        outline_id: int,
        title: str,
        objectives: Optional[List[str]] = None,
        timeline: Optional[List[dict]] = None,
        topics: Optional[List[str]] = None,
    ) -> LessonPlan:
        lesson = LessonPlan(
            outline_id=outline_id,
            title=title,
            objectives=serialize_json(objectives),
            timeline=serialize_json(timeline),
            topics=serialize_json(topics),
        )
        self.db.add(lesson)
        self.db.commit()
        self.db.refresh(lesson)
        logger.info(f"Created lesson {lesson.id}: {lesson.title}")
        return lesson

    def get_lesson(self, lesson_id: int) -> Optional[LessonPlan]:
        return self.db.get(LessonPlan, lesson_id)

    def list_lessons(self, outline_id: int) -> List[LessonPlan]:
        return list(
            self.db.execute(select(LessonPlan).where(LessonPlan.outline_id == outline_id)).scalars().all()
        )

    def update_lesson(
        self,
        lesson_id: int,
        title: Optional[str] = None,
        objectives: Optional[List[str]] = None,
        timeline: Optional[List[dict]] = None,
        topics: Optional[List[str]] = None,
    ) -> LessonPlan:
        lesson = self.db.get(LessonPlan, lesson_id)
        if not lesson:
            logger.error(f"Lesson {lesson_id} not found")
            return None
        
        if title is not None:
            lesson.title = title
        if objectives is not None:
            lesson.objectives = serialize_json(objectives)
        if timeline is not None:
            lesson.timeline = serialize_json(timeline)
        if topics is not None:
            lesson.topics = serialize_json(topics)
        
        self.db.commit()
        self.db.refresh(lesson)
        logger.info(f"Updated lesson {lesson.id}")
        return lesson