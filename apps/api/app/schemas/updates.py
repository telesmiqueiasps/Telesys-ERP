from typing import Optional, Dict, Any
from pydantic import BaseModel


class UpdateCheckResponse(BaseModel):
    current_version: str
    latest_version: str
    update_available: bool
    mandatory: bool = False
    release_notes: str
    download_url: Optional[str] = None
    pub_date: str


class TauriManifestResponse(BaseModel):
    version: str
    notes: str
    pub_date: str
    platforms: Dict[str, Any]
