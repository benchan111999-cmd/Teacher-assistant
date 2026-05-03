from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.core.config import get_db
from app.modules.slides.service import SlidesService
from app.schemas import SlidesUpdateRequest


router = APIRouter(prefix="/slides", tags=["slides"])


def get_slides_service(db: Session = Depends(get_db)):
    return SlidesService(db)


@router.post("/generate/{lesson_id}")
def generate_slides(
    lesson_id: int,
    service: SlidesService = Depends(get_slides_service),
):
    slides = service.generate_yaml(lesson_id)
    return {"id": slides.id, "lesson_id": slides.lesson_id, "yaml": slides.yaml}


@router.put("/yaml/{lesson_id}")
def set_yaml(
    lesson_id: int,
    request: SlidesUpdateRequest,
    service: SlidesService = Depends(get_slides_service),
):
    slides = service.set_yaml(lesson_id, request.yaml_content)
    return {"id": slides.id, "yaml": slides.yaml}


@router.post("/render/{lesson_id}")
def render_html(
    lesson_id: int,
    service: SlidesService = Depends(get_slides_service),
):
    slides = service.render_html(lesson_id)
    if not slides:
        raise HTTPException(status_code=404, detail="Slides not found")
    return {"id": slides.id, "html": slides.html}


@router.get("/{lesson_id}")
def get_slides(
    lesson_id: int,
    service: SlidesService = Depends(get_slides_service),
):
    slides = service.get_slides(lesson_id)
    if not slides:
        raise HTTPException(status_code=404, detail="Slides not found")
    return slides
