from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional


class CurriculumVersion(SQLModel, table=True):
    __tablename__ = "curriculum_versions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    year: int
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Material(SQLModel, table=True):
    __tablename__ = "materials"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    curriculum_version_id: int = Field(foreign_key="curriculum_versions.id")
    file_name: str
    file_type: str
    parsed_at: Optional[datetime] = None
    status: str = Field(default="pending")


class Section(SQLModel, table=True):
    __tablename__ = "sections"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    material_id: int = Field(foreign_key="materials.id")
    title: str
    body: str
    position: int


class Topic(SQLModel, table=True):
    __tablename__ = "topics"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    curriculum_version_id: int = Field(foreign_key="curriculum_versions.id")
    name: str
    summary: Optional[str] = None
    tags: Optional[str] = None
    source_section_ids: Optional[str] = None
    cluster_id: Optional[str] = None


class CurriculumOutline(SQLModel, table=True):
    __tablename__ = "curriculum_outlines"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    curriculum_version_id: int = Field(foreign_key="curriculum_versions.id")
    items: str


class LessonPlan(SQLModel, table=True):
    __tablename__ = "lesson_plans"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    outline_id: int = Field(foreign_key="curriculum_outlines.id")
    title: str
    objectives: Optional[str] = None
    timeline: Optional[str] = None
    topics: Optional[str] = None


class LessonSlides(SQLModel, table=True):
    __tablename__ = "lesson_slides"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    lesson_id: int = Field(foreign_key="lesson_plans.id")
    yaml: Optional[str] = None
    html: Optional[str] = None
