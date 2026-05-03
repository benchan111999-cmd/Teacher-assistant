from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class VersionCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    year: int = Field(..., ge=1900, le=2100)
    notes: Optional[str] = None


class VersionResponse(BaseModel):
    id: int
    name: str
    year: int
    notes: Optional[str] = None


class VersionListResponse(BaseModel):
    versions: List[VersionResponse]


class OutlineCreateRequest(BaseModel):
    curriculum_version_id: int = Field(..., gt=0)
    items: List[Dict[str, Any]]


class OutlineUpdateRequest(BaseModel):
    items: List[Dict[str, Any]]


class OutlineResponse(BaseModel):
    id: int
    curriculum_version_id: int
    items: str


class OutlineListResponse(BaseModel):
    outlines: List[OutlineResponse]


class TopicCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    curriculum_version_id: int = Field(..., gt=0)
    summary: Optional[str] = None
    tags: Optional[List[str]] = None


class SubtopicResponse(BaseModel):
    id: int
    name: str
    summary: Optional[str] = None


class TopicResponse(BaseModel):
    id: int
    name: str
    summary: Optional[str] = None
    tags: Optional[str] = None
    cluster_id: Optional[str] = None
    subtopics: List[SubtopicResponse] = Field(default_factory=list)


class TopicListResponse(BaseModel):
    topics: List[TopicResponse]


class LessonCreateRequest(BaseModel):
    outline_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=200)
    objectives: Optional[List[str]] = None
    timeline: Optional[List[Dict[str, Any]]] = None
    topics: Optional[List[str]] = None


class LessonUpdateRequest(BaseModel):
    title: Optional[str] = None
    objectives: Optional[List[str]] = None
    timeline: Optional[List[Dict[str, Any]]] = None
    topics: Optional[List[str]] = None


class LessonResponse(BaseModel):
    id: int
    outline_id: int
    title: str
    objectives: Optional[str] = None
    timeline: Optional[str] = None
    topics: Optional[str] = None


class LessonListResponse(BaseModel):
    lessons: List[LessonResponse]


class SlidesUpdateRequest(BaseModel):
    yaml_content: str


class SlidesResponse(BaseModel):
    id: int
    lesson_id: int
    yaml: Optional[str] = None
    html: Optional[str] = None


class ExtractTopicsRequest(BaseModel):
    curriculum_version_id: int = Field(..., gt=0)
    section_ids: List[int] = Field(..., min_length=1)


class GenerateLessonRequest(BaseModel):
    outline_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=200)
    num_lessons: int = Field(default=1, ge=1, le=20)
    duration_minutes: int = Field(default=45, ge=5, le=180)
    target_audience: str = Field(default="general")


class FileUploadResponse(BaseModel):
    id: int
    file_name: str
    status: str


class HealthResponse(BaseModel):
    status: str


class RootResponse(BaseModel):
    message: str
    version: str
