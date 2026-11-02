from sqlalchemy import func, select

from app.core.config import settings
from app.models.client import Client
from app.models.proposal import Proposal
from app.scripts import seed_dev_demo


def test_seed_e_idempotente(monkeypatch, admin_user, db, client, auth_headers):
    monkeypatch.setattr(settings, "SEED_DEV_DATA", True)
    assert seed_dev_demo.main() == 0
    assert seed_dev_demo.main() == 0

    n_cases = len(seed_dev_demo.DEMO_CASES)
    assert db.scalar(select(func.count()).select_from(Client)) == n_cases
    assert db.scalar(select(func.count()).select_from(Proposal)) == n_cases

    summary = client.get("/api/v1/dashboard/summary", headers=auth_headers).json()
    assert summary["total_proposals"] == n_cases
    assert summary["proposals_finalizadas"] == 1

    # A proposta finalizada tem o histórico completo do fluxo
    finalizada = client.get("/api/v1/proposals?status=FINALIZADO", headers=auth_headers).json()["items"][0]
    history = client.get(f"/api/v1/proposals/{finalizada['id']}/history", headers=auth_headers).json()
    assert history[0]["new_status"] == "FINALIZADO"
    assert history[-1]["action"] == "CREATED"
    assert len(history) == len(seed_dev_demo.FLOW)


def test_seed_desligado_nao_faz_nada(monkeypatch, admin_user, db):
    monkeypatch.setattr(settings, "SEED_DEV_DATA", False)
    assert seed_dev_demo.main() == 0
    assert db.scalar(select(func.count()).select_from(Client)) == 0
