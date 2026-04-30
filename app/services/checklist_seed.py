from sqlalchemy.orm import Session

from app.constants.checklist import DEFAULT_CHECKLIST_TITLES
from app.models.proposal_checklist import ProposalChecklistItem


def seed_default_checklist(db: Session, proposal_id: int) -> None:
    for order, title in enumerate(DEFAULT_CHECKLIST_TITLES):
        db.add(
            ProposalChecklistItem(
                proposal_id=proposal_id,
                title=title,
                is_done=False,
                sort_order=order,
            )
        )
