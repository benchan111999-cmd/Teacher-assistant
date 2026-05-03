import logging
from typing import Optional

from sqlmodel import select
from sqlalchemy.orm import Session
from app.core.models import LessonSlides, LessonPlan
from app.core.llm import call_generate_yaml_slides
from app.core.json_utils import deserialize_json


logger = logging.getLogger(__name__)


class SlidesService:
    def __init__(self, db: Session):
        self.db = db

    def generate_yaml(self, lesson_id: int) -> LessonSlides:
        lesson = self.db.get(LessonPlan, lesson_id)
        if not lesson:
            logger.error(f"Lesson {lesson_id} not found")
            raise ValueError(f"Lesson {lesson_id} not found")
        
        try:
            objectives = deserialize_json(lesson.objectives) if lesson.objectives else []
            topics = deserialize_json(lesson.topics) if lesson.topics else []
        except Exception as e:
            logger.error(f"Failed to parse lesson data: {e}")
            objectives = []
            topics = []
        
        try:
            yaml_content = call_generate_yaml_slides(
                lesson.title, objectives, topics
            )
        except Exception as e:
            logger.error(f"LLM YAML generation error: {e}")
            yaml_content = ""
        
        return self.set_yaml(lesson_id, yaml_content)

    def set_yaml(self, lesson_id: int, yaml_content: str) -> LessonSlides:
        existing = self.db.execute(
            select(LessonSlides).where(LessonSlides.lesson_id == lesson_id)
        ).scalars().first()
        
        if existing:
            existing.yaml = yaml_content
            self.db.commit()
            self.db.refresh(existing)
            logger.info(f"Updated slides for lesson {lesson_id}")
            return existing
        
        slides = LessonSlides(
            lesson_id=lesson_id,
            yaml=yaml_content,
        )
        self.db.add(slides)
        self.db.commit()
        self.db.refresh(slides)
        logger.info(f"Created slides for lesson {lesson_id}")
        return slides

    def render_html(self, lesson_id: int) -> LessonSlides:
        slides = self.db.execute(
            select(LessonSlides).where(LessonSlides.lesson_id == lesson_id)
        ).scalars().first()
        
        if not slides or not slides.yaml:
            logger.error(f"Slides or YAML not found for lesson {lesson_id}")
            return None
        
        html = f"<html><body><pre>{slides.yaml}</pre></body></html>"
        slides.html = html
        self.db.commit()
        self.db.refresh(slides)
        logger.info(f"Rendered HTML for lesson {lesson_id}")
        return slides

    def get_slides(self, lesson_id: int) -> Optional[LessonSlides]:
        return self.db.execute(
            select(LessonSlides).where(LessonSlides.lesson_id == lesson_id)
        ).scalars().first()
