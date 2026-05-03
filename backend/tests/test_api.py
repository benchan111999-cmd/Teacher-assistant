import pytest
from fastapi import HTTPException

from app.core.models import CurriculumOutline, CurriculumVersion, LessonPlan, Material, Section, Subtopic, Topic
from app.modules.documents.service import DocumentService
from app.modules.lessons.service import LessonService
from app.modules.topics.service import TopicService


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Teacher Assistant API" in response.json()["message"]


def test_create_curriculum_version(client):
    response = client.post(
        "/curriculum/version",
        json={"name": "Test Curriculum", "year": 2025}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Curriculum"
    assert data["year"] == 2025


def test_list_curriculum_versions_returns_collection(client):
    response = client.get("/curriculum/version/list")
    assert response.status_code == 200
    data = response.json()
    assert "versions" in data
    assert isinstance(data["versions"], list)


def test_get_nonexistent_version(client):
    response = client.get("/curriculum/version/99999")
    assert response.status_code == 404


def test_get_nonexistent_outline(client):
    response = client.get("/curriculum/outline/99999")
    assert response.status_code == 404


def test_create_and_list_outlines_by_curriculum_version(client):
    version_response = client.post(
        "/curriculum/version",
        json={"name": "Outline Curriculum", "year": 2025},
    )
    version_id = version_response.json()["id"]

    create_response = client.post(
        "/curriculum/outline",
        json={
            "curriculum_version_id": version_id,
            "items": [{"type": "topic", "topic_id": 1, "title": "Fractions"}],
        },
    )

    assert create_response.status_code == 200

    list_response = client.get(f"/curriculum/outline/list/{version_id}")

    assert list_response.status_code == 200
    data = list_response.json()
    assert len(data["outlines"]) == 1
    assert data["outlines"][0]["curriculum_version_id"] == version_id
    assert "Fractions" in data["outlines"][0]["items"]


def test_extract_topics_accepts_json_body(client, db_session, monkeypatch):
    version = CurriculumVersion(name="Topic Curriculum", year=2025)
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)

    material = Material(
        curriculum_version_id=version.id,
        file_name="lesson.pdf",
        file_type="pdf",
        status="parsed",
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(material)

    section = Section(
        material_id=material.id,
        title="Fractions",
        body="Equivalent fractions",
        position=1,
    )
    db_session.add(section)
    db_session.commit()
    db_session.refresh(section)

    def fake_extract(self, curriculum_version_id, sections):
        assert curriculum_version_id == version.id
        assert [s.id for s in sections] == [section.id]
        return [Topic(id=10, curriculum_version_id=version.id, name="Fractions")]

    monkeypatch.setattr(TopicService, "extract_topics_from_sections", fake_extract)

    response = client.post(
        "/topics/extract",
        json={"curriculum_version_id": version.id, "section_ids": [section.id]},
    )

    assert response.status_code == 200
    assert response.json() == {"topics": [{"id": 10, "name": "Fractions", "subtopics": []}]}


def test_upload_pdf_accepts_password_form_field(client, monkeypatch):
    version_response = client.post(
        "/curriculum/version",
        json={"name": "Protected Curriculum", "year": 2026},
    )
    version_id = version_response.json()["id"]
    captured = {}

    def fake_parse_material(file_type, content, password=None):
        captured["file_type"] = file_type
        captured["password"] = password
        return []

    monkeypatch.setattr("app.modules.documents.service.parse_material", fake_parse_material)

    response = client.post(
        f"/documents/{version_id}/upload",
        data={"password": "secret"},
        files={"file": ("protected.pdf", b"%PDF-1.4 content", "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": response.json()["id"],
        "file_name": "protected.pdf",
        "status": "needs_review",
    }
    assert captured == {"file_type": "pdf", "password": "secret"}
    assert "secret" not in str(response.json())


def test_extract_topics_returns_nested_subtopics(client, db_session, monkeypatch):
    version = CurriculumVersion(name="Nested Topic Curriculum", year=2026)
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)

    material = Material(
        curriculum_version_id=version.id,
        file_name="lesson.pdf",
        file_type="pdf",
        status="parsed",
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(material)

    section = Section(
        material_id=material.id,
        title="ECG rhythm",
        body="Rate assessment and rhythm regularity",
        position=1,
    )
    db_session.add(section)
    db_session.commit()
    db_session.refresh(section)

    def fake_call_extract_topics(sections):
        return [
            {
                "name": "ECG Rhythm Assessment",
                "summary": "Assess ECG rhythm strips.",
                "tags": ["ecg"],
                "subtopics": [
                    {
                        "name": "Rate assessment",
                        "summary": "Estimate ventricular rate.",
                    },
                    {
                        "name": "Rhythm regularity",
                        "summary": "Check R-R interval regularity.",
                    },
                ],
            }
        ]

    monkeypatch.setattr("app.modules.topics.service.call_extract_topics", fake_call_extract_topics)

    response = client.post(
        "/topics/extract",
        json={"curriculum_version_id": version.id, "section_ids": [section.id]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["topics"][0]["name"] == "ECG Rhythm Assessment"
    assert [s["name"] for s in data["topics"][0]["subtopics"]] == [
        "Rate assessment",
        "Rhythm regularity",
    ]

    subtopics = db_session.query(Subtopic).all()
    assert [s.name for s in subtopics] == ["Rate assessment", "Rhythm regularity"]


def test_create_topic_accepts_json_body_with_tags(client):
    version_response = client.post(
        "/curriculum/version",
        json={"name": "Topic Create Curriculum", "year": 2025},
    )
    version_id = version_response.json()["id"]

    response = client.post(
        "/topics/create",
        json={
            "name": "Decimals",
            "curriculum_version_id": version_id,
            "summary": "Decimal notation",
            "tags": ["math", "number"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Decimals"


def test_generate_lesson_accepts_json_body(client, db_session, monkeypatch):
    outline = _create_outline(db_session)

    def fake_generate(self, outline_id, title, num_lessons, duration_minutes, target_audience):
        assert outline_id == outline.id
        assert title == "Lesson 1"
        assert num_lessons == 2
        assert duration_minutes == 50
        assert target_audience == "Grade 5"
        return LessonPlan(id=22, outline_id=outline.id, title=title)

    monkeypatch.setattr(LessonService, "generate_lesson_plan", fake_generate)

    response = client.post(
        "/lessons/generate",
        json={
            "outline_id": outline.id,
            "title": "Lesson 1",
            "num_lessons": 2,
            "duration_minutes": 50,
            "target_audience": "Grade 5",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"id": 22, "title": "Lesson 1"}


def test_create_and_update_lesson_accept_json_body(client, db_session):
    outline = _create_outline(db_session)

    create_response = client.post(
        "/lessons/create",
        json={
            "outline_id": outline.id,
            "title": "Original",
            "objectives": ["Understand fractions"],
            "timeline": [{"time": "10m", "activity": "Warm-up"}],
            "topics": ["Fractions"],
        },
    )

    assert create_response.status_code == 200
    lesson_id = create_response.json()["id"]

    update_response = client.put(
        f"/lessons/{lesson_id}",
        json={
            "title": "Updated",
            "objectives": ["Compare fractions"],
            "timeline": [{"time": "15m", "activity": "Practice"}],
            "topics": ["Equivalent fractions"],
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated"


def test_set_yaml_accepts_json_body(client, db_session):
    outline = _create_outline(db_session)
    lesson = LessonPlan(outline_id=outline.id, title="Slides Lesson")
    db_session.add(lesson)
    db_session.commit()
    db_session.refresh(lesson)

    response = client.put(
        f"/slides/yaml/{lesson.id}",
        json={"yaml_content": "title: Slides Lesson"},
    )

    assert response.status_code == 200
    assert response.json()["yaml"] == "title: Slides Lesson"


def _create_outline(db_session):
    version = CurriculumVersion(name="Test Curriculum", year=2025)
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)

    outline = CurriculumOutline(curriculum_version_id=version.id, items="[]")
    db_session.add(outline)
    db_session.commit()
    db_session.refresh(outline)
    return outline
