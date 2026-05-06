from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List

from app.core.config import get_db
from app.core.models import CurriculumVersion, CurriculumOutline
from app.modules.curriculum.service import CurriculumService
from app.schemas import (
    VersionCreateRequest,
    VersionResponse,
    VersionListResponse,
    OutlineCreateRequest,
    OutlineUpdateRequest,
    OutlineResponse,
    OutlineListResponse,
)


router = APIRouter(prefix="/curriculum", tags=["curriculum"])


def get_curriculum_service(db: Session = Depends(get_db)) -> CurriculumService:
    return CurriculumService(db)


@router.post("/version", response_model=VersionResponse)
def create_version(
    request: VersionCreateRequest,
    service: CurriculumService = Depends(get_curriculum_service),
) -> VersionResponse:
    version = service.create_version(request.name, request.year, request.notes)
    return VersionResponse(
        id=version.id,
        name=version.name,
        year=version.year,
        notes=version.notes,
    )


@router.get("/version/list", response_model=VersionListResponse)
def list_versions(
    service: CurriculumService = Depends(get_curriculum_service),
) -> VersionListResponse:
    versions = service.list_versions()
    return VersionListResponse(
        versions=[
            VersionResponse(id=v.id, name=v.name, year=v.year, notes=v.notes)
            for v in versions
        ]
    )


@router.get("/version/{version_id}", response_model=VersionResponse)
def get_version(
    version_id: int,
    service: CurriculumService = Depends(get_curriculum_service),
) -> VersionResponse:
    version = service.get_version(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return VersionResponse(
        id=version.id,
        name=version.name,
        year=version.year,
        notes=version.notes,
    )


@router.delete("/version/{version_id}")
def delete_version(
    version_id: int,
    service: CurriculumService = Depends(get_curriculum_service),
):
    if not service.delete_version(version_id):
        raise HTTPException(status_code=404, detail="Version not found")
    return {"message": "Version deleted successfully"}


@router.post("/outline", response_model=OutlineResponse)
def create_outline(
    request: OutlineCreateRequest,
    service: CurriculumService = Depends(get_curriculum_service),
) -> OutlineResponse:
    try:
        outline = service.create_outline(request.curriculum_version_id, request.items)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return OutlineResponse(
        id=outline.id,
        curriculum_version_id=outline.curriculum_version_id,
        items=outline.items,
    )


@router.get("/outline/{outline_id}", response_model=OutlineResponse)
def get_outline(
    outline_id: int,
    service: CurriculumService = Depends(get_curriculum_service),
) -> OutlineResponse:
    outline = service.get_outline(outline_id)
    if not outline:
        raise HTTPException(status_code=404, detail="Outline not found")
    return OutlineResponse(
        id=outline.id,
        curriculum_version_id=outline.curriculum_version_id,
        items=outline.items,
    )


@router.get("/outline/list/{curriculum_version_id}", response_model=OutlineListResponse)
def list_outlines(
    curriculum_version_id: int,
    service: CurriculumService = Depends(get_curriculum_service),
) -> OutlineListResponse:
    outlines = service.list_outlines(curriculum_version_id)
    return OutlineListResponse(
        outlines=[
            OutlineResponse(
                id=o.id,
                curriculum_version_id=o.curriculum_version_id,
                items=o.items,
            )
            for o in outlines
        ]
    )


@router.put("/outline/{outline_id}", response_model=OutlineResponse)
def update_outline(
    outline_id: int,
    request: OutlineUpdateRequest,
    service: CurriculumService = Depends(get_curriculum_service),
) -> OutlineResponse:
    outline = service.update_outline(outline_id, request.items)
    if not outline:
        raise HTTPException(status_code=404, detail="Outline not found")
    return OutlineResponse(
        id=outline.id,
        curriculum_version_id=outline.curriculum_version_id,
        items=outline.items,
    )


@router.get("/diff/{version_a_id}/{version_b_id}")
def diff_versions(
    version_a_id: int,
    version_b_id: int,
    service: CurriculumService = Depends(get_curriculum_service),
):
    return service.diff_versions(version_a_id, version_b_id)


@router.post("/outline/suggest/{curriculum_version_id}")
def suggest_outline(
    curriculum_version_id: int,
    service: CurriculumService = Depends(get_curriculum_service),
):
    suggested = service.suggest_outline(curriculum_version_id)
    return {"items": suggested}
