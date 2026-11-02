import pytest

from app.utils.documents import is_valid_cnpj, is_valid_cpf
from tests.conftest import VALID_CNPJ, VALID_CPF, VALID_CPF_2


@pytest.mark.parametrize(
    ("value", "expected"),
    [(VALID_CPF, True), (VALID_CPF_2, True), ("52998224724", False), ("11111111111", False)],
)
def test_validacao_cpf(value, expected):
    assert is_valid_cpf(value) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(VALID_CNPJ, True), ("11222333000180", False), ("00000000000000", False)],
)
def test_validacao_cnpj(value, expected):
    assert is_valid_cnpj(value) is expected


def test_cria_cliente_normaliza_documento(client, auth_headers):
    res = client.post(
        "/api/v1/clients",
        json={
            "name": "  João ",
            "document": "529.982.247-25",
            "phone": "11 98765-4321",
            "email": "JOAO@Example.com",
        },
        headers=auth_headers,
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["document"] == VALID_CPF
    assert body["name"] == "João"
    assert body["email"] == "joao@example.com"


def test_cpf_invalido_retorna_422(client, auth_headers):
    res = client.post(
        "/api/v1/clients",
        json={"name": "X", "document": "12345678900", "phone": "11987654321", "email": "x@example.com"},
        headers=auth_headers,
    )
    assert res.status_code == 422


def test_documento_duplicado_retorna_409(client, auth_headers, make_client):
    make_client()
    res = client.post(
        "/api/v1/clients",
        json={"name": "Outro", "document": VALID_CPF, "phone": "11987654321", "email": "o@example.com"},
        headers=auth_headers,
    )
    assert res.status_code == 409


def test_busca_e_paginacao(client, auth_headers, make_client):
    make_client(VALID_CPF, name="Ana Souza", email="ana@example.com")
    make_client(VALID_CPF_2, name="Bruno Lima", email="bruno@example.com")
    make_client(VALID_CNPJ, name="Construtora XPTO", email="contato@xpto.com")

    res = client.get("/api/v1/clients?search=bruno", headers=auth_headers)
    assert [c["name"] for c in res.json()["items"]] == ["Bruno Lima"]

    res = client.get("/api/v1/clients?search=111.444", headers=auth_headers)
    assert [c["document"] for c in res.json()["items"]] == [VALID_CPF_2]

    res = client.get("/api/v1/clients?page=2&page_size=2", headers=auth_headers)
    body = res.json()
    assert body["total"] == 3
    assert len(body["items"]) == 1


def test_atualiza_cliente(client, auth_headers, make_client):
    c = make_client()
    res = client.put(
        f"/api/v1/clients/{c['id']}",
        json={**c, "name": "Maria Atualizada", "monthly_income": None},
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    assert res.json()["name"] == "Maria Atualizada"
    assert res.json()["monthly_income"] is None


def test_exclui_cliente_sem_propostas(client, auth_headers, make_client):
    c = make_client()
    assert client.delete(f"/api/v1/clients/{c['id']}", headers=auth_headers).status_code == 204
    assert client.get(f"/api/v1/clients/{c['id']}", headers=auth_headers).status_code == 404


def test_nao_exclui_cliente_com_propostas(client, auth_headers, make_proposal):
    p = make_proposal()
    res = client.delete(f"/api/v1/clients/{p['client_id']}", headers=auth_headers)
    assert res.status_code == 409
