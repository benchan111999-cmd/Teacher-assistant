import pytest
from sqlmodel import Session, SQLModel, create_engine
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import get_db


@pytest.fixture(scope="session")
def test_engine(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("db") / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def db_session(test_engine):
    from sqlalchemy.orm import sessionmaker
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(test_engine):
    from sqlalchemy.orm import sessionmaker
    from app import core
    import app.main as app_main

    original_config_get_engine = core.config.get_engine
    original_main_get_engine = app_main.get_engine
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_engine():
        return test_engine

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    core.config.get_engine = override_get_engine
    app_main.get_engine = override_get_engine
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    core.config.get_engine = original_config_get_engine
    app_main.get_engine = original_main_get_engine
