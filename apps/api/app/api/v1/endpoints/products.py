from typing import List, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.api import deps
from app.models.user import User
from app.models.product import Product, ProductCategory, ProductUnit, ProductBarcode
from app.schemas.product import (
    ProductCreate,
    ProductResponse,
    ProductDetailResponse,
    ProductUpdate,
    CategoryCreate,
    CategoryResponse,
    UnitResponse
)

router = APIRouter()


# Units Endpoints
@router.get("/units", response_model=List[UnitResponse], summary="Listar Unidades de Medida")
def list_units(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retorna o catálogo de unidades de medida disponíveis (UN, KG, CX, LT, M, etc.).
    """
    units = db.scalars(select(ProductUnit).order_by(ProductUnit.code)).all()
    return units


# Categories Endpoints
@router.get("/categories", response_model=List[CategoryResponse], summary="Listar Categorias de Produtos")
def list_categories(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Lista todas as categorias de produtos pertencentes ao Tenant.
    """
    categories = db.scalars(
        select(ProductCategory).where(ProductCategory.tenant_id == current_user.tenant_id)
    ).all()
    return categories


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED, summary="Criar Categoria")
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("produtos.editar"))
) -> Any:
    """
    Cria uma nova categoria de produto.
    """
    tenant_id = category_in.tenant_id or current_user.tenant_id

    category = ProductCategory(
        tenant_id=tenant_id,
        company_id=category_in.company_id,
        name=category_in.name,
        description=category_in.description,
        is_active=category_in.is_active
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


# Products Endpoints
@router.get("", response_model=List[ProductDetailResponse], summary="Listar Produtos")
def list_products(
    company_id: Optional[UUID] = Query(None, description="Filtrar por ID da empresa"),
    category_id: Optional[UUID] = Query(None, description="Filtrar por categoria"),
    query: Optional[str] = Query(None, description="Buscar por nome, código ou código de barras"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("produtos.visualizar"))
) -> Any:
    """
    Lista os produtos cadastrados com suporte a busca textual por nome, SKU ou código de barras.
    """
    stmt = select(Product).where(Product.tenant_id == current_user.tenant_id)

    if company_id:
        stmt = stmt.where(Product.company_id == company_id)

    if category_id:
        stmt = stmt.where(Product.category_id == category_id)

    if query:
        search_pattern = f"%{query.strip()}%"
        stmt = stmt.outerjoin(ProductBarcode).where(
            or_(
                Product.name.ilike(search_pattern),
                Product.code.ilike(search_pattern),
                ProductBarcode.barcode.ilike(search_pattern)
            )
        ).distinct()

    stmt = stmt.order_by(Product.name)
    products = db.scalars(stmt.offset(skip).limit(limit)).all()
    return products


@router.post("", response_model=ProductDetailResponse, status_code=status.HTTP_201_CREATED, summary="Cadastrar Produto")
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("produtos.editar"))
) -> Any:
    """
    Cadastra um novo produto com preço, custo, unidade e códigos de barras.
    """
    if not current_user.is_superuser and product_in.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Não é permitido cadastrar produtos em outro tenant")

    product = Product(
        tenant_id=product_in.tenant_id,
        company_id=product_in.company_id,
        category_id=product_in.category_id,
        unit_id=product_in.unit_id,
        code=product_in.code,
        name=product_in.name,
        description=product_in.description,
        price=product_in.price,
        cost=product_in.cost,
        stock_qty=product_in.stock_qty,
        min_stock_qty=product_in.min_stock_qty,
        ncm=product_in.ncm,
        cest=product_in.cest,
        is_active=product_in.is_active
    )

    if product_in.barcodes:
        for b_code in product_in.barcodes:
            if b_code.strip():
                product.barcodes.append(ProductBarcode(barcode=b_code.strip()))

    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/by-barcode/{barcode}", response_model=ProductDetailResponse, summary="Buscar Produto por Código de Barras (PDV)")
def get_product_by_barcode(
    barcode: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Busca rápida otimizada para o leitor de código de barras no PDV.
    """
    product = db.scalar(
        select(Product)
        .join(ProductBarcode)
        .where(
            Product.tenant_id == current_user.tenant_id,
            ProductBarcode.barcode == barcode.strip()
        )
    )
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado pelo código de barras informado")
    return product


@router.get("/{product_id}", response_model=ProductDetailResponse, summary="Obter Detalhes do Produto por ID")
def get_product(
    product_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("produtos.visualizar"))
) -> Any:
    """
    Obtém detalhes do produto pelo ID.
    """
    product = db.scalar(select(Product).where(Product.id == product_id))
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    if not current_user.is_superuser and product.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acesso não autorizado")

    return product


@router.put("/{product_id}", response_model=ProductDetailResponse, summary="Atualizar Produto")
def update_product(
    product_id: UUID,
    product_in: ProductUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("produtos.editar"))
) -> Any:
    """
    Atualiza informações de um produto existente.
    """
    product = db.scalar(select(Product).where(Product.id == product_id))
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    if not current_user.is_superuser and product.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acesso não autorizado")

    update_data = product_in.model_dump(exclude_unset=True)

    if "barcodes" in update_data:
        new_barcodes = update_data.pop("barcodes")
        if new_barcodes is not None:
            product.barcodes.clear()
            for b_code in new_barcodes:
                if b_code.strip():
                    product.barcodes.append(ProductBarcode(barcode=b_code.strip()))

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", summary="Inativar/Excluir Produto")
def delete_product(
    product_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("produtos.editar"))
) -> Any:
    """
    Inativa (Soft-Delete) um produto mantendo o histórico de auditoria intacto.
    """
    product = db.scalar(select(Product).where(Product.id == product_id))
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    if not current_user.is_superuser and product.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Acesso não autorizado")

    product.is_active = False
    db.commit()
    return {"detail": "Produto inativado com sucesso"}
