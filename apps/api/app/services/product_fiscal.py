import json
import uuid
from typing import List, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.product import Product
from app.models.product_fiscal import ProductFiscalProfile, ProductFiscalProfileHistory
from app.schemas.product_fiscal import (
    ProductFiscalProfileCreate,
    ProductFiscalProfileUpdate,
    FiscalPendingItem,
)


def evaluate_product_fiscal_status(product: Product, profile: Optional[ProductFiscalProfile]) -> List[str]:
    """
    Avalia os parâmetros fiscais de um produto e retorna uma lista de pendências/inconsistências fiscais.
    """
    reasons = []

    if not profile:
        reasons.append("Perfil fiscal não cadastrado para o produto nesta empresa.")
        return reasons

    # 1. Validação do NCM
    if not profile.ncm:
        reasons.append("NCM ausente (obrigatório 8 dígitos).")
    elif len(profile.ncm.replace(".", "").strip()) != 8:
        reasons.append(f"NCM inválido ({profile.ncm}). Deve possuir exatamente 8 dígitos.")

    # 2. Validação do CST / CSOSN
    if not profile.cst_csosn:
        reasons.append("CST/CSOSN não informado.")
    else:
        # Se for ST e não tiver CEST
        st_codes = ["201", "202", "203", "500", "10", "30", "70", "90"]
        if profile.cst_csosn in st_codes and not profile.cest:
            reasons.append(f"CEST ausente para produto com Substituição Tributária (CSOSN/CST {profile.cst_csosn}).")

    # 3. Validação dos CFOPs padrão
    if not profile.cfop_default_inside or len(profile.cfop_default_inside.strip()) != 4:
        reasons.append("CFOP Estadual padrão ausente ou inválido.")
    if not profile.cfop_default_outside or len(profile.cfop_default_outside.strip()) != 4:
        reasons.append("CFOP Interestadual padrão ausente ou inválido.")

    # 4. Unidades de medida
    if not profile.unit_commercial:
        reasons.append("Unidade comercial de medida não informada.")
    if not profile.unit_taxable:
        reasons.append("Unidade tributável de medida não informada.")

    # 5. GTIN
    if profile.gtin_commercial and profile.gtin_commercial.upper() != "SEM GTIN":
        clean_gtin = profile.gtin_commercial.strip()
        if len(clean_gtin) not in (8, 12, 13, 14):
            reasons.append(f"GTIN Comercial inválido ({clean_gtin}). Deve ter 8, 12, 13 ou 14 dígitos ou 'SEM GTIN'.")

    return reasons


