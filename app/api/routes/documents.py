from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.document import Document
from app.models.enums import HistoryAction
from app.models.user import User
from app.services.proposal_history import add_history

router = APIRouter(prefix="/documents", tags=["documents"])


def _get_document_or_404(db: Session, document_id: int) -> Document:
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado")
    return doc


@router.get("/{document_id}/download", summary="Download seguro do documento")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> FileResponse:
    doc = _get_document_or_404(db, document_id)

    path = Path(settings.UPLOAD_DIR) / doc.storage_name
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo indisponível")

    return FileResponse(
        path=str(path.resolve()),
        media_type=doc.mime_type,
        filename=doc.display_name,
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Excluir documento",
)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    doc = _get_document_or_404(db, document_id)
    path = Path(settings.UPLOAD_DIR) / doc.storage_name
    add_history(
        db,
        proposal_id=doc.proposal_id,
        user_id=current_user.id,
        action=HistoryAction.DOCUMENT_REMOVED,
        note=doc.display_name,
    )
    db.delete(doc)
    db.commit()
    path.unlink(missing_ok=True)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
