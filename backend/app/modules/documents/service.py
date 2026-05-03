import logging
from typing import List
from datetime import datetime, timezone
from fastapi import UploadFile, HTTPException, Depends
from sqlmodel import select
from sqlalchemy.orm import Session
from sqlalchemy import delete

from app.core.config import get_db, get_settings, get_allowed_file_types, get_max_file_size
from app.core.models import Material, Section, CurriculumVersion
from app.modules.documents.parsers import (
    OcrRuntimeUnavailable,
    PdfPasswordInvalid,
    PdfPasswordRequired,
    parse_material,
    validate_file_type,
)


logger = logging.getLogger(__name__)


MAX_FILE_SIZE = get_max_file_size()
ALLOWED_TYPES = get_allowed_file_types()


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    async def upload_material(
        self, file: UploadFile, curriculum_version_id: int, password: str | None = None
    ) -> Material:
        version = self.db.get(CurriculumVersion, curriculum_version_id)
        if not version:
            raise HTTPException(
                status_code=404,
                detail=f"Curriculum version {curriculum_version_id} not found"
            )

        content = await file.read()
        logger.info(f"Received file '{file.filename}' with size {len(content)} bytes")
        
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE} bytes"
            )

        extension = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if extension not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{extension}' not allowed. Allowed types: {ALLOWED_TYPES}"
            )

        validated_type = validate_file_type(content, file.filename)
        if not validated_type:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {ALLOWED_TYPES}"
            )
        file_type = validated_type

        material = Material(
            curriculum_version_id=curriculum_version_id,
            file_name=file.filename,
            file_type=file_type,
            status="pending",
        )
        self.db.add(material)
        self.db.commit()
        self.db.refresh(material)

        try:
            sections = parse_material(file_type, content, password=password)
            logger.info(f"Parsed {len(sections) if sections else 0} sections from {file.filename}")
            
            # If no sections, try to at least store the file
            if sections is None:
                raise ValueError(f"Failed to parse {file_type} file")
            
            if len(sections) == 0:
                logger.warning(f"No sections extracted from {file.filename} - may need OCR")
                material.status = "needs_review"
            else:
                for idx, section in enumerate(sections):
                    db_section = Section(
                        material_id=material.id,
                        title=section.title,
                        body=section.body,
                        position=section.position,
                    )
                    self.db.add(db_section)
                material.status = "parsed"
                material.parsed_at = datetime.now(timezone.utc)
            
            self.db.commit()
            self.db.refresh(material)
            logger.info(f"Successfully processed material {material.id}: {file.filename} (status: {material.status})")

        except (PdfPasswordRequired, PdfPasswordInvalid) as e:
            logger.error(f"Failed to process material {material.id}: {e}")
            material.status = "failed"
            self.db.commit()
            raise HTTPException(
                status_code=400,
                detail=str(e),
            )
        except OcrRuntimeUnavailable as e:
            logger.error(f"Failed to process material {material.id}: {e}")
            material.status = "needs_review"
            self.db.commit()
            raise HTTPException(
                status_code=400,
                detail=str(e),
            )
        except (ValueError, IOError) as e:
            logger.error(f"Failed to process material {material.id}: {e}")
            material.status = "failed"
            self.db.commit()
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse file: {str(e)}"
            )

        return material

    def get_material(self, material_id: int) -> Material:
        return self.db.get(Material, material_id)

    def get_sections(self, material_id: int) -> List[Section]:
        return list(
            self.db.execute(
                select(Section)
                .where(Section.material_id == material_id)
                .order_by(Section.position)
            ).scalars().all()
        )

    def list_materials(self, curriculum_version_id: int) -> List[Material]:
        return list(
            self.db.execute(
                select(Material).where(
                    Material.curriculum_version_id == curriculum_version_id
                )
            ).scalars().all()
        )

    def delete_material(self, material_id: int) -> bool:
        material = self.db.get(Material, material_id)
        if not material:
            return False
        
        self.db.execute(
            delete(Section).where(Section.material_id == material_id)
        )
        self.db.delete(material)
        self.db.commit()
        return True
