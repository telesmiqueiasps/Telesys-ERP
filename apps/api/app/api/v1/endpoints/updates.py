from typing import Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Query
from app.core.config import settings
from app.schemas.updates import UpdateCheckResponse, TauriManifestResponse

router = APIRouter()

# Versão mais recente publicada do Desktop App
LATEST_DESKTOP_VERSION = "1.0.0"
LATEST_DOWNLOAD_URL = "https://pub-71c90519f08541178151f1fbb70ca9aa.r2.dev/releases/v1.0.0/Telesys_1.0.0_x64-setup.exe"
LATEST_RELEASE_NOTES = """
- Versão oficial Telesys Tecnologia v1.0.0;
- Emissão de NF-e 55, NFC-e 65 e NFS-e Padrão Nacional;
- Suporte a contingência offline com reconciliação automática;
- Módulos de Estoque, Caixa, Clientes, Fornecedores e Financeiro.
"""


def _is_newer_version(current: str, latest: str) -> bool:
    try:
        c_parts = [int(x) for x in current.split(".")]
        l_parts = [int(x) for x in latest.split(".")]
        return l_parts > c_parts
    except Exception:
        return current != latest


@router.get("/check", response_model=UpdateCheckResponse, summary="Verificar Atualizações do App Desktop")
def check_updates(
    current_version: str = Query("1.0.0", description="Versão atual instalada no Desktop"),
) -> Any:
    """
    Verifica se existe uma nova versão da aplicação Desktop disponível para download.
    """
    update_avail = _is_newer_version(current_version, LATEST_DESKTOP_VERSION)

    return UpdateCheckResponse(
        current_version=current_version,
        latest_version=LATEST_DESKTOP_VERSION,
        update_available=update_avail,
        mandatory=False,
        release_notes=LATEST_RELEASE_NOTES.strip(),
        download_url=LATEST_DOWNLOAD_URL,
        pub_date=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/tauri-manifest", response_model=TauriManifestResponse, summary="Manifesto de Atualização Nativa do Tauri")
def tauri_manifest() -> Any:
    """
    Retorna o manifesto oficial de atualização consumido pelo plugin nativo Auto-Updater do Tauri.
    """
    return TauriManifestResponse(
        version=LATEST_DESKTOP_VERSION,
        notes=LATEST_RELEASE_NOTES.strip(),
        pub_date=datetime.now(timezone.utc).isoformat(),
        platforms={
            "windows-x86_64": {
                "signature": "",
                "url": f"https://downloads.telesys.com.br/desktop/v{LATEST_DESKTOP_VERSION}/Telesys_ERP_Setup.msi.zip",
            }
        },
    )
