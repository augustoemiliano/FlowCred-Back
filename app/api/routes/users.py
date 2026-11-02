from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.proposal import UserMinimal

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserMinimal], summary="Listar usuários ativos (para escolher responsável)")
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[User]:
    return list(db.scalars(select(User).where(User.is_active.is_(True)).order_by(User.username)).all())
