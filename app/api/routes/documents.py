from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.document import Document
from app.models.user import User

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{document_id}/download", summary="Download seguro do documento")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> FileResponse:
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado")

    path = Path(settings.UPLOAD_DIR) / doc.storage_name
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo indisponível")

    return FileResponse(
        path=str(path.resolve()),
        media_type=doc.mime_type,
        filename=doc.display_name,
    )

