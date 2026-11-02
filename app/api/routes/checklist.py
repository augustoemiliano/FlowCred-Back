from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import HistoryAction
from app.models.proposal_checklist import ProposalChecklistItem
from app.models.user import User
from app.schemas.checklist import ChecklistItemPatch, ChecklistItemRead
from app.services.proposal_history import add_history

router = APIRouter(prefix="/checklist", tags=["checklist"])


@router.patch("/{item_id}", response_model=ChecklistItemRead, summary="Marcar/desmarcar item do checklist")
def patch_checklist_item(
    item_id: int,
    body: ChecklistItemPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProposalChecklistItem:
    item = db.get(ProposalChecklistItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item não encontrado")
    if item.is_done != body.is_done:
        item.is_done = body.is_done
        verb = "concluído" if body.is_done else "reaberto"
        add_history(
            db,
            proposal_id=item.proposal_id,
            user_id=current_user.id,
            action=HistoryAction.CHECKLIST_UPDATED,
            note=f"{item.title} — {verb}",
        )
        db.commit()
        db.refresh(item)
    return item
