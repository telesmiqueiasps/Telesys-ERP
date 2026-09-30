import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from app.api import deps
from app.models.user import User
from app.models.product import Product
from app.models.product_fiscal import ProductFiscalProfile
from app.schemas.product_fiscal import (
    ProductFiscalProfileCreate,
    ProductFiscalProfileResponse,
    FiscalPendingItem,
    FiscalPendingReportResponse,
)
from app.services.product_fiscal import (
    evaluate_product_fiscal_status,
    upsert_product_fiscal_profile,
)

router = APIRouter()


@router.get("/{product_id}", response_model=Optional[ProductFiscalProfileResponse], summary="Obter Perfil Fiscal do Produto")
def get_product_fiscal_profile(
    product_id: uuid.UUID,
    company_id: uuid.UUID = Query(..., description="ID da Empresa"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retorna o perfil fiscal ativo do produto para a empresa informada.
    """
    profile = db.scalar(
        select(ProductFiscalProfile).where(
            ProductFiscalProfile.product_id == product_id,
            ProductFiscalProfile.company_id == company_id,
            ProductFiscalProfile.tenant_id == current_user.tenant_id,
        )
    )
    return profile


@router.put("/{product_id}", response_model=ProductFiscalProfileResponse, summary="Salvar / Atualizar Perfil Fiscal do Produto")
def update_product_fiscal_profile(
    product_id: uuid.UUID,
    profile_in: ProductFiscalProfileCreate,
    company_id: uuid.UUID = Query(..., description="ID da Empresa"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Cadastra ou atualiza o perfil fiscal do produto, criando histórico de vigência para auditoria.
    """
    try:
        profile = upsert_product_fiscal_profile(
            db=db,
            tenant_id=current_user.tenant_id,
            company_id=company_id,
            product_id=product_id,
            data=profile_in,
            user_id=current_user.id,
        )
        return profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/pending/report", response_model=FiscalPendingReportResponse, summary="Relatório de Pendências Fiscais de Produtos")
def get_fiscal_pending_report(
    company_id: uuid.UUID = Query(..., description="ID da Empresa"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Analisa o catálogo de produtos da empresa e diagnostica itens com pendências fiscais (NCM ausente, CEST faltando, CST nulo).
    """
    stmt = (
        select(Product)
        .options(
            selectinload(Product.fiscal_profile),
            selectinload(Product.barcodes)
        )
        .where(
            Product.company_id == company_id,
            Product.tenant_id == current_user.tenant_id,
            Product.is_active == True,
        )
        .order_by(Product.name.asc())
    )
    products = db.scalars(stmt).all()

    pending_items: List[FiscalPendingItem] = []
    ok_count = 0

    for p in products:
        reasons = evaluate_product_fiscal_status(p, p.fiscal_profile)
        barcodes_list = [b.barcode for b in p.barcodes] if p.barcodes else []

        if reasons:
            pending_items.append(
                FiscalPendingItem(
                    product_id=p.id,
                    product_name=p.name,
                    code=p.code,
                    barcodes=barcodes_list,
                    has_profile=p.fiscal_profile is not None,
                    pending_reasons=reasons,
                )
            )
        else:
            ok_count += 1

    return FiscalPendingReportResponse(
        total_products=len(products),
        pending_count=len(pending_items),
        ok_count=ok_count,
        items=pending_items,
    )
