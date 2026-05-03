from fastapi import APIRouter, UploadFile, File, Depends, Form, HTTPException
from sqlmodel import Session, select
from typing import List
from app.core.config import get_db
from app.core.models import Material, Section
from app.modules.documents.service import DocumentService


router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_service(db: Session = Depends(get_db)):
    return DocumentService(db)


@router.post("/{curriculum_version_id}/upload")
async def upload_material(
    curriculum_version_id: int,
    file: UploadFile = File(...),
    password: str | None = Form(default=None),
    service: DocumentService = Depends(get_document_service),
):
    material = await service.upload_material(file, curriculum_version_id, password=password)
    return {"id": material.id, "file_name": material.file_name, "status": material.status}


@router.get("/{material_id}")
def get_material(
    material_id: int,
    service: DocumentService = Depends(get_document_service),
):
    material = service.get_material(material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material


@router.get("/{material_id}/sections")
def get_sections(
    material_id: int,
    service: DocumentService = Depends(get_document_service),
):
    return service.get_sections(material_id)


@router.get("/list/{curriculum_version_id}")
def list_materials(
    curriculum_version_id: int,
    service: DocumentService = Depends(get_document_service),
):
    return service.list_materials(curriculum_version_id)


@router.delete("/{material_id}")
def delete_material(
    material_id: int,
    service: DocumentService = Depends(get_document_service),
):
    success = service.delete_material(material_id)
    if not success:
        raise HTTPException(status_code=404, detail="Material not found")
    return {"message": "Material deleted successfully"}
