"""Dados de demonstração idempotentes para dev (cliente + proposta).

Ativado por SEED_DEV_DATA=1 no .env. Correr depois de ensure_admin e alembic.
"""

import sys
from decimal import Decimal

from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.client import Client
from app.models.enums import HistoryAction, ProposalStatus
from app.models.proposal import Proposal
from app.models.user import User
from app.services.checklist_seed import seed_default_checklist
from app.services.proposal_history import add_history

# CPF válido (11 dígitos) — marcador fixo para idempotência
DEMO_DOCUMENT = "52998224725"
DEMO_EMAIL = "cliente.demo@flowcred.local"
DEMO_BANK = "Banco demonstração (FlowCred seed)"


def main() -> int:
    if not settings.SEED_DEV_DATA:
        return 0

    db = SessionLocal()
    try:
        admin = db.scalar(
            select(User).where(User.is_superuser.is_(True)).order_by(User.id).limit(1),
        )
        if admin is None:
            print(
                "No superuser found. Run ensure_admin with INITIAL_ADMIN_* first.",
                file=sys.stderr,
            )
            return 1

        client = db.scalar(select(Client).where(Client.document == DEMO_DOCUMENT))
        if client is None:
            client = Client(
                name="Cliente demonstração FlowCred",
                document=DEMO_DOCUMENT,
                phone="11987654321",
                email=DEMO_EMAIL,
                monthly_income=Decimal("5500.00"),
                notes="Criado por SEED_DEV_DATA (git clone / dev). Pode editar ou apagar.",
            )
            db.add(client)
            db.commit()
            db.refresh(client)
            print("Demo client created.")
        else:
            print("Demo client already present.")

        seeded_proposal = db.scalar(select(Proposal).where(Proposal.bank == DEMO_BANK).limit(1))
        if seeded_proposal is not None:
            print("Demo proposal already present.")
            return 0

        proposal = Proposal(
            client_id=client.id,
            bank=DEMO_BANK,
            property_value=Decimal("450000.00"),
            financed_amount=Decimal("320000.00"),
            status=ProposalStatus.ANALISE_CREDITO,
            responsible_user_id=admin.id,
            next_stage_date=None,
            notes="Proposta exemplo (SEED_DEV_DATA).",
        )
        db.add(proposal)
        db.flush()
        seed_default_checklist(db, proposal.id)
        add_history(
            db,
            proposal_id=proposal.id,
            user_id=admin.id,
            action=HistoryAction.CREATED,
            new_status=proposal.status,
            note=None,
        )
        db.commit()
        print("Demo proposal created.")
        return 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
