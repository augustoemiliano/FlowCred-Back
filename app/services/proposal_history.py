from sqlalchemy.orm import Session

from app.models.enums import HistoryAction, ProposalStatus
from app.models.proposal_history import ProposalHistory


def add_history(
    db: Session,
    *,
    proposal_id: int,
    user_id: int,
    action: HistoryAction,
    old_status: ProposalStatus | None = None,
    new_status: ProposalStatus | None = None,
    note: str | None = None,
) -> None:
    row = ProposalHistory(
        proposal_id=proposal_id,
        user_id=user_id,
        action=action,
        old_status=old_status,
        new_status=new_status,
        note=note,
    )
    db.add(row)
