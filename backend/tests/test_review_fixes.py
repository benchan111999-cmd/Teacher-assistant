from app.core.models import (
    CurriculumOutline,
    CurriculumVersion,
    LessonPlan,
    LessonSlides,
    Topic,
)
from app.modules.curriculum.service import CurriculumService
from app.modules.slides.service import SlidesService


def test_slides_set_yaml_updates_existing_slide_model(db_session):
    lesson = _create_lesson(db_session)
    service = SlidesService(db_session)

    created = service.set_yaml(lesson.id, "first")
    updated = service.set_yaml(lesson.id, "second")

    assert isinstance(updated, LessonSlides)
    assert updated.id == created.id
    assert updated.yaml == "second"


def test_slides_render_html_updates_existing_slide_model(db_session):
    lesson = _create_lesson(db_session)
    service = SlidesService(db_session)
    service.set_yaml(lesson.id, "title: Lesson")

    slides = service.render_html(lesson.id)

    assert isinstance(slides, LessonSlides)
    assert slides.html == "<html><body><pre>title: Lesson</pre></body></html>"


def test_slides_generate_endpoint_calls_service_with_lesson_id_only(client, monkeypatch):
    captured = {}

    def fake_generate_yaml(self, lesson_id):
        captured["lesson_id"] = lesson_id
        return LessonSlides(id=7, lesson_id=lesson_id, yaml="title: Test")

    monkeypatch.setattr(SlidesService, "generate_yaml", fake_generate_yaml)

    response = client.post("/slides/generate/123")

    assert response.status_code == 200
    assert response.json() == {"id": 7, "lesson_id": 123, "yaml": "title: Test"}
    assert captured == {"lesson_id": 123}


def test_curriculum_diff_uses_shared_cluster_ids(db_session):
    version_a = CurriculumVersion(name="A", year=2025)
    version_b = CurriculumVersion(name="B", year=2026)
    db_session.add(version_a)
    db_session.add(version_b)
    db_session.commit()
    db_session.refresh(version_a)
    db_session.refresh(version_b)

    db_session.add(Topic(curriculum_version_id=version_a.id, name="Fractions", cluster_id="math-1"))
    db_session.add(Topic(curriculum_version_id=version_b.id, name="Equivalent Fractions", cluster_id="math-1"))
    db_session.add(Topic(curriculum_version_id=version_a.id, name="Decimals", cluster_id="math-2"))
    db_session.add(Topic(curriculum_version_id=version_b.id, name="Geometry", cluster_id="math-3"))
    db_session.commit()

    diff = CurriculumService(db_session).diff_versions(version_a.id, version_b.id)

    assert diff["common"] == ["math-1"]
    assert diff["unique_to_version_a"] == ["math-2"]
    assert diff["unique_to_version_b"] == ["math-3"]


def _create_lesson(db_session):
    version = CurriculumVersion(name="Test", year=2025)
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)

    outline = CurriculumOutline(curriculum_version_id=version.id, items="[]")
    db_session.add(outline)
    db_session.commit()
    db_session.refresh(outline)

    lesson = LessonPlan(outline_id=outline.id, title="Lesson")
    db_session.add(lesson)
    db_session.commit()
    db_session.refresh(lesson)
    return lesson
