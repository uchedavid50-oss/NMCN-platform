import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.session import Base, get_db
from app.main import app
from app.models.user import User
from starlette.testclient import TestClient

# Tests run against a separate database so they never touch real dev data.
# Derived from the same connection settings, just a different database name.
TEST_DB_NAME = "nmcn_test_db"
_base_url = settings.database_url.rsplit("/", 1)[0]
TEST_DATABASE_URL = f"{_base_url}/{TEST_DB_NAME}"


@pytest.fixture(scope="session", autouse=True)
def _create_test_database():
    admin_url = f"{_base_url}/postgres"
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_DB_NAME}
        ).first()
        if not exists:
            conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))
    admin_engine.dispose()


@pytest.fixture(scope="session")
def engine(_create_test_database):
    eng = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)
    eng.dispose()


@pytest.fixture()
def db_session(engine):
    """Each test runs inside its own transaction that's rolled back afterward,
    so tests never see leftover data from one another."""
    connection = engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def make_user(db_session):
    """Factory fixture: create a user directly in the DB and return (user, token),
    skipping the HTTP signup/login round trip for tests that don't need it."""

    def _make_user(email: str = None, role: str = "student", subscription_status: str = "free"):
        user = User(
            email=email or f"{uuid.uuid4().hex}@example.com",
            password_hash=hash_password("testpassword123"),
            role=role,
            subscription_status=subscription_status,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        token = create_access_token(subject=str(user.id))
        return user, token

    return _make_user


@pytest.fixture()
def auth_headers(make_user):
    _, token = make_user()
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_headers(make_user):
    _, token = make_user(role="admin")
    return {"Authorization": f"Bearer {token}"}
