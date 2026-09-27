from typing import Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Query
from app.core.config import settings
from app.schemas.updates import UpdateCheckResponse, TauriManifestResponse

router = APIRouter()

# Versão mais recente publicada do Desktop App
LATEST_DESKTOP_VERSION = "1.0.1"
LATEST_RELEASE_NOTES = """
- Módulo de Relatórios BI e DRE Gerencial integrado;
- Suporte a backup automático diário e exportação Cloudflare R2;
- Otimizações de velocidade no PDV e sincronização offline-first;
- Melhorias gerais de estabilidade e correção de pequenos bugs.
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
        download_url=f"https://downloads.telesys.com.br/desktop/v{LATEST_DESKTOP_VERSION}/Telesys_ERP_Setup.exe",
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
