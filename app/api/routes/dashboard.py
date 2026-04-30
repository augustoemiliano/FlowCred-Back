from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import ProposalStatus
from app.models.proposal import Proposal
from app.models.user import User
from app.schemas.dashboard import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary, summary="Indicadores do dashboard")
def dashboard_summary(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DashboardSummary:
    total = db.scalar(select(func.count()).select_from(Proposal)) or 0
    em_analise = (
        db.scalar(
            select(func.count()).select_from(Proposal).where(Proposal.status == ProposalStatus.ANALISE_CREDITO)
        )
        or 0
    )
    juridico = (
        db.scalar(
            select(func.count()).select_from(Proposal).where(Proposal.status == ProposalStatus.JURIDICO)
        )
        or 0
    )
    finalizadas = (
        db.scalar(
            select(func.count()).select_from(Proposal).where(Proposal.status == ProposalStatus.FINALIZADO)
        )
        or 0
    )
    total_financed = db.scalar(select(func.coalesce(func.sum(Proposal.financed_amount), 0))) or Decimal("0")

    status_rows = db.execute(select(Proposal.status, func.count(Proposal.id)).group_by(Proposal.status)).all()
    proposals_by_status: dict[str, int] = {}
    for st, cnt in status_rows:
        key = st.value if isinstance(st, ProposalStatus) else str(st)
        proposals_by_status[key] = int(cnt)

    bank_rows = db.execute(select(Proposal.bank, func.count(Proposal.id)).group_by(Proposal.bank)).all()
    proposals_by_bank: dict[str, int] = {str(b): int(c) for b, c in bank_rows}

    return DashboardSummary(
        total_proposals=int(total),
        proposals_em_analise=int(em_analise),
        proposals_juridico=int(juridico),
        proposals_finalizadas=int(finalizadas),
        total_financed_amount=Decimal(str(total_financed)),
        proposals_by_status=proposals_by_status,
        proposals_by_bank=proposals_by_bank,
    )
