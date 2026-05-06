import logging
from typing import List, Optional
import json

from sqlmodel import select
from sqlalchemy.orm import Session
from app.core.models import Topic, Section, Subtopic
from app.core.llm import call_extract_topics
from app.core.json_utils import serialize_json, deserialize_json


logger = logging.getLogger(__name__)


class TopicService:
    def __init__(self, db: Session):
        self.db = db

    def extract_topics_from_sections(
        self, curriculum_version_id: int, sections: List[Section]
    ) -> List[Topic]:
        section_dicts = [
            {"title": s.title, "body": s.body}
            for s in sections
        ]
        try:
            extracted = call_extract_topics(section_dicts)
        except Exception as e:
            logger.error(f"LLM extraction error: {e}")
            raise RuntimeError(f"Topic extraction failed: {e}") from e
        
        topics = []
        for item in extracted:
            topic = self.create_topic(
                curriculum_version_id=curriculum_version_id,
                name=item.get("name", "Untitled"),
                summary=item.get("summary"),
                tags=item.get("tags"),
                source_section_ids=[s.id for s in sections],
            )
            for position, subtopic_data in enumerate(item.get("subtopics") or []):
                self.create_subtopic(
                    topic_id=topic.id,
                    name=subtopic_data.get("name", "Untitled"),
                    summary=subtopic_data.get("summary"),
                    position=position,
                    source_section_ids=[s.id for s in sections],
                )
            topics.append(topic)
        return topics

    def create_topic(
        self,
        curriculum_version_id: int,
        name: str,
        summary: Optional[str] = None,
        tags: Optional[List[str]] = None,
        source_section_ids: Optional[List[int]] = None,
        cluster_id: Optional[str] = None,
    ) -> Topic:
        topic = Topic(
            curriculum_version_id=curriculum_version_id,
            name=name,
            summary=summary,
            tags=serialize_json(tags),
            source_section_ids=serialize_json(source_section_ids),
            cluster_id=cluster_id,
        )
        self.db.add(topic)
        self.db.commit()
        self.db.refresh(topic)
        logger.info(f"Created topic {topic.id}: {topic.name}")
        return topic

    def get_topics(self, curriculum_version_id: int) -> List[Topic]:
        return list(
            self.db.execute(
                select(Topic).where(
                    Topic.curriculum_version_id == curriculum_version_id
                )
            ).scalars().all()
        )

    def get_topic(self, topic_id: int) -> Optional[Topic]:
        return self.db.get(Topic, topic_id)

    def create_subtopic(
        self,
        topic_id: int,
        name: str,
        summary: Optional[str] = None,
        position: int = 0,
        source_section_ids: Optional[List[int]] = None,
    ) -> Subtopic:
        subtopic = Subtopic(
            topic_id=topic_id,
            name=name,
            summary=summary,
            position=position,
            source_section_ids=serialize_json(source_section_ids),
        )
        self.db.add(subtopic)
        self.db.commit()
        self.db.refresh(subtopic)
        logger.info(f"Created subtopic {subtopic.id}: {subtopic.name}")
        return subtopic

    def get_subtopics(self, topic_id: int) -> List[Subtopic]:
        return list(
            self.db.execute(
                select(Subtopic)
                .where(Subtopic.topic_id == topic_id)
                .order_by(Subtopic.position)
            ).scalars().all()
        )

    def group_by_cluster(self, curriculum_version_id: int) -> dict:
        topics = self.get_topics(curriculum_version_id)
        clusters = {}
        for topic in topics:
            cluster_id = topic.cluster_id or "unclustered"
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(topic)
        return clusters
