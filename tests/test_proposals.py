from app.constants.checklist import DEFAULT_CHECKLIST_TITLES
from tests.conftest import VALID_CPF_2


def test_cria_proposta_com_checklist_e_historico(client, auth_headers, make_proposal):
    p = make_proposal()
    assert p["status"] == "ANALISE_CREDITO"
    assert p["client"]["name"] == "Maria Silva"
    assert p["responsible"]["username"] == "admin"

    checklist = client.get(f"/api/v1/proposals/{p['id']}/checklist", headers=auth_headers).json()
    assert [i["title"] for i in checklist] == DEFAULT_CHECKLIST_TITLES

    history = client.get(f"/api/v1/proposals/{p['id']}/history", headers=auth_headers).json()
    assert [h["action"] for h in history] == ["CREATED"]
    assert history[0]["user_username"] == "admin"


def test_financiado_maior_que_imovel_retorna_422(client, auth_headers, admin_user, make_client):
    c = make_client()
    res = client.post(
        "/api/v1/proposals",
        json={
            "client_id": c["id"],
            "bank": "Itaú",
            "property_value": "100000",
            "financed_amount": "200000",
            "responsible_user_id": admin_user.id,
        },
        headers=auth_headers,
    )
    assert res.status_code == 422


def test_cliente_inexistente_retorna_404(client, auth_headers, admin_user):
    res = client.post(
        "/api/v1/proposals",
        json={
            "client_id": 999,
            "bank": "Itaú",
            "property_value": "100000",
            "financed_amount": "50000",
            "responsible_user_id": admin_user.id,
        },
        headers=auth_headers,
    )
    assert res.status_code == 404


def test_filtros_da_lista(client, auth_headers, make_client, make_proposal):
    make_proposal(bank="Caixa Econômica")
    other = make_client(VALID_CPF_2, email="b@example.com")
    p2 = make_proposal(client_id=other["id"], bank="Banco do Brasil")
    client.patch(f"/api/v1/proposals/{p2['id']}/status", json={"status": "JURIDICO"}, headers=auth_headers)

    res = client.get("/api/v1/proposals?bank=caixa", headers=auth_headers).json()
    assert res["total"] == 1 and res["items"][0]["bank"] == "Caixa Econômica"

    res = client.get("/api/v1/proposals?status=JURIDICO", headers=auth_headers).json()
    assert [p["id"] for p in res["items"]] == [p2["id"]]

    res = client.get(f"/api/v1/proposals?client_id={other['id']}", headers=auth_headers).json()
    assert res["total"] == 1
    assert res["items"][0]["client"]["id"] == other["id"]

    assert client.get("/api/v1/proposals?status=INVALIDO", headers=auth_headers).status_code == 422


def test_alterar_status_regista_historico(client, auth_headers, make_proposal):
    p = make_proposal()
    res = client.patch(
        f"/api/v1/proposals/{p['id']}/status",
        json={"status": "LAUDO", "note": "Laudo agendado"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "LAUDO"

    # Mesmo status: não gera novo evento
    client.patch(f"/api/v1/proposals/{p['id']}/status", json={"status": "LAUDO"}, headers=auth_headers)

    history = client.get(f"/api/v1/proposals/{p['id']}/history", headers=auth_headers).json()
    assert [h["action"] for h in history] == ["STATUS_CHANGED", "CREATED"]
    assert history[0]["old_status"] == "ANALISE_CREDITO"
    assert history[0]["new_status"] == "LAUDO"
    assert history[0]["note"] == "Laudo agendado"


def test_atualizar_proposta(client, auth_headers, make_proposal):
    p = make_proposal()
    payload = {
        "client_id": p["client_id"],
        "bank": "Santander",
        "property_value": "600000.00",
        "financed_amount": "400000.00",
        "responsible_user_id": p["responsible_user_id"],
        "next_stage_date": "2026-12-15",
        "notes": "Atualizada",
        "observation": "Cliente pediu troca de banco",
    }
    res = client.put(f"/api/v1/proposals/{p['id']}", json=payload, headers=auth_headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["bank"] == "Santander"
    assert body["next_stage_date"] == "2026-12-15"
    assert body["status"] == "ANALISE_CREDITO"

    history = client.get(f"/api/v1/proposals/{p['id']}/history", headers=auth_headers).json()
    assert history[0]["action"] == "UPDATED"
    assert history[0]["note"] == "Cliente pediu troca de banco"


def test_checklist_toggle(client, auth_headers, make_proposal):
    p = make_proposal()
    item = client.get(f"/api/v1/proposals/{p['id']}/checklist", headers=auth_headers).json()[0]
    res = client.patch(f"/api/v1/checklist/{item['id']}", json={"is_done": True}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["is_done"] is True

    history = client.get(f"/api/v1/proposals/{p['id']}/history", headers=auth_headers).json()
    assert history[0]["action"] == "CHECKLIST_UPDATED"

    assert client.patch("/api/v1/checklist/99999", json={"is_done": True}, headers=auth_headers).status_code == 404


def test_excluir_proposta(client, auth_headers, make_proposal):
    p = make_proposal()
    assert client.delete(f"/api/v1/proposals/{p['id']}", headers=auth_headers).status_code == 204
    assert client.get(f"/api/v1/proposals/{p['id']}", headers=auth_headers).status_code == 404
    # cliente pode agora ser excluído
    assert client.delete(f"/api/v1/clients/{p['client_id']}", headers=auth_headers).status_code == 204


def test_dashboard(client, auth_headers, make_client, make_proposal):
    make_proposal(bank="Caixa", financed_amount="100000.00")
    other = make_client(VALID_CPF_2, email="b@example.com")
    p2 = make_proposal(client_id=other["id"], bank="Itaú", financed_amount="250000.50")
    client.patch(f"/api/v1/proposals/{p2['id']}/status", json={"status": "FINALIZADO"}, headers=auth_headers)

    res = client.get("/api/v1/dashboard/summary", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["total_proposals"] == 2
    assert body["proposals_em_analise"] == 1
    assert body["proposals_finalizadas"] == 1
    assert body["proposals_juridico"] == 0
    assert float(body["total_financed_amount"]) == 350000.50
    assert body["proposals_by_bank"] == {"Caixa": 1, "Itaú": 1}
    assert body["proposals_by_status"] == {"ANALISE_CREDITO": 1, "FINALIZADO": 1}
