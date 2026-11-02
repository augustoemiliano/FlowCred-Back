from tests.conftest import ADMIN_PASSWORD


def test_health(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_login_ok_e_me(client, admin_user):
    res = client.post("/api/v1/auth/login", json={"username": "  ADMIN ", "password": ADMIN_PASSWORD})
    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["username"] == "admin"
    assert "hashed_password" not in me.json()


def test_login_senha_errada(client, admin_user):
    res = client.post("/api/v1/auth/login", json={"username": "admin", "password": "errada"})
    assert res.status_code == 401


def test_login_utilizador_inativo(client, admin_user, db):
    admin_user.is_active = False
    db.merge(admin_user)
    db.commit()
    res = client.post("/api/v1/auth/login", json={"username": "admin", "password": ADMIN_PASSWORD})
    assert res.status_code == 403


def test_rotas_protegidas_exigem_token(client):
    for path in ("/api/v1/auth/me", "/api/v1/clients", "/api/v1/proposals", "/api/v1/dashboard/summary"):
        res = client.get(path)
        assert res.status_code in (401, 403), path


def test_token_invalido(client):
    res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer nao-e-um-jwt"})
    assert res.status_code == 401


def test_cors_preflight_origem_permitida(client):
    res = client.options(
        "/api/v1/auth/login",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert res.status_code == 200
    assert res.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_lista_utilizadores(client, auth_headers):
    res = client.get("/api/v1/users", headers=auth_headers)
    assert res.status_code == 200
    assert [u["username"] for u in res.json()] == ["admin"]
