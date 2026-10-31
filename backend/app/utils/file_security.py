import os
import re
import uuid
from pathlib import Path
from fastapi import HTTPException, UploadFile, status
from app.core.config import settings

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
ALLOWED_MIME_TYPES = {
    "text/csv",
    "application/csv",
    "text/plain",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/octet-stream",
}


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent path traversal and unsafe characters."""
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing.",
        )
    base_name = os.path.basename(filename)
    cleaned = re.sub(r"[^a-zA-Z0-9._-]", "_", base_name)
    cleaned = cleaned.lstrip(".")
    if not cleaned:
        cleaned = "uploaded_dataset.csv"
    return cleaned


def validate_and_save_upload(upload_file: UploadFile, target_dir: str) -> tuple[str, str, int]:
    """
    Validate file extension, MIME type, size, and binary/text signature,
    then save safely inside target_dir with path traversal protection.
    Returns (saved_path, file_extension_without_dot, file_size_bytes).
    """
    safe_name = sanitize_filename(upload_file.filename or "")
    ext = Path(safe_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed types: CSV, XLSX, XLS.",
        )

    content_type = (upload_file.content_type or "").lower()
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported MIME type '{content_type}'.",
        )

    content = upload_file.file.read()
    file_size = len(content)
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    # Content signature validation: Never trust the filename alone
    if ext == ".csv":
        # Reject binary executables or ZIP/XLSX disguised as CSV if null bytes exist
        if b"\x00" in content[:4096]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content failed CSV validation: binary data detected in CSV file.",
            )
    elif ext == ".xlsx":
        # XLSX files are ZIP containers starting with PK\x03\x04
        if not content.startswith(b"PK\x03\x04"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content failed XLSX validation: invalid OOXML signature.",
            )
    elif ext == ".xls":
        # XLS BIFF8 files start with D0 CF 11 E0 or PK
        if not (content.startswith(b"\xd0\xcf\x11\xe0") or content.startswith(b"PK\x03\x04")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content failed XLS validation: invalid Excel file signature.",
            )

    target_root = Path(target_dir).resolve()
    target_root.mkdir(parents=True, exist_ok=True)

    unique_filename = f"{uuid.uuid4().hex[:12]}_{safe_name}"
    saved_path = (target_root / unique_filename).resolve()

    # Path traversal check
    if not str(saved_path).startswith(str(target_root)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path detected.",
        )

    with open(saved_path, "wb") as f:
        f.write(content)

    return str(saved_path), ext.lstrip("."), file_size

