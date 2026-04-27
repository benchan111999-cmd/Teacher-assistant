from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.core.config import get_db
from app.modules.lessons.service import LessonService
from app.schemas import GenerateLessonRequest, LessonCreateRequest, LessonUpdateRequest


router = APIRouter(prefix="/lessons", tags=["lessons"])


def get_lesson_service(db: Session = Depends(get_db)):
    return LessonService(db)


@router.post("/generate")
def generate_lesson(
    request: GenerateLessonRequest,
    service: LessonService = Depends(get_lesson_service),
):
    try:
        lesson = service.generate_lesson_plan(
            request.outline_id,
            request.title,
            request.num_lessons,
            request.duration_minutes,
            request.target_audience,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if not lesson:
        raise HTTPException(status_code=500, detail="Lesson generation failed")
    return {"id": lesson.id, "title": lesson.title}


@router.post("/create")
def create_lesson(
    request: LessonCreateRequest,
    service: LessonService = Depends(get_lesson_service),
):
    lesson = service.create_lesson(
        request.outline_id,
        request.title,
        request.objectives,
        request.timeline,
        request.topics,
    )
    return {"id": lesson.id, "title": lesson.title}


@router.get("/{lesson_id}")
def get_lesson(
    lesson_id: int,
    service: LessonService = Depends(get_lesson_service),
):
    lesson = service.get_lesson(lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.get("/list/{outline_id}")
def list_lessons(
    outline_id: int,
    service: LessonService = Depends(get_lesson_service),
):
    return service.list_lessons(outline_id)


@router.put("/{lesson_id}")
def update_lesson(
    lesson_id: int,
    request: LessonUpdateRequest,
    service: LessonService = Depends(get_lesson_service),
):
    lesson = service.update_lesson(
        lesson_id,
        request.title,
        request.objectives,
        request.timeline,
        request.topics,
    )
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson
