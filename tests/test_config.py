import pytest

from app.core.config import Settings


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("postgres://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
        ("postgresql://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("postgresql+psycopg://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("sqlite:////app/data/db.local", "sqlite:////app/data/db.local"),
    ],
)
def test_database_url_normalizada_para_psycopg(raw, expected):
    uri = Settings(DATABASE_URL=raw, JWT_SECRET_KEY="x" * 16).SQLALCHEMY_DATABASE_URI
    assert uri == expected


def test_docs_ligados_por_padrao(client):
    assert client.get("/openapi.json").status_code == 200
