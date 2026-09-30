import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.company_fiscal import (
    FiscalCompanyConfigUpdate,
    FiscalCompanyConfigResponse,
    FiscalSeriesCreate,
    FiscalSeriesResponse,
    FiscalCertificateMetadataResponse,
)
from app.services.company_fiscal import (
    get_or_create_company_fiscal_config,
    update_company_fiscal_config,
    list_company_fiscal_series,
    upsert_company_fiscal_series,
    upload_and_save_certificate,
    get_active_certificate_metadata,
)

router = APIRouter()


@router.get("/config", response_model=FiscalCompanyConfigResponse, summary="Obter Configurações Fiscais da Empresa")
def get_company_fiscal_config(
    company_id: uuid.UUID = Query(..., description="ID da Empresa"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retorna os parâmetros fiscais da empresa (CRT, Inscrições, CSC, NFS-e, Contingência).
    """
    return get_or_create_company_fiscal_config(db, current_user.tenant_id, company_id)


@router.put("/config", response_model=FiscalCompanyConfigResponse, summary="Atualizar Configurações Fiscais da Empresa")
def update_fiscal_config(
    data_in: FiscalCompanyConfigUpdate,
    company_id: uuid.UUID = Query(..., description="ID da Empresa"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Atualiza as configurações fiscais, ambiente de emissão e contingência da empresa.
    """
    try:
        return update_company_fiscal_config(db, current_user.tenant_id, company_id, data_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/series", response_model=List[FiscalSeriesResponse], summary="Listar Séries Fiscais da Empresa")
def list_fiscal_series(
    company_id: uuid.UUID = Query(..., description="ID da Empresa"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Lista todas as séries fiscais por modelo de documento (55, 65, NFS) cadastradas.
    """
    return list_company_fiscal_series(db, current_user.tenant_id, company_id)


@router.post("/series", response_model=FiscalSeriesResponse, summary="Cadastrar / Atualizar Série Fiscal")
def create_or_update_series(
    series_in: FiscalSeriesCreate,
    company_id: uuid.UUID = Query(..., description="ID da Empresa"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Cadastra ou atualiza uma série fiscal e seu número atual autorizado.
    """
    try:
        return upsert_company_fiscal_series(db, current_user.tenant_id, company_id, series_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/certificate", response_model=Optional[FiscalCertificateMetadataResponse], summary="Obter Metadados Seguros do Certificado A1")
def get_certificate_metadata(
    company_id: uuid.UUID = Query(..., description="ID da Empresa"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retorna exclusivamente os metadados seguros do certificado A1 ativo (Sem expor senhas ou chaves privadas).
    """
    return get_active_certificate_metadata(db, current_user.tenant_id, company_id)


@router.post("/certificate/upload", response_model=FiscalCertificateMetadataResponse, summary="Upload de Certificado Digital A1 (.pfx/.p12)")
async def upload_certificate_a1(
    company_id: uuid.UUID = Query(..., description="ID da Empresa"),
    password: str = Form(..., description="Senha do certificado PFX/P12"),
    file: UploadFile = File(..., description="Arquivo binário .pfx ou .p12"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Recebe o arquivo .pfx/.p12, valida a senha via PKCS12 parser, extrai as datas de validade/CNPJ,
    criptografa o conteúdo com Fernet e salva no servidor com segurança.
    """
    filename = file.filename or "certificado_a1.pfx"
    if not (filename.endswith(".pfx") or filename.endswith(".p12")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo inválido. Envie um arquivo com extensão .pfx ou .p12."
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arquivo de certificado vazio.")

    try:
        cert_obj = upload_and_save_certificate(
            db=db,
            tenant_id=current_user.tenant_id,
            company_id=company_id,
            filename=filename,
            file_bytes=file_bytes,
            password=password,
        )
        metadata = get_active_certificate_metadata(db, current_user.tenant_id, company_id)
        if not metadata:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao carregar metadados do certificado.")
        return metadata
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
