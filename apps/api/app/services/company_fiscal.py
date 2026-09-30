import re
import uuid
from typing import List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select

from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography import x509
from cryptography.x509.oid import NameOID

from app.models.company_fiscal import (
    FiscalCompanyConfig,
    FiscalSeries,
    FiscalCertificate,
)
from app.schemas.company_fiscal import (
    FiscalCompanyConfigCreate,
    FiscalCompanyConfigUpdate,
    FiscalSeriesCreate,
    FiscalSeriesUpdate,
    FiscalCertificateMetadataResponse,
)
from app.core.crypto import encrypt_data, decrypt_data, decrypt_text


def get_or_create_company_fiscal_config(
    db: Session,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID
) -> FiscalCompanyConfig:
    """
    Retorna a configuração fiscal da empresa ou inicializa uma padrão se não existir.
    """
    config = db.scalar(
        select(FiscalCompanyConfig).where(
            FiscalCompanyConfig.company_id == company_id,
            FiscalCompanyConfig.tenant_id == tenant_id
        )
    )
    if not config:
        config = FiscalCompanyConfig(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            company_id=company_id,
            environment="HOMOLOGATION",
            tax_regime="SIMPLES_NACIONAL",
            crt=1,
            nfse_environment="HOMOLOGATION",
            contingency_mode="NONE",
            is_active=True,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def update_company_fiscal_config(
    db: Session,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    data: FiscalCompanyConfigUpdate
) -> FiscalCompanyConfig:
    """
    Atualiza os parâmetros fiscais da empresa/filial.
    """
    config = get_or_create_company_fiscal_config(db, tenant_id, company_id)

    config.environment = data.environment
    config.tax_regime = data.tax_regime
    config.crt = data.crt
    config.state_tax_number = data.state_tax_number
    config.municipal_tax_number = data.municipal_tax_number
    config.ibge_city_code = data.ibge_city_code
    config.nfc_csc_id = data.nfc_csc_id

    if data.nfc_csc_secret:
        config.nfc_csc_secret_encrypted = encrypt_data(data.nfc_csc_secret.strip())

    config.nfse_provider = data.nfse_provider
    config.nfse_environment = data.nfse_environment

    if config.contingency_mode != data.contingency_mode:
        config.contingency_mode = data.contingency_mode
        config.contingency_reason = data.contingency_reason
        if data.contingency_mode != "NONE":
            config.contingency_started_at = datetime.now()
        else:
            config.contingency_started_at = None

    db.commit()
    db.refresh(config)
    return config


def list_company_fiscal_series(
    db: Session,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID
) -> List[FiscalSeries]:
    """
    Lista todas as séries fiscais cadastradas para a empresa.
    """
    stmt = (
        select(FiscalSeries)
        .where(
            FiscalSeries.company_id == company_id,
            FiscalSeries.tenant_id == tenant_id
        )
        .order_by(FiscalSeries.doc_model, FiscalSeries.series)
    )
    return db.scalars(stmt).all()


def upsert_company_fiscal_series(
    db: Session,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    data: FiscalSeriesCreate
) -> FiscalSeries:
    """
    Cadastra ou atualiza uma série fiscal (55, 65, NFS) para a empresa.
    """
    series_obj = db.scalar(
        select(FiscalSeries).where(
            FiscalSeries.company_id == company_id,
            FiscalSeries.tenant_id == tenant_id,
            FiscalSeries.doc_model == data.doc_model,
            FiscalSeries.series == data.series,
            FiscalSeries.environment == data.environment,
        )
    )
    if series_obj:
        if data.current_number < series_obj.current_number:
            raise ValueError(
                f"Número atual ({data.current_number}) não pode ser inferior ao último número autorizado ({series_obj.current_number})."
            )
        series_obj.current_number = data.current_number
        series_obj.is_active = data.is_active
    else:
        series_obj = FiscalSeries(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            company_id=company_id,
            doc_model=data.doc_model,
            series=data.series,
            current_number=data.current_number,
            environment=data.environment,
            is_active=data.is_active,
        )
        db.add(series_obj)

    db.commit()
    db.refresh(series_obj)
    return series_obj


def increment_fiscal_series_number(
    db: Session,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    doc_model: str,
    series: int = 1,
    environment: str = "HOMOLOGATION"
) -> int:
    """
    Incrementa atomicamente e com segurança o número da nota fiscal para a próxima emissão.
    """
    series_obj = db.scalar(
        select(FiscalSeries).where(
            FiscalSeries.company_id == company_id,
            FiscalSeries.tenant_id == tenant_id,
            FiscalSeries.doc_model == doc_model,
            FiscalSeries.series == series,
            FiscalSeries.environment == environment,
        ).with_for_update()
    )
    if not series_obj:
        # Se não existe, cria série inicial número 0 e incrementa para 1
        series_obj = FiscalSeries(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            company_id=company_id,
            doc_model=doc_model,
            series=series,
            current_number=1,
            environment=environment,
            is_active=True,
        )
        db.add(series_obj)
    else:
        series_obj.current_number += 1

    db.commit()
    return series_obj.current_number


def parse_and_validate_pkcs12(file_bytes: bytes, password: str) -> Tuple[x509.Certificate, str, str, str, datetime, datetime]:
    """
    Realiza o parse criptográfico do arquivo A1 (.pfx/.p12), valida a senha e extrai os metadados do certificado X.509.
    """
    try:
        private_key, cert, additional_certs = pkcs12.load_key_and_certificates(
            file_bytes,
            password.encode("utf-8") if password else None
        )
    except Exception as e:
        raise ValueError("Senha do certificado incorreta ou arquivo PKCS12 (.pfx/.p12) corrompido.")

    if not cert:
        raise ValueError("Nenhum certificado digital X.509 válido encontrado no arquivo informando.")

    # Extrair Subject CN
    subject_cn = "Certificado Digital A1"
    cn_attrs = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
    if cn_attrs:
        subject_cn = cn_attrs[0].value

    # Tentar extrair CNPJ do Subject CN ou OIDs
    subject_cnpj = None
    cnpj_match = re.search(r"\d{14}", subject_cn.replace(".", "").replace("/", "").replace("-", ""))
    if cnpj_match:
        subject_cnpj = cnpj_match.group(0)

    # Extrair Issuer
    issuer = "AC Emissora"
    issuer_attrs = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)
    if issuer_attrs:
        issuer = issuer_attrs[0].value

    serial_number = str(cert.serial_number)
    valid_from = cert.not_valid_before_utc
    valid_until = cert.not_valid_after_utc

    return cert, subject_cn, subject_cnpj, issuer, serial_number, valid_from, valid_until


