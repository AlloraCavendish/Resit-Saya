# Purpose: File attachment storage, content-type verification, and secure file handling.
# Security: Inspects file magic bytes/Pillow; ignores client headers; prevents path traversal; isolates files by user.

import io
import uuid
from pathlib import Path
from typing import Tuple

from fastapi import HTTPException, status
from PIL import Image, UnidentifiedImageError

from app.config import settings

ALLOWED_EXTENSIONS = {
    "JPEG": "jpg",
    "PNG": "png",
    "WEBP": "webp",
}


def detect_file_type_and_extension(file_bytes: bytes) -> Tuple[str, str]:
    """Detect file type from binary contents. Returns (mime_type, extension)."""
    # Check max file size
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File exceeds maximum size limit of {settings.MAX_UPLOAD_MB} MB",
        )

    # 1. Check for PDF magic bytes
    if file_bytes.startswith(b"%PDF"):
        return "application/pdf", "pdf"

    # 2. Check for supported image formats using Pillow
    try:
        image_stream = io.BytesIO(file_bytes)
        with Image.open(image_stream) as img:
            img.verify()
            fmt = img.format
            if fmt in ALLOWED_EXTENSIONS:
                ext = ALLOWED_EXTENSIONS[fmt]
                mime = f"image/{'jpeg' if ext == 'jpg' else ext}"
                return mime, ext
    except (UnidentifiedImageError, Exception):
        pass

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid file format. Allowed file formats are JPEG, PNG, WebP, and PDF.",
    )


def save_user_file(user_id: int, file_bytes: bytes) -> Tuple[str, str]:
    """Save verified file to uploads/<user_id>/<uuid>.<ext>. Returns (relative_path, mime_type)."""
    mime_type, ext = detect_file_type_and_extension(file_bytes)

    base_upload_dir = settings.upload_path
    user_upload_dir = base_upload_dir / str(user_id)
    user_upload_dir.mkdir(parents=True, exist_ok=True)

    file_id = f"{uuid.uuid4().hex}.{ext}"
    target_path = user_upload_dir / file_id

    # Verify target path is strictly inside user_upload_dir (guard against path traversal)
    resolved_target = target_path.resolve()
    resolved_user_dir = user_upload_dir.resolve()
    if not str(resolved_target).startswith(str(resolved_user_dir)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Illegal file storage path",
        )

    with open(target_path, "wb") as f:
        f.write(file_bytes)

    # Return storage path relative to base upload directory (e.g. "1/abc.jpg")
    relative_path = f"{user_id}/{file_id}"
    return relative_path, mime_type


def resolve_user_file_path(user_id: int, relative_path: str) -> Path:
    """Safely resolve user's file on disk and verify boundaries."""
    base_upload_dir = settings.upload_path
    target = (base_upload_dir / relative_path).resolve()
    expected_user_dir = (base_upload_dir / str(user_id)).resolve()

    if not str(target).startswith(str(expected_user_dir)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to path forbidden",
        )

    if not target.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File attachment not found on disk",
        )

    return target


def delete_stored_file(relative_path: str) -> None:
    """Safely delete stored file from disk if it exists."""
    if not relative_path:
        return
    try:
        base_upload_dir = settings.upload_path
        target = (base_upload_dir / relative_path).resolve()
        if target.is_file():
            target.unlink(missing_ok=True)
    except Exception:
        # Ignore errors during file unlink to avoid blocking DB cleanup
        pass
