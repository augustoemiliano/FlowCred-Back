"""Fixtures de teste: SQLite temporário + uploads em diretório temporário.

As variáveis de ambiente são definidas antes de importar a app, porque
`app.core.config.settings` e o engine são criados no import.
"""

import os
import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="flowcred-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP / 'test.db').as_posix()}"
os.environ["UPLOAD_DIR"] = str(_TMP / "uploads")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-with-enough-length"
os.environ["BACKEND_CORS_ORIGINS"] = "http://localhost:5173"
os.environ["MAX_UPLOAD_BYTES"] = str(64 * 1024)
os.environ["SEED_DEV_DATA"] = "0"

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin-pass"
VALID_CPF = "52998224725"
VALID_CPF_2 = "11144477735"
VALID_CNPJ = "11222333000181"


@pytest.fixture(scope="session", autouse=True)
def _migrated_db() -> Iterator[None]:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    command.upgrade(cfg, "head")
    yield
    engine.dispose()
    shutil.rmtree(_TMP, ignore_errors=True)


@pytest.fixture(autouse=True)
def _clean_tables() -> Iterator[None]:
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def admin_user(db) -> User:
    user = User(
        username=ADMIN_USERNAME,
        hashed_password=hash_password(ADMIN_PASSWORD),
        is_active=True,
        is_superuser=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers(client: TestClient, admin_user: User) -> dict[str, str]:
    res = client.post("/api/v1/auth/login", json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture
def make_client(client: TestClient, auth_headers):
    def _make(document: str = VALID_CPF, **overrides) -> dict:
        payload = {
            "name": "Maria Silva",
            "document": document,
            "phone": "11987654321",
            "email": "maria@example.com",
            "monthly_income": "8500.00",
            "notes": None,
            **overrides,
        }
        res = client.post("/api/v1/clients", json=payload, headers=auth_headers)
        assert res.status_code == 201, res.text
        return res.json()

    return _make


@pytest.fixture
def make_proposal(client: TestClient, auth_headers, admin_user, make_client):
    def _make(client_id: int | None = None, **overrides) -> dict:
        if client_id is None:
            client_id = make_client()["id"]
        payload = {
            "client_id": client_id,
            "bank": "Caixa",
            "property_value": "500000.00",
            "financed_amount": "350000.00",
            "responsible_user_id": admin_user.id,
            "next_stage_date": None,
            "notes": None,
            **overrides,
        }
        res = client.post("/api/v1/proposals", json=payload, headers=auth_headers)
        assert res.status_code == 201, res.text
        return res.json()

    return _make
