# Purpose: Pytest test configuration and isolated fixtures for Resit Saya.
# Security: Sets up isolated temporary SQLite databases and storage directories per test session.

import io
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db import Base, get_db
from app.main import app
from app.models.user import User
from app.security.passwords import hash_password
from app.security.rate_limit import reset_all_rate_limits
from app.security.sessions import create_session
from app.services.receipt_service import seed_default_categories


@pytest.fixture(autouse=True)
def reset_rate_limit_state():
    """Ensure in-memory rate limits are clean before each test."""
    reset_all_rate_limits()
    yield
    reset_all_rate_limits()


@pytest.fixture(scope="session")
def temp_environment():
    """Create isolated temporary database and upload directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_path = tmp_path / "test_resitsaya.db"
        upload_path = tmp_path / "uploads"
        upload_path.mkdir(parents=True, exist_ok=True)

        # Configure settings for test run
        orig_db_url = settings.DATABASE_URL
        orig_upload_dir = settings.UPLOAD_DIR
        settings.DATABASE_URL = f"sqlite:///{db_path}"
        settings.UPLOAD_DIR = str(upload_path)

        engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False},
        )
        TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=engine
        )

        Base.metadata.create_all(bind=engine)

        try:
            yield {
                "engine": engine,
                "SessionLocal": TestingSessionLocal,
                "upload_path": upload_path,
            }
        finally:
            engine.dispose()

        # Cleanup
        settings.DATABASE_URL = orig_db_url
        settings.UPLOAD_DIR = orig_upload_dir


@pytest.fixture
def db(temp_environment):
    """Provide a transactional DB session for tests."""
    SessionLocal = temp_environment["SessionLocal"]
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(temp_environment, db):
    """Provide FastAPI TestClient wired to the temporary DB."""
    SessionLocal = temp_environment["SessionLocal"]

    def override_get_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db):
    user = db.query(User).filter(User.username == "test_admin").first()
    if not user:
        user = User(
            username="test_admin",
            email="admin@test.com",
            password_hash=hash_password("AdminSecret123!"),
            role="admin",
            is_active=True,
            must_change_password=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        seed_default_categories(db, user.id)
    return user


@pytest.fixture
def user_a(db):
    user = db.query(User).filter(User.username == "user_a").first()
    if not user:
        user = User(
            username="user_a",
            email="user_a@test.com",
            password_hash=hash_password("UserAPassword123!"),
            role="user",
            is_active=True,
            must_change_password=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        seed_default_categories(db, user.id)
    return user


@pytest.fixture
def user_b(db):
    user = db.query(User).filter(User.username == "user_b").first()
    if not user:
        user = User(
            username="user_b",
            email="user_b@test.com",
            password_hash=hash_password("UserBPassword123!"),
            role="user",
            is_active=True,
            must_change_password=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        seed_default_categories(db, user.id)
    return user


@pytest.fixture
def forced_user(db):
    user = db.query(User).filter(User.username == "forced_user").first()
    if not user:
        user = User(
            username="forced_user",
            email="forced@test.com",
            password_hash=hash_password("TempPassword123!"),
            role="user",
            is_active=True,
            must_change_password=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        seed_default_categories(db, user.id)
    return user


def create_authenticated_client(user: User, db, temp_environment) -> TestClient:
    SessionLocal = temp_environment["SessionLocal"]

    def override_get_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    c = TestClient(app, base_url="http://testserver")
    token, _ = create_session(db, user.id)
    c.cookies.set(settings.COOKIE_NAME, token)
    return c


@pytest.fixture
def auth_client_a(user_a, db, temp_environment):
    c = create_authenticated_client(user_a, db, temp_environment)
    yield c


@pytest.fixture
def auth_client_b(user_b, db, temp_environment):
    c = create_authenticated_client(user_b, db, temp_environment)
    yield c


@pytest.fixture
def auth_admin(admin_user, db, temp_environment):
    c = create_authenticated_client(admin_user, db, temp_environment)
    yield c


@pytest.fixture
def auth_forced_user(forced_user, db, temp_environment):
    c = create_authenticated_client(forced_user, db, temp_environment)
    yield c


@pytest.fixture
def sample_image_bytes():
    """Generate small valid JPEG image bytes in-memory."""
    buf = io.BytesIO()
    img = Image.new("RGB", (100, 100), color="blue")
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def sample_png_bytes():
    """Generate small valid PNG image bytes in-memory."""
    buf = io.BytesIO()
    img = Image.new("RGBA", (50, 50), color="red")
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_pdf_bytes():
    """Generate minimal valid PDF bytes in-memory."""
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"
