from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.client import Client
from app.models.document import Document
from app.models.enums import HistoryAction, ProposalStatus
from app.models.proposal import Proposal
from app.models.proposal_checklist import ProposalChecklistItem
from app.models.proposal_history import ProposalHistory
from app.models.user import User
from app.schemas.checklist import ChecklistItemRead
from app.schemas.document import DocumentRead
from app.schemas.proposal import (
    ProposalCreate,
    ProposalDetailRead,
    ProposalHistoryRead,
    ProposalListResponse,
    ProposalStatusPatch,
    ProposalUpdate,
)
from app.services.checklist_seed import seed_default_checklist
from app.services.proposal_history import add_history
from app.utils.file_upload import (
    extension_for_mime,
    new_storage_name,
    sanitize_display_name,
    sniff_bytes_match_mime,
)

router = APIRouter(prefix="/proposals", tags=["proposals"])

_UPLOAD_CHUNK = 1024 * 1024


def _get_proposal_or_404(db: Session, proposal_id: int) -> Proposal:
    proposal = db.get(Proposal, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposta não encontrada")
    return proposal


def _ensure_client_and_responsible(db: Session, client_id: int, responsible_user_id: int) -> None:
    if db.get(Client, client_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    responsible = db.get(User, responsible_user_id)
    if responsible is None or not responsible.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Responsável não encontrado")


@router.post(
    "",
    response_model=ProposalDetailRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar proposta",
)
def create_proposal(
    body: ProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Proposal:
    _ensure_client_and_responsible(db, body.client_id, body.responsible_user_id)

    proposal = Proposal(
        client_id=body.client_id,
        bank=body.bank,
        property_value=body.property_value,
        financed_amount=body.financed_amount,
        status=body.status,
        responsible_user_id=body.responsible_user_id,
        next_stage_date=body.next_stage_date,
        notes=body.notes,
    )
    db.add(proposal)
    db.flush()
    seed_default_checklist(db, proposal.id)
    add_history(
        db,
        proposal_id=proposal.id,
        user_id=current_user.id,
        action=HistoryAction.CREATED,
        new_status=proposal.status,
        note=None,
    )
    db.commit()
    db.refresh(proposal)
    return proposal


@router.get("", response_model=ProposalListResponse, summary="Listar propostas")
def list_proposals(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    bank: str | None = Query(default=None, description="Filtrar por banco (parcial)"),
    status_filter: ProposalStatus | None = Query(default=None, alias="status"),
    responsible_user_id: int | None = Query(default=None, ge=1),
    client_id: int | None = Query(default=None, ge=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ProposalListResponse:
    filters = []
    if bank and (term := bank.strip()):
        filters.append(Proposal.bank.ilike(f"%{term}%"))
    if status_filter is not None:
        filters.append(Proposal.status == status_filter)
    if responsible_user_id is not None:
        filters.append(Proposal.responsible_user_id == responsible_user_id)
    if client_id is not None:
        filters.append(Proposal.client_id == client_id)

    total = db.scalar(select(func.count()).select_from(Proposal).where(*filters)) or 0
    offset = (page - 1) * page_size
    stmt = (
        select(Proposal)
        .where(*filters)
        .order_by(Proposal.created_at.desc(), Proposal.id.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = list(db.scalars(stmt).unique().all())
    return ProposalListResponse(
        items=[ProposalDetailRead.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{proposal_id}/checklist",
    response_model=list[ChecklistItemRead],
    summary="Checklist da proposta",
)
def get_checklist(
    proposal_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ProposalChecklistItem]:
    _get_proposal_or_404(db, proposal_id)
    rows = db.scalars(
        select(ProposalChecklistItem)
        .where(ProposalChecklistItem.proposal_id == proposal_id)
        .order_by(ProposalChecklistItem.sort_order, ProposalChecklistItem.id)
    ).all()
    return list(rows)


@router.get(
    "/{proposal_id}/documents",
    response_model=list[DocumentRead],
    summary="Documentos da proposta",
)
def list_documents(
    proposal_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Document]:
    _get_proposal_or_404(db, proposal_id)
    return list(
        db.scalars(
            select(Document)
            .where(Document.proposal_id == proposal_id)
            .order_by(Document.created_at.desc(), Document.id.desc())
        ).all()
    )


async def _read_limited(file: UploadFile, limit: int) -> bytes:
    """Lê o upload em blocos e aborta assim que ultrapassar o limite (evita carregar ficheiros enormes)."""
    chunks: list[bytes] = []
    size = 0
    while chunk := await file.read(_UPLOAD_CHUNK):
        size += len(chunk)
        if size > limit:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Arquivo excede o limite configurado",
            )
        chunks.append(chunk)
    return b"".join(chunks)


@router.post(
    "/{proposal_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload de documento (PDF, PNG, JPG, JPEG)",
)
async def upload_document(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...),
) -> Document:
    _get_proposal_or_404(db, proposal_id)

    mime = (file.content_type or "").split(";")[0].strip().lower()
    ext = extension_for_mime(mime)
    if ext is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Tipo de arquivo não permitido. Use PDF, PNG ou JPEG.",
        )

    raw = await _read_limited(file, settings.MAX_UPLOAD_BYTES)
    if len(raw) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arquivo vazio")

    if not sniff_bytes_match_mime(raw[:32], mime):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conteúdo do arquivo não corresponde ao tipo informado",
        )

    storage_name = new_storage_name(ext)
    display_name = sanitize_display_name(file.filename or "documento")
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / storage_name
    dest.write_bytes(raw)

    doc = Document(
        proposal_id=proposal_id,
        display_name=display_name,
        storage_name=storage_name,
        mime_type=mime,
        size_bytes=len(raw),
    )
    db.add(doc)
    add_history(
        db,
        proposal_id=proposal_id,
        user_id=current_user.id,
        action=HistoryAction.DOCUMENT_ADDED,
        note=display_name,
    )
    try:
        db.commit()
    except Exception:
        db.rollback()
        dest.unlink(missing_ok=True)
        raise
    db.refresh(doc)
    return doc


@router.get(
    "/{proposal_id}/history",
    response_model=list[ProposalHistoryRead],
    summary="Histórico da proposta",
)
def get_history(
    proposal_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ProposalHistoryRead]:
    _get_proposal_or_404(db, proposal_id)
    rows = db.scalars(
        select(ProposalHistory)
        .where(ProposalHistory.proposal_id == proposal_id)
        .order_by(ProposalHistory.created_at.desc(), ProposalHistory.id.desc())
    ).all()
    return [
        ProposalHistoryRead(
            id=h.id,
            proposal_id=h.proposal_id,
            user_id=h.user_id,
            user_username=h.user.username if h.user else None,
            action=str(h.action.value if hasattr(h.action, "value") else h.action),
            old_status=h.old_status,
            new_status=h.new_status,
            note=h.note,
            created_at=h.created_at,
        )
        for h in rows
    ]


@router.get("/{proposal_id}", response_model=ProposalDetailRead, summary="Detalhe da proposta")
def get_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Proposal:
    return _get_proposal_or_404(db, proposal_id)


@router.put("/{proposal_id}", response_model=ProposalDetailRead, summary="Atualizar proposta (sem status)")
def update_proposal(
    proposal_id: int,
    body: ProposalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Proposal:
    proposal = _get_proposal_or_404(db, proposal_id)
    _ensure_client_and_responsible(db, body.client_id, body.responsible_user_id)

    proposal.client_id = body.client_id
    proposal.bank = body.bank
    proposal.property_value = body.property_value
    proposal.financed_amount = body.financed_amount
    proposal.responsible_user_id = body.responsible_user_id
    proposal.next_stage_date = body.next_stage_date
    proposal.notes = body.notes

    add_history(
        db,
        proposal_id=proposal.id,
        user_id=current_user.id,
        action=HistoryAction.UPDATED,
        note=body.observation,
    )
    db.commit()
    db.refresh(proposal)
    return proposal


@router.patch(
    "/{proposal_id}/status",
    response_model=ProposalDetailRead,
    summary="Alterar status da proposta",
)
def patch_proposal_status(
    proposal_id: int,
    body: ProposalStatusPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Proposal:
    proposal = _get_proposal_or_404(db, proposal_id)
    old = proposal.status
    if old == body.status:
        return proposal
    proposal.status = body.status
    add_history(
        db,
        proposal_id=proposal.id,
        user_id=current_user.id,
        action=HistoryAction.STATUS_CHANGED,
        old_status=old,
        new_status=body.status,
        note=body.note,
    )
    db.commit()
    db.refresh(proposal)
    return proposal


@router.delete(
    "/{proposal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Excluir proposta (remove checklist, histórico e documentos)",
)
def delete_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Response:
    proposal = _get_proposal_or_404(db, proposal_id)
    files = [Path(settings.UPLOAD_DIR) / d.storage_name for d in proposal.documents]
    db.delete(proposal)
    db.commit()
    for path in files:
        path.unlink(missing_ok=True)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
