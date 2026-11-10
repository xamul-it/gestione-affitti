"""
Temporary uploads between "read" and "confirm" (visura import, single upload
point): the file stays in the tenant's temp_uploads/<token>/ and is re-read
server side on confirm, so the confirmation can't point at another document.
Uploads older than 24h are purged at each new upload.
"""
import io
import json
import re
import shutil
import time
import uuid
from pathlib import Path
from typing import Optional, Tuple

from app.core.file_storage import file_storage

TEMP_TTL_SECONDS = 24 * 3600
TOKEN_RE = re.compile(r"^[0-9a-f]{32}$")
_META = "meta.json"


def temp_root(tenant_schema: str) -> Path:
    return file_storage._get_tenant_path(tenant_schema) / "temp_uploads"


def purge_old_uploads(tenant_schema: str) -> None:
    root = temp_root(tenant_schema)
    if not root.exists():
        return
    cutoff = time.time() - TEMP_TTL_SECONDS
    for d in root.iterdir():
        if d.is_dir() and TOKEN_RE.match(d.name) and d.stat().st_mtime < cutoff:
            shutil.rmtree(d, ignore_errors=True)


def token_dir(tenant_schema: str, token: str) -> Optional[Path]:
    if not TOKEN_RE.match(token or ""):
        return None
    d = temp_root(tenant_schema) / token
    return d if d.is_dir() else None


def salva(tenant_schema: str, contenuto: bytes, nome_file: str, mime_type: Optional[str] = None) -> str:
    """Store the upload with its metadata; returns the token."""
    purge_old_uploads(tenant_schema)
    token = uuid.uuid4().hex
    file_storage.save_temp_file(io.BytesIO(contenuto), token, nome_file, tenant_schema)
    scrivi_meta(tenant_schema, token, {"nome_file": nome_file, "mime_type": mime_type})
    return token


def scrivi_meta(tenant_schema: str, token: str, meta: dict) -> None:
    d = temp_root(tenant_schema) / token
    (d / _META).write_text(json.dumps(meta))


def leggi(tenant_schema: str, token: str) -> Optional[Tuple[bytes, dict]]:
    """(content, metadata) of the upload, None if expired or unknown."""
    d = token_dir(tenant_schema, token)
    if d is None:
        return None
    files = sorted(p for p in d.iterdir() if p.is_file() and p.name != _META)
    if not files:
        return None
    meta_path = d / _META
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    return files[0].read_bytes(), meta


def elimina(tenant_schema: str, token: str) -> None:
    d = token_dir(tenant_schema, token)
    if d is not None:
        shutil.rmtree(d, ignore_errors=True)
