import os
import uuid
from typing import List, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.services.r2_storage import r2_storage

router = APIRouter()

BACKUP_STORAGE_DIR = os.path.join(os.getcwd(), "storage", "backups")
os.makedirs(BACKUP_STORAGE_DIR, exist_ok=True)


@router.post("/upload", summary="Enviar Backup para Armazenamento na Nuvem / Cloudflare R2")
async def upload_cloud_backup(
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Recebe um arquivo de backup compactado (.zip ou .json) enviado pelo app Desktop e armazena na nuvem (Cloudflare R2 / Disk).
    """
    if not file.filename.endswith((".zip", ".json", ".bak")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de arquivo inválido. Permitidos: .zip, .json, .bak"
        )

    tenant_dir = os.path.join(BACKUP_STORAGE_DIR, str(current_user.tenant_id))
    os.makedirs(tenant_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_filename = f"backup_{timestamp}_{uuid.uuid4().hex[:6]}_{file.filename}"
    file_path = os.path.join(tenant_dir, safe_filename)

    content = await file.read()
    
    # 1. Salvar backup local do servidor
    with open(file_path, "wb") as f:
        f.write(content)

    # 2. Enviar para Bucket Cloudflare R2 (se credenciais S3/R2 configuradas no .env)
    object_key = f"backups/{current_user.tenant_id}/{safe_filename}"
    uploaded_r2 = r2_storage.upload_file(content, object_key, content_type="application/json")

    return {
        "id": str(uuid.uuid4()),
        "tenant_id": str(current_user.tenant_id),
        "filename": safe_filename,
        "size_bytes": len(content),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "storage_mode": "CLOUDFLARE_R2" if uploaded_r2 else "LOCAL_DISK",
        "status": "STORED",
    }


@router.get("/cloud", summary="Listar Backups Salvos na Nuvem")
def list_cloud_backups(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retorna a lista de arquivos de backup salvos no servidor/nuvem para este tenant.
    """
    tenant_dir = os.path.join(BACKUP_STORAGE_DIR, str(current_user.tenant_id))
    if not os.path.exists(tenant_dir):
        return []

    backups = []
    for filename in sorted(os.listdir(tenant_dir), reverse=True):
        file_path = os.path.join(tenant_dir, filename)
        if os.path.isfile(file_path):
            stat = os.stat(file_path)
            backups.append({
                "id": filename,
                "filename": filename,
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "type": "CLOUD",
                "storage_engine": "Cloudflare R2 / Storage" if r2_storage.is_configured else "Local Disk",
            })

    return backups


@router.get("/cloud/{filename}/download", summary="Baixar Arquivo de Backup")
def download_cloud_backup(
    filename: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Faz o download do arquivo de backup armazenado na nuvem.
    """
    tenant_dir = os.path.join(BACKUP_STORAGE_DIR, str(current_user.tenant_id))
    file_path = os.path.join(tenant_dir, filename)

    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo de backup não encontrado."
        )

    return FileResponse(path=file_path, filename=filename, media_type="application/octet-stream")