def upsert_product_fiscal_profile(
    db: Session,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    product_id: uuid.UUID,
    data: ProductFiscalProfileCreate,
    user_id: Optional[uuid.UUID] = None,
) -> ProductFiscalProfile:
    """
    Cria ou atualiza o perfil fiscal do produto, gerando versão histórica para auditoria (vigência).
    """
    product = db.scalar(
        select(Product).where(
            Product.id == product_id,
            Product.company_id == company_id,
            Product.tenant_id == tenant_id
        )
    )
    if not product:
        raise ValueError("Produto não encontrado na empresa especificada.")

    existing_profile = db.scalar(
        select(ProductFiscalProfile).where(
            ProductFiscalProfile.product_id == product_id,
            ProductFiscalProfile.company_id == company_id,
            ProductFiscalProfile.tenant_id == tenant_id
        )
    )

    now = datetime.now()

    if existing_profile:
        # 1. Registrar Snapshot da versão anterior no histórico imutável
        history_snapshot = {
            "profile_id": str(existing_profile.id),
            "ncm": existing_profile.ncm,
            "cest": existing_profile.cest,
            "origin": existing_profile.origin,
            "gtin_commercial": existing_profile.gtin_commercial,
            "gtin_taxable": existing_profile.gtin_taxable,
            "unit_commercial": existing_profile.unit_commercial,
            "unit_taxable": existing_profile.unit_taxable,
            "conversion_factor": float(existing_profile.conversion_factor),
            "cst_csosn": existing_profile.cst_csosn,
            "cfop_default_inside": existing_profile.cfop_default_inside,
            "cfop_default_outside": existing_profile.cfop_default_outside,
            "icms_rate": float(existing_profile.icms_rate),
            "icms_st_rate": float(existing_profile.icms_st_rate),
            "fcp_rate": float(existing_profile.fcp_rate),
            "ipi_cst": existing_profile.ipi_cst,
            "ipi_rate": float(existing_profile.ipi_rate),
            "pis_cst": existing_profile.pis_cst,
            "pis_rate": float(existing_profile.pis_rate),
            "cofins_cst": existing_profile.cofins_cst,
            "cofins_rate": float(existing_profile.cofins_rate),
            "ibs_cst": existing_profile.ibs_cst,
            "ibs_rate": float(existing_profile.ibs_rate),
            "cbs_cst": existing_profile.cbs_cst,
            "cbs_rate": float(existing_profile.cbs_rate),
            "effective_from": existing_profile.effective_from.isoformat(),
            "effective_to": now.isoformat(),
        }

        history = ProductFiscalProfileHistory(
            id=uuid.uuid4(),
            profile_id=existing_profile.id,
            product_id=product_id,
            company_id=company_id,
            changed_by_user_id=user_id,
            snapshot_json=json.dumps(history_snapshot, ensure_ascii=False),
            created_at=now,
        )
        db.add(history)

        # 2. Atualizar o perfil com a nova vigência
        existing_profile.ncm = data.ncm
        existing_profile.cest = data.cest
        existing_profile.origin = data.origin
        existing_profile.gtin_commercial = data.gtin_commercial
        existing_profile.gtin_taxable = data.gtin_taxable
        existing_profile.unit_commercial = data.unit_commercial
        existing_profile.unit_taxable = data.unit_taxable
        existing_profile.conversion_factor = data.conversion_factor
        existing_profile.cst_csosn = data.cst_csosn
        existing_profile.cfop_default_inside = data.cfop_default_inside
        existing_profile.cfop_default_outside = data.cfop_default_outside
        existing_profile.icms_rate = data.icms_rate
        existing_profile.icms_st_rate = data.icms_st_rate
        existing_profile.fcp_rate = data.fcp_rate
        existing_profile.ipi_cst = data.ipi_cst
        existing_profile.ipi_rate = data.ipi_rate
        existing_profile.pis_cst = data.pis_cst
        existing_profile.pis_rate = data.pis_rate
        existing_profile.cofins_cst = data.cofins_cst
        existing_profile.cofins_rate = data.cofins_rate
        existing_profile.ibs_cst = data.ibs_cst
        existing_profile.ibs_rate = data.ibs_rate
        existing_profile.cbs_cst = data.cbs_cst
        existing_profile.cbs_rate = data.cbs_rate
        existing_profile.effective_from = now
        existing_profile.source_reference = data.source_reference

        profile = existing_profile
    else:
        profile = ProductFiscalProfile(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            company_id=company_id,
            product_id=product_id,
            ncm=data.ncm,
            cest=data.cest,
            origin=data.origin,
            gtin_commercial=data.gtin_commercial,
            gtin_taxable=data.gtin_taxable,
            unit_commercial=data.unit_commercial,
            unit_taxable=data.unit_taxable,
            conversion_factor=data.conversion_factor,
            cst_csosn=data.cst_csosn,
            cfop_default_inside=data.cfop_default_inside,
            cfop_default_outside=data.cfop_default_outside,
            icms_rate=data.icms_rate,
            icms_st_rate=data.icms_st_rate,
            fcp_rate=data.fcp_rate,
            ipi_cst=data.ipi_cst,
            ipi_rate=data.ipi_rate,
            pis_cst=data.pis_cst,
            pis_rate=data.pis_rate,
            cofins_cst=data.cofins_cst,
            cofins_rate=data.cofins_rate,
            ibs_cst=data.ibs_cst,
            ibs_rate=data.ibs_rate,
            cbs_cst=data.cbs_cst,
            cbs_rate=data.cbs_rate,
            effective_from=now,
            source_reference=data.source_reference,
            is_active=True,
        )
        db.add(profile)

    # Atualizar NCM e CEST espelhados no produto para atalho simples se existirem
    if data.ncm:
        product.ncm = data.ncm
    if data.cest:
        product.cest = data.cest

    db.commit()
    db.refresh(profile)
    return profile
