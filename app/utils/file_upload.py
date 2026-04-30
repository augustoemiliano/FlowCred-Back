import re
import uuid
from pathlib import Path

ALLOWED_MIME_TO_EXT: dict[str, str] = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
}

MAX_FILENAME_DISPLAY = 200


def extension_for_mime(mime: str) -> str | None:
    return ALLOWED_MIME_TO_EXT.get(mime.lower().strip())


def sniff_bytes_match_mime(header: bytes, mime: str) -> bool:
    if mime == "application/pdf":
        return header.startswith(b"%PDF")
    if mime == "image/png":
        return header.startswith(b"\x89PNG\r\n\x1a\n")
    if mime == "image/jpeg":
        return header.startswith(b"\xff\xd8\xff")
    return False


def sanitize_display_name(name: str) -> str:
    base = Path(name).name
    base = re.sub(r"[^\w.\-()\s\u00C0-\u024F]", "_", base, flags=re.UNICODE)
    base = base.strip()[:MAX_FILENAME_DISPLAY] or "document"
    return base


def new_storage_name(ext: str) -> str:
    safe_ext = ext if ext.startswith(".") else f".{ext}"
    return f"{uuid.uuid4().hex}{safe_ext.lower()}"
