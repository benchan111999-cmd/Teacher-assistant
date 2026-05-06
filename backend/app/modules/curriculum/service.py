import logging
from typing import List, Optional

from sqlmodel import select
from sqlalchemy.orm import Session
from app.core.models import (
    CurriculumVersion,
    CurriculumOutline,
    LessonPlan,
    LessonSlides,
    Material,
    Section,
    Subtopic,
    Topic,
)
from app.core.llm import call_suggest_outline
from app.core.json_utils import serialize_json, deserialize_json


logger = logging.getLogger(__name__)


class CurriculumService:
    def __init__(self, db: Session):
        self.db = db

    def create_version(self, name: str, year: int, notes: Optional[str] = None) -> CurriculumVersion:
        version = CurriculumVersion(name=name, year=year, notes=notes)
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        logger.info(f"Created curriculum version {version.id}: {version.name}")
        return version

    def get_version(self, version_id: int) -> Optional[CurriculumVersion]:
        return self.db.get(CurriculumVersion, version_id)

    def list_versions(self) -> List[CurriculumVersion]:
        return list(self.db.execute(select(CurriculumVersion)).scalars().all())

    def delete_version(self, version_id: int) -> bool:
        version = self.db.get(CurriculumVersion, version_id)
        if not version:
            return False

        outlines = list(
            self.db.execute(
                select(CurriculumOutline).where(
                    CurriculumOutline.curriculum_version_id == version_id
                )
            ).scalars().all()
        )
        for outline in outlines:
            lessons = list(
                self.db.execute(
                    select(LessonPlan).where(LessonPlan.outline_id == outline.id)
                ).scalars().all()
            )
            for lesson in lessons:
                slides = list(
                    self.db.execute(
                        select(LessonSlides).where(LessonSlides.lesson_id == lesson.id)
                    ).scalars().all()
                )
                for slide in slides:
                    self.db.delete(slide)
                self.db.delete(lesson)
            self.db.delete(outline)

        topics = list(
            self.db.execute(
                select(Topic).where(Topic.curriculum_version_id == version_id)
            ).scalars().all()
        )
        for topic in topics:
            subtopics = list(
                self.db.execute(
                    select(Subtopic).where(Subtopic.topic_id == topic.id)
                ).scalars().all()
            )
            for subtopic in subtopics:
                self.db.delete(subtopic)
            self.db.delete(topic)

        materials = list(
            self.db.execute(
                select(Material).where(Material.curriculum_version_id == version_id)
            ).scalars().all()
        )
        for material in materials:
            sections = list(
                self.db.execute(
                    select(Section).where(Section.material_id == material.id)
                ).scalars().all()
            )
            for section in sections:
                self.db.delete(section)
            self.db.delete(material)

        self.db.delete(version)
        self.db.commit()
        logger.info(f"Deleted curriculum version {version_id}")
        return True

    def create_outline(
        self, curriculum_version_id: int, items: List[dict]
    ) -> CurriculumOutline:
        version = self.db.get(CurriculumVersion, curriculum_version_id)
        if not version:
            logger.error(f"Curriculum version {curriculum_version_id} not found")
            raise ValueError(f"Curriculum version {curriculum_version_id} not found")
        
        outline = CurriculumOutline(
            curriculum_version_id=curriculum_version_id,
            items=serialize_json(items),
        )
        self.db.add(outline)
        self.db.commit()
        self.db.refresh(outline)
        logger.info(f"Created outline {outline.id} for version {curriculum_version_id}")
        return outline

    def get_outline(self, outline_id: int) -> Optional[CurriculumOutline]:
        return self.db.get(CurriculumOutline, outline_id)

    def list_outlines(self, curriculum_version_id: int) -> List[CurriculumOutline]:
        return list(
            self.db.execute(
                select(CurriculumOutline).where(
                    CurriculumOutline.curriculum_version_id == curriculum_version_id
                )
            ).scalars().all()
        )

    def update_outline(self, outline_id: int, items: List[dict]) -> Optional[CurriculumOutline]:
        outline = self.db.get(CurriculumOutline, outline_id)
        if outline:
            outline.items = serialize_json(items)
            self.db.commit()
            self.db.refresh(outline)
            logger.info(f"Updated outline {outline_id}")
        return outline

    def suggest_outline(self, curriculum_version_id: int) -> List[dict]:
        topics = list(self.db.execute(
            select(Topic).where(Topic.curriculum_version_id == curriculum_version_id)
        ).scalars().all())
        topic_dicts = [
            {"name": t.name, "summary": t.summary}
            for t in topics
        ]
        
        if not topic_dicts:
            logger.warning(f"No topics found for version {curriculum_version_id}")
            return []
        
        try:
            suggested = call_suggest_outline(topic_dicts)
        except Exception as e:
            logger.error(f"LLM outline suggestion error: {e}")
            suggested = []
        
        return suggested

    def diff_versions(self, version_a_id: int, version_b_id: int) -> dict:
        topics_a = list(self.db.execute(
            select(Topic).where(Topic.curriculum_version_id == version_a_id)
        ).scalars().all())
        topics_b = list(self.db.execute(
            select(Topic).where(Topic.curriculum_version_id == version_b_id)
        ).scalars().all())

        cluster_keys_a = {self._topic_diff_key(t) for t in topics_a}
        cluster_keys_b = {self._topic_diff_key(t) for t in topics_b}

        common = cluster_keys_a & cluster_keys_b
        unique_a = cluster_keys_a - cluster_keys_b
        unique_b = cluster_keys_b - cluster_keys_a

        return {
            "common": sorted(common),
            "unique_to_version_a": sorted(unique_a),
            "unique_to_version_b": sorted(unique_b),
        }

    @staticmethod
    def _topic_diff_key(topic: Topic) -> str:
        return topic.cluster_id or topic.name
