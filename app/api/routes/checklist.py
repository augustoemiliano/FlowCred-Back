from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.proposal_checklist import ProposalChecklistItem
from app.models.user import User
from app.schemas.checklist import ChecklistItemPatch, ChecklistItemRead

router = APIRouter(prefix="/checklist", tags=["checklist"])


@router.patch("/{item_id}", response_model=ChecklistItemRead, summary="Marcar/desmarcar item do checklist")
def patch_checklist_item(
    item_id: int,
    body: ChecklistItemPatch,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ProposalChecklistItem:
    item = db.get(ProposalChecklistItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item não encontrado")
    item.is_done = body.is_done
    db.commit()
    db.refresh(item)
    return item
