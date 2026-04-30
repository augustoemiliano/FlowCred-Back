from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.client import Client
from app.models.user import User
from app.schemas.client import ClientCreate, ClientListResponse, ClientRead, ClientUpdate

router = APIRouter(prefix="/clients", tags=["clients"])


def _search_filter(search: str | None):
    if not search or not (term := search.strip()):
        return None
    digits = "".join(c for c in term if c.isdigit())
    parts = [
        Client.name.ilike(f"%{term}%"),
        Client.email.ilike(f"%{term}%"),
    ]
    if digits:
        parts.append(Client.document.contains(digits))
    return or_(*parts)


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED, summary="Criar cliente")
def create_client(
    body: ClientCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Client:
    client = Client(
        name=body.name,
        document=body.document,
        phone=body.phone,
        email=str(body.email).lower().strip(),
        monthly_income=body.monthly_income,
        notes=body.notes,
    )
    db.add(client)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe cliente com este CPF/CNPJ",
        ) from exc
    db.refresh(client)
    return client


@router.get("", response_model=ClientListResponse, summary="Listar clientes com busca e paginação")
def list_clients(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    search: str | None = Query(
        default=None,
        description="Busca por nome, e-mail ou CPF/CNPJ (parcial)",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ClientListResponse:
    base = select(Client)
    count_stmt = select(func.count()).select_from(Client)
    filt = _search_filter(search)
    if filt is not None:
        base = base.where(filt)
        count_stmt = count_stmt.where(filt)

    total = db.scalar(count_stmt) or 0
    offset = (page - 1) * page_size
    stmt = base.order_by(Client.created_at.desc()).offset(offset).limit(page_size)
    items = list(db.scalars(stmt).all())
    return ClientListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{client_id}", response_model=ClientRead, summary="Detalhe do cliente")
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Client:
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    return client


@router.put("/{client_id}", response_model=ClientRead, summary="Atualizar cliente")
def update_client(
    client_id: int,
    body: ClientUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Client:
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    client.name = body.name
    client.document = body.document
    client.phone = body.phone
    client.email = str(body.email).lower().strip()
    client.monthly_income = body.monthly_income
    client.notes = body.notes
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe cliente com este CPF/CNPJ",
        ) from exc
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir cliente")
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    db.delete(client)
    db.commit()
