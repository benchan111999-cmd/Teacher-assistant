from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.core.config import get_db
from app.core.models import Topic, Section
from app.modules.topics.service import TopicService
from app.schemas import ExtractTopicsRequest, TopicCreateRequest


router = APIRouter(prefix="/topics", tags=["topics"])


def get_topic_service(db: Session = Depends(get_db)):
    return TopicService(db)


@router.post("/extract")
def extract_topics(
    request: ExtractTopicsRequest,
    service: TopicService = Depends(get_topic_service),
):
    sections = []
    for sid in request.section_ids:
        section = service.db.get(Section, sid)
        if section:
            sections.append(section)
    try:
        topics = service.extract_topics_from_sections(
            request.curriculum_version_id,
            sections,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"topics": [serialize_topic(t, service) for t in topics]}


@router.post("/create")
def create_topic(
    request: TopicCreateRequest,
    service: TopicService = Depends(get_topic_service),
):
    topic = service.create_topic(
        request.curriculum_version_id,
        request.name,
        request.summary,
        request.tags,
    )
    return {"id": topic.id, "name": topic.name}


@router.get("/list/{curriculum_version_id}")
def list_topics(
    curriculum_version_id: int,
    service: TopicService = Depends(get_topic_service),
):
    topics = service.get_topics(curriculum_version_id)
    return [serialize_topic(t, service, include_details=True) for t in topics]


@router.get("/clusters/{curriculum_version_id}")
def get_clusters(
    curriculum_version_id: int,
    service: TopicService = Depends(get_topic_service),
):
    clusters = service.group_by_cluster(curriculum_version_id)
    return {
        cluster_id: [{"id": t.id, "name": t.name} for t in topics]
        for cluster_id, topics in clusters.items()
    }


def serialize_topic(
    topic: Topic,
    service: TopicService,
    include_details: bool = False,
) -> dict:
    data = {
        "id": topic.id,
        "name": topic.name,
        "subtopics": [
            {
                "id": subtopic.id,
                "name": subtopic.name,
                "summary": subtopic.summary,
            }
            for subtopic in service.get_subtopics(topic.id)
        ],
    }
    if include_details:
        data.update(
            {
                "summary": topic.summary,
                "tags": topic.tags,
                "cluster_id": topic.cluster_id,
            }
        )
    return data
