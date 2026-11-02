"""Dados de demonstração idempotentes para dev (clientes + propostas em várias etapas).

Ativado por SEED_DEV_DATA=1 no .env. Correr depois de `alembic upgrade head` e `ensure_admin`.
Cada cliente demo é identificado pelo CPF/CNPJ: se já existir, nada é recriado.
"""

import sys
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.client import Client
from app.models.enums import HistoryAction, ProposalStatus
from app.models.proposal import Proposal
from app.models.proposal_checklist import ProposalChecklistItem
from app.models.user import User
from app.services.checklist_seed import seed_default_checklist
from app.services.proposal_history import add_history

# Mantidos para compatibilidade com o README e o smoke test.
DEMO_DOCUMENT = "52998224725"
DEMO_EMAIL = "cliente.demo@flowcred.local"
DEMO_BANK = "Banco demonstração (FlowCred seed)"

# Ordem do fluxo usada para gerar o histórico até à etapa final de cada proposta.
FLOW = [
    ProposalStatus.ANALISE_CREDITO,
    ProposalStatus.LAUDO,
    ProposalStatus.JURIDICO,
    ProposalStatus.CONTRATO,
    ProposalStatus.REGISTRO,
    ProposalStatus.PAGAMENTO_VENDEDOR,
    ProposalStatus.FINALIZADO,
]


@dataclass(frozen=True)
class DemoCase:
    name: str
    document: str
    email: str
    phone: str
    income: str | None
    bank: str
    property_value: str
    financed_amount: str
    status: ProposalStatus
    checklist_done: int
    next_stage_in_days: int | None


DEMO_CASES: list[DemoCase] = [
    DemoCase(
        "Cliente demonstração FlowCred",
        DEMO_DOCUMENT,
        DEMO_EMAIL,
        "11987654321",
        "5500.00",
        DEMO_BANK,
        "450000.00",
        "320000.00",
        ProposalStatus.ANALISE_CREDITO,
        1,
        5,
    ),
    DemoCase(
        "Ana Paula Ribeiro",
        "12345678909",
        "ana.ribeiro@example.com",
        "11991234567",
        "12800.00",
        "Caixa Econômica Federal",
        "680000.00",
        "476000.00",
        ProposalStatus.LAUDO,
        3,
        3,
    ),
    DemoCase(
        "Carlos Eduardo Menezes",
        "98765432100",
        "carlos.menezes@example.com",
        "21998765432",
        "9400.00",
        "Itaú",
        "520000.00",
        "390000.00",
        ProposalStatus.JURIDICO,
        5,
        7,
    ),
    DemoCase(
        "Fernanda Lima Costa",
        "45678912364",
        "fernanda.costa@example.com",
        "31997654321",
        "15200.00",
        "Bradesco",
        "890000.00",
        "600000.00",
        ProposalStatus.CONTRATO,
        6,
        10,
    ),
    DemoCase(
        "Rafael Souza Martins",
        "32165498791",
        "rafael.martins@example.com",
        "41996543210",
        "7300.00",
        "Santander",
        "360000.00",
        "250000.00",
        ProposalStatus.FINALIZADO,
        10,
        None,
    ),
    DemoCase(
        "Construtora Horizonte Ltda",
        "12345678000195",
        "financeiro@horizonte.example.com",
        "1133224455",
        None,
        "Banco do Brasil",
        "1250000.00",
        "800000.00",
        ProposalStatus.CANCELADO,
        2,
        None,
    ),
]


def _create_case(db: Session, case: DemoCase, admin: User) -> None:
    client = Client(
        name=case.name,
        document=case.document,
        phone=case.phone,
        email=case.email,
        monthly_income=Decimal(case.income) if case.income else None,
        notes="Criado por SEED_DEV_DATA (dados de demonstração).",
    )
    db.add(client)
    db.flush()

    proposal = Proposal(
        client_id=client.id,
        bank=case.bank,
        property_value=Decimal(case.property_value),
        financed_amount=Decimal(case.financed_amount),
        status=ProposalStatus.ANALISE_CREDITO,
        responsible_user_id=admin.id,
        next_stage_date=(date.today() + timedelta(days=case.next_stage_in_days))
        if case.next_stage_in_days is not None
        else None,
        notes="Proposta de demonstração (SEED_DEV_DATA).",
    )
    db.add(proposal)
    db.flush()
    seed_default_checklist(db, proposal.id)
    add_history(
        db,
        proposal_id=proposal.id,
        user_id=admin.id,
        action=HistoryAction.CREATED,
        new_status=ProposalStatus.ANALISE_CREDITO,
    )

    # Percorre o fluxo até à etapa final, registando cada movimentação.
    if case.status == ProposalStatus.CANCELADO:
        path = [ProposalStatus.CANCELADO]
    else:
        path = FLOW[1 : FLOW.index(case.status) + 1]
    previous = ProposalStatus.ANALISE_CREDITO
    for step in path:
        add_history(
            db,
            proposal_id=proposal.id,
            user_id=admin.id,
            action=HistoryAction.STATUS_CHANGED,
            old_status=previous,
            new_status=step,
            note="Cliente desistiu da compra." if step == ProposalStatus.CANCELADO else None,
        )
        previous = step
    proposal.status = case.status

    db.flush()
    items = db.scalars(
        select(ProposalChecklistItem)
        .where(ProposalChecklistItem.proposal_id == proposal.id)
        .order_by(ProposalChecklistItem.sort_order)
    ).all()
    for item in items[: case.checklist_done]:
        item.is_done = True


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

        created = 0
        for case in DEMO_CASES:
            if db.scalar(select(Client).where(Client.document == case.document)) is not None:
                continue
            _create_case(db, case, admin)
            created += 1
        db.commit()
        print(f"Demo data: {created} client(s)/proposal(s) created, {len(DEMO_CASES) - created} already present.")
        return 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
