import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


TEST_DATABASE_URL = (
    "postgresql+psycopg2://"
    "peblo:peblo_password@localhost:5432/peblo_tv_test"
)

# Make sure application modules imported by tests use the test database.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL


from app.database import Base  # noqa: E402
from app.models import Artwork, Episode, PublishRun, Season, Show  # noqa: E402


test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    db = TestSessionLocal()

    try:
        yield db
    finally:
        db.rollback()
        db.close()
        