def upload_and_save_certificate(
    db: Session,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    filename: str,
    file_bytes: bytes,
    password: str
) -> FiscalCertificate:
    """
    Realiza o parse do certificado A1, criptografa a chave/senha e armazena os metadados no banco.
    """
    cert, subject_cn, subject_cnpj, issuer, serial_number, valid_from, valid_until = parse_and_validate_pkcs12(file_bytes, password)

    # Inativar certificados anteriores da empresa
    db.query(FiscalCertificate).filter(
        FiscalCertificate.company_id == company_id,
        FiscalCertificate.tenant_id == tenant_id
    ).update({"is_active": False})

    cert_obj = FiscalCertificate(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        company_id=company_id,
        filename=filename,
        certificate_data_encrypted=encrypt_data(file_bytes),
        password_encrypted=encrypt_data(password),
        subject_cn=subject_cn,
        subject_cnpj=subject_cnpj,
        issuer=issuer,
        serial_number=serial_number,
        valid_from=valid_from,
        valid_until=valid_until,
        is_active=True,
    )
    db.add(cert_obj)
    db.commit()
    db.refresh(cert_obj)
    return cert_obj


def get_active_certificate_metadata(
    db: Session,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID
) -> Optional[FiscalCertificateMetadataResponse]:
    """
    Retorna exclusivamente os metadados seguros do certificado A1 ativo para a UI (Sem expor senhas/chaves).
    """
    cert_obj = db.scalar(
        select(FiscalCertificate).where(
            FiscalCertificate.company_id == company_id,
            FiscalCertificate.tenant_id == tenant_id,
            FiscalCertificate.is_active == True
        )
    )
    if not cert_obj:
        return None

    now = datetime.now(timezone.utc)
    valid_until_utc = cert_obj.valid_until.replace(tzinfo=timezone.utc) if cert_obj.valid_until.tzinfo is None else cert_obj.valid_until
    valid_from_utc = cert_obj.valid_from.replace(tzinfo=timezone.utc) if cert_obj.valid_from.tzinfo is None else cert_obj.valid_from

    is_expired = now > valid_until_utc
    is_valid = (now >= valid_from_utc) and not is_expired
    days_until_expiration = (valid_until_utc - now).days

    return FiscalCertificateMetadataResponse(
        id=cert_obj.id,
        company_id=cert_obj.company_id,
        filename=cert_obj.filename,
        subject_cn=cert_obj.subject_cn,
        subject_cnpj=cert_obj.subject_cnpj,
        issuer=cert_obj.issuer,
        serial_number=cert_obj.serial_number,
        valid_from=cert_obj.valid_from,
        valid_until=cert_obj.valid_until,
        is_expired=is_expired,
        is_valid=is_valid,
        days_until_expiration=days_until_expiration,
        is_active=cert_obj.is_active,
    )
