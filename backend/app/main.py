import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel

from app.core.config import get_engine, get_cors_origins, get_max_file_size
from app.core.models import (
    CurriculumVersion,
    Material,
    Section,
    Topic,
    Subtopic,
    CurriculumOutline,
    LessonPlan,
    LessonSlides,
)
from app.modules.documents.router import router as documents_router
from app.modules.topics.router import router as topics_router
from app.modules.curriculum.router import router as curriculum_router
from app.modules.lessons.router import router as lessons_router
from app.modules.slides.router import router as slides_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_db_tables():
    engine = get_engine()
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating database tables...")
    create_db_tables()
    logger.info("Application started successfully")
    yield


app = FastAPI(
    title="Teacher Assistant API",
    description="Teaching preparation assistant - materials to lesson plans",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    max_size = get_max_file_size()
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > max_size:
        return JSONResponse(
            status_code=413,
            content={"error": "File too large", "max_size": max_size},
        )
    return await call_next(request)


cors_origins = get_cors_origins()
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.include_router(documents_router)
app.include_router(topics_router)
app.include_router(curriculum_router)
app.include_router(lessons_router)
app.include_router(slides_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc) if logger.isEnabledFor(logging.DEBUG) else "An error occurred"},
    )


@app.get("/")
def root():
    return {"message": "Teacher Assistant API", "version": "0.1.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
