import uuid
import random
from typing import List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, desc

from app.api import deps
from app.models.user import User
from app.models.company import Company
from app.models.customer import Supplier
from app.models.product import Product
from app.models.stock import StockMovement, StockMovementType
from app.models.purchase import Purchase, PurchaseItem, PurchaseStatus
from app.schemas.purchase import (
    PurchaseCreate,
    PurchaseResponse,
    PurchaseItemResponse,
)
from app.schemas.purchase_import import (
    NfeImportPreviewResponse,
    PurchaseConfirmInput,
)
from app.services.nfe_xml_import_service import NfeXmlImportService

router = APIRouter()


@router.post("/import-xml-preview", response_model=NfeImportPreviewResponse, summary="FASE 1: Prévia e Validação de Importação XML de NF-e")
async def preview_nfe_xml_import(
    company_id: uuid.UUID = Query(..., description="ID da Empresa"),
    xml_file: Optional[UploadFile] = File(None, description="Arquivo XML da NF-e Modelo 55"),
    xml_content_str: Optional[str] = Form(None, description="Conteúdo XML em texto puro"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    FASE 1: Recebe o XML da NF-e Modelo 55 de fornecedor, realiza pré-validação estrita
    (chave de acesso duplicada, CNPJ do destinatário), extrai faturas, resolve fornecedor
    e sugere o de-para de produtos.
    IMPORTANTE: Esta etapa NÃO altera o estoque nem cria lançamentos no Contas a Pagar.
    """
    raw_xml = ""
    if xml_file:
        content_bytes = await xml_file.read()
        raw_xml = content_bytes.decode("utf-8", errors="ignore")
    elif xml_content_str:
        raw_xml = xml_content_str

    if not raw_xml:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Envie um arquivo XML da NF-e ou o conteúdo XML em texto."
        )

    try:
        return NfeXmlImportService.parse_and_preview_xml(
            db=db,
            tenant_id=current_user.tenant_id,
            company_id=company_id,
            xml_content=raw_xml,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro no processamento do XML: {str(e)}")


@router.post("/confirm-import", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED, summary="FASE 2: Confirmação e Efetivação da Entrada de Compra por NF-e")
def confirm_nfe_xml_import(
    confirm_in: PurchaseConfirmInput,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    FASE 2: Confirmação explícita do operador após revisar o de-para de produtos e fatores de conversão de unidade.
    Executa a efetivação atômica no banco de dados:
    1. Cadastra/atualiza Fornecedor.
    2. Cria registro da Compra com a Chave de Acesso da NF-e e armazena o XML.
    3. Atualiza o estoque com a quantidade convertida e atualiza o Custo Médio Ponderado dos produtos.
    4. Lança os títulos a pagar no módulo financeiro (Contas a Pagar).
    5. Gera o log de Auditoria e rastreabilidade.
    """
    try:
        purchase = NfeXmlImportService.confirm_and_execute_import(
            db=db,
            tenant_id=current_user.tenant_id,
            company_id=confirm_in.company_id,
            user_id=current_user.id,
            confirm_input=confirm_in,
        )
        
        # Carrega relacionamentos para resposta
        p_loaded = db.scalar(
            select(Purchase)
            .options(
                selectinload(Purchase.items),
                selectinload(Purchase.supplier),
                selectinload(Purchase.user),
            )
            .where(Purchase.id == purchase.id)
        )
        return p_loaded
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao efetivar compra: {str(e)}")


def generate_purchase_code() -> str:
    now_str = datetime.now().strftime("%Y%m%d")
    rand_num = random.randint(1000, 9999)
    return f"COMP-{now_str}-{rand_num}"


@router.post("/", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED, summary="Registrar Entrada de Compra")
def create_purchase(
    purchase_in: PurchaseCreate,
    company_id: uuid.UUID = Query(..., description="ID da empresa/filial da compra"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Registra uma nova compra/entrada de mercadoria no estoque.
    Gera automaticamente as movimentações de estoque (ENTRADA_NF),
    atualiza as quantidades em estoque e ajusta o preço de custo do produto.
    """
    # Verificar permissão na empresa
    company = db.scalar(
        select(Company).where(
            Company.id == company_id,
            Company.tenant_id == current_user.tenant_id
        )
    )
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada ou sem autorização."
        )

    # Validar fornecedor se informado
    supplier = None
    if purchase_in.supplier_id:
        supplier = db.scalar(
            select(Supplier).where(
                Supplier.id == purchase_in.supplier_id,
                Supplier.company_id == company_id
            )
        )
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Fornecedor informado não encontrado."
            )

    code = generate_purchase_code()
    subtotal = 0.0
    purchase_items = []
    stock_movements = []

    for idx, item_in in enumerate(purchase_in.items, start=1):
        product = db.scalar(
            select(Product)
            .options(selectinload(Product.unit))
            .where(
                Product.id == item_in.product_id,
                Product.company_id == company_id
            )
        )
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produto ID {item_in.product_id} não encontrado."
            )

        item_total = item_in.quantity * item_in.unit_cost
        subtotal += item_total

        # Criar item da compra
        u_code = product.unit.code if product.unit else "UN"
        p_item = PurchaseItem(
            id=uuid.uuid4(),
            product_id=product.id,
            item_number=idx,
            product_name=product.name,
            unit_code=u_code,
            quantity=item_in.quantity,
            unit_cost=item_in.unit_cost,
            total_cost=item_total,
        )
        purchase_items.append(p_item)

        # Atualizar estoque do produto
        prev_qty = float(product.stock_qty)
        new_qty = prev_qty + item_in.quantity
        product.stock_qty = new_qty
        # Atualizar preço de custo unitário do produto
        product.cost = item_in.unit_cost

        # Gerar auditoria de estoque
        stk_mov = StockMovement(
            id=uuid.uuid4(),
            tenant_id=current_user.tenant_id,
            company_id=company_id,
            product_id=product.id,
            user_id=current_user.id,
            movement_type=StockMovementType.ENTRADA_NF.value,
            quantity=item_in.quantity,
            previous_qty=prev_qty,
            new_qty=new_qty,
            unit_cost=item_in.unit_cost,
            reference_doc=code,
            notes=f"Entrada de Compra #{code}",
        )
        stock_movements.append(stk_mov)

    total_amount = max(0.0, subtotal - purchase_in.discount_amount)

    purchase = Purchase(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        company_id=company_id,
        supplier_id=purchase_in.supplier_id,
        user_id=current_user.id,
        code=code,
        status=PurchaseStatus.RECEIVED.value,
        subtotal=subtotal,
        discount_amount=purchase_in.discount_amount,
        total_amount=total_amount,
        notes=purchase_in.notes,
        items=purchase_items,
    )

    db.add(purchase)
    db.add_all(stock_movements)
    db.commit()
    db.refresh(purchase)

    return PurchaseResponse(
        id=purchase.id,
        tenant_id=purchase.tenant_id,
        company_id=purchase.company_id,
        supplier_id=purchase.supplier_id,
        supplier_name=supplier.name if supplier else None,
        user_id=purchase.user_id,
        user_name=current_user.name,
        code=purchase.code,
        status=purchase.status,
        subtotal=float(purchase.subtotal),
        discount_amount=float(purchase.discount_amount),
        total_amount=float(purchase.total_amount),
        notes=purchase.notes,
        items=[
            PurchaseItemResponse(
                id=pi.id,
                purchase_id=pi.purchase_id,
                product_id=pi.product_id,
                item_number=pi.item_number,
                product_name=pi.product_name,
                unit_code=pi.unit_code,
                quantity=float(pi.quantity),
                unit_cost=float(pi.unit_cost),
                total_cost=float(pi.total_cost),
            )
            for pi in purchase.items
        ],
        created_at=purchase.created_at,
        updated_at=purchase.updated_at,
    )


@router.get("/", response_model=List[PurchaseResponse], summary="Listar Entradas de Compras")
def list_purchases(
    company_id: uuid.UUID = Query(..., description="ID da empresa/filial"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Lista todos os pedidos e entradas de compras da empresa ativa.
    """
    stmt = (
        select(Purchase)
        .options(
            selectinload(Purchase.items),
            selectinload(Purchase.supplier),
            selectinload(Purchase.user)
        )
        .where(
            Purchase.company_id == company_id,
            Purchase.tenant_id == current_user.tenant_id
        )
        .order_by(desc(Purchase.created_at))
    )
    purchases = db.scalars(stmt).all()

    result = []
    for p in purchases:
        result.append(
            PurchaseResponse(
                id=p.id,
                tenant_id=p.tenant_id,
                company_id=p.company_id,
                supplier_id=p.supplier_id,
                supplier_name=p.supplier.name if p.supplier else None,
                user_id=p.user_id,
                user_name=p.user.name if p.user else None,
                code=p.code,
                status=p.status,
                subtotal=float(p.subtotal),
                discount_amount=float(p.discount_amount),
                total_amount=float(p.total_amount),
                notes=p.notes,
                items=[
                    PurchaseItemResponse(
                        id=pi.id,
                        purchase_id=pi.purchase_id,
                        product_id=pi.product_id,
                        item_number=pi.item_number,
                        product_name=pi.product_name,
                        unit_code=pi.unit_code,
                        quantity=float(pi.quantity),
                        unit_cost=float(pi.unit_cost),
                        total_cost=float(pi.total_cost),
                    )
                    for pi in p.items
                ],
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )
    return result


@router.get("/{purchase_id}", response_model=PurchaseResponse, summary="Obter Detalhes da Compra")
def get_purchase_detail(
    purchase_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retorna os detalhes completos de uma compra por ID.
    """
    stmt = (
        select(Purchase)
        .options(
            selectinload(Purchase.items),
            selectinload(Purchase.supplier),
            selectinload(Purchase.user)
        )
        .where(
            Purchase.id == purchase_id,
            Purchase.tenant_id == current_user.tenant_id
        )
    )
    purchase = db.scalar(stmt)
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de compra não encontrado."
        )

    return PurchaseResponse(
        id=purchase.id,
        tenant_id=purchase.tenant_id,
        company_id=purchase.company_id,
        supplier_id=purchase.supplier_id,
        supplier_name=purchase.supplier.name if purchase.supplier else None,
        user_id=purchase.user_id,
        user_name=purchase.user.name if purchase.user else None,
        code=purchase.code,
        status=purchase.status,
        subtotal=float(purchase.subtotal),
        discount_amount=float(purchase.discount_amount),
        total_amount=float(purchase.total_amount),
        notes=purchase.notes,
        items=[
            PurchaseItemResponse(
                id=pi.id,
                purchase_id=pi.purchase_id,
                product_id=pi.product_id,
                item_number=pi.item_number,
                product_name=pi.product_name,
                unit_code=pi.unit_code,
                quantity=float(pi.quantity),
                unit_cost=float(pi.unit_cost),
                total_cost=float(pi.total_cost),
            )
            for pi in purchase.items
        ],
        created_at=purchase.created_at,
        updated_at=purchase.updated_at,
    )


@router.post("/{purchase_id}/cancel", response_model=PurchaseResponse, summary="Cancelar Entrada de Compra")
def cancel_purchase(
    purchase_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Cancela uma compra recebida e realiza o estorno transacional do estoque.
    """
    stmt = (
        select(Purchase)
        .options(
            selectinload(Purchase.items),
            selectinload(Purchase.supplier),
            selectinload(Purchase.user)
        )
        .where(
            Purchase.id == purchase_id,
            Purchase.tenant_id == current_user.tenant_id
        )
    )
    purchase = db.scalar(stmt)
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de compra não encontrado."
        )

    if purchase.status == PurchaseStatus.CANCELED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta compra já se encontra cancelada."
        )

    stock_movements = []
    for item in purchase.items:
        product = db.scalar(
            select(Product).where(Product.id == item.product_id)
        )
        if product:
            prev_qty = float(product.stock_qty)
            new_qty = prev_qty - float(item.quantity)
            product.stock_qty = new_qty

            stk_mov = StockMovement(
                id=uuid.uuid4(),
                tenant_id=current_user.tenant_id,
                company_id=purchase.company_id,
                product_id=product.id,
                user_id=current_user.id,
                movement_type=StockMovementType.ESTORNO.value,
                quantity=-float(item.quantity),
                previous_qty=prev_qty,
                new_qty=new_qty,
                unit_cost=float(item.unit_cost),
                reference_doc=purchase.code,
                notes=f"Estorno por Cancelamento da Compra #{purchase.code}",
            )
            stock_movements.append(stk_mov)

    purchase.status = PurchaseStatus.CANCELED.value
    db.add_all(stock_movements)
    db.commit()
    db.refresh(purchase)

    return PurchaseResponse(
        id=purchase.id,
        tenant_id=purchase.tenant_id,
        company_id=purchase.company_id,
        supplier_id=purchase.supplier_id,
        supplier_name=purchase.supplier.name if purchase.supplier else None,
        user_id=purchase.user_id,
        user_name=purchase.user.name if purchase.user else None,
        code=purchase.code,
        status=purchase.status,
        subtotal=float(purchase.subtotal),
        discount_amount=float(purchase.discount_amount),
        total_amount=float(purchase.total_amount),
        notes=purchase.notes,
        items=[
            PurchaseItemResponse(
                id=pi.id,
                purchase_id=pi.purchase_id,
                product_id=pi.product_id,
                item_number=pi.item_number,
                product_name=pi.product_name,
                unit_code=pi.unit_code,
                quantity=float(pi.quantity),
                unit_cost=float(pi.unit_cost),
                total_cost=float(pi.total_cost),
            )
            for pi in purchase.items
        ],
        created_at=purchase.created_at,
        updated_at=purchase.updated_at,
    )


# --- XML Import Endpoints ---
from fastapi import UploadFile, File
from app.core.nfe_parser import parse_nfe_xml_bytes
from app.models.product import ProductBarcode
from app.models.finance import AccountPayable, AccountPayableStatus
from app.schemas.xml_import import (
    NfeParseResponse,
    NfeItemXmlParsed,
    NfeDupXmlParsed,
    NfeSupplierXml,
    NfeConfirmImportInput,
)


@router.post("/parse-xml", response_model=NfeParseResponse, summary="Parse de Arquivo XML de NF-e")
async def parse_nfe_xml_endpoint(
    file: UploadFile = File(...),
    company_id: uuid.UUID = Query(..., description="ID da empresa"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Recebe um arquivo XML de NF-e, faz a extração de emitente, itens e duplicatas
    e realiza a autodetecção de vínculo com os produtos cadastrados no banco de dados.
    """
    if not file.filename.endswith(".xml"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de arquivo inválido. Por favor envie um arquivo .xml de NF-e."
        )

    xml_content = await file.read()
    try:
        parsed_data = parse_nfe_xml_bytes(xml_content)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    # Tentar autodetectar vínculos de produtos na empresa
    company_products = db.scalars(
        select(Product)
        .options(selectinload(Product.barcodes))
        .where(
            Product.company_id == company_id,
            Product.tenant_id == current_user.tenant_id
        )
    ).all()

    items_response = []
    for item in parsed_data["items"]:
        c_ean = item.get("cEAN")
        c_prod = item.get("cProd")
        x_prod = item.get("xProd", "")

        matched_id = None
        matched_name = None

        for prod in company_products:
            # 1. Checar Barcode / EAN
            if c_ean and any(b.barcode == c_ean for b in prod.barcodes):
                matched_id = prod.id
                matched_name = prod.name
                break
            # 2. Checar Código do produto
            if c_prod and prod.code == c_prod:
                matched_id = prod.id
                matched_name = prod.name
                break
            # 3. Checar nome exato
            if prod.name.lower() == x_prod.lower():
                matched_id = prod.id
                matched_name = prod.name
                break

        items_response.append(
            NfeItemXmlParsed(
                item_number=item["item_number"],
                cProd=item["cProd"],
                cEAN=item.get("cEAN"),
                xProd=item["xProd"],
                ncm=item.get("ncm"),
                cest=item.get("cest"),
                uCom=item["uCom"],
                qCom=item["qCom"],
                vUnCom=item["vUnCom"],
                vProd=item["vProd"],
                matched_product_id=matched_id,
                matched_product_name=matched_name,
            )
        )

    return NfeParseResponse(
        chNFe=parsed_data["chNFe"],
        nNF=parsed_data["nNF"],
        serie=parsed_data["serie"],
        dhEmi=parsed_data.get("dhEmi"),
        supplier=NfeSupplierXml(**parsed_data["supplier"]),
        items=items_response,
        duplicatas=[NfeDupXmlParsed(**d) for d in parsed_data["duplicatas"]],
        total_vProd=parsed_data["total_vProd"],
        total_vNF=parsed_data["total_vNF"],
    )


@router.post("/confirm-xml", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED, summary="Confirmar Importação de NF-e")
def confirm_nfe_import_endpoint(
    confirm_in: NfeConfirmImportInput,
    company_id: uuid.UUID = Query(..., description="ID da empresa"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Executa a importação da NF-e com criação/vínculo de produtos,
    lançamento no estoque, criação da compra e lançamento opcional das Contas a Pagar.
    """
    # 1. Buscar ou cadastrar Fornecedor pelo Documento/CNPJ
    supplier = db.scalar(
        select(Supplier).where(
            Supplier.document == confirm_in.supplier.document,
            Supplier.company_id == company_id
        )
    )
    if not supplier:
        supplier = Supplier(
            id=uuid.uuid4(),
            tenant_id=current_user.tenant_id,
            company_id=company_id,
            name=confirm_in.supplier.name,
            trade_name=confirm_in.supplier.trade_name,
            document=confirm_in.supplier.document,
            state_registration=confirm_in.supplier.state_registration,
            phone=confirm_in.supplier.phone,
            address_street=confirm_in.supplier.address_street,
            address_number=confirm_in.supplier.address_number,
            address_neighborhood=confirm_in.supplier.address_neighborhood,
            city=confirm_in.supplier.city,
            state=confirm_in.supplier.state,
            postal_code=confirm_in.supplier.postal_code,
            is_active=True,
        )
        db.add(supplier)
        db.flush()

    purchase_code = f"COMP-NFE-{confirm_in.nNF}"
    subtotal = 0.0
    purchase_items = []
    stock_movements = []

    # 2. Processar Itens
    for idx, item_in in enumerate(confirm_in.items, start=1):
        product = None

        if item_in.action == "LINK_EXISTING" and item_in.linked_product_id:
            product = db.scalar(
                select(Product).where(
                    Product.id == item_in.linked_product_id,
                    Product.company_id == company_id
                )
            )

        if not product:
            # Criar Novo Produto no Estoque
            product = Product(
                id=uuid.uuid4(),
                tenant_id=current_user.tenant_id,
                company_id=company_id,
                code=item_in.cProd,
                name=item_in.name,
                unit_code=item_in.uCom or "UN",
                ncm=item_in.ncm,
                price=round(item_in.unit_cost * 1.30, 2),  # Margem padrão 30%
                cost_price=item_in.unit_cost,
                stock_qty=0.0,
                min_stock_qty=1.0,
                is_active=True,
            )
            db.add(product)
            db.flush()

            if item_in.cEAN:
                barcode = ProductBarcode(
                    id=uuid.uuid4(),
                    product_id=product.id,
                    barcode=item_in.cEAN,
                    is_main=True,
                )
                db.add(barcode)
        else:
            # Atualizar custo unitário
            product.cost_price = item_in.unit_cost

        item_total = item_in.quantity * item_in.unit_cost
        subtotal += item_total

        # Criar item de compra
        p_item = PurchaseItem(
            id=uuid.uuid4(),
            product_id=product.id,
            item_number=idx,
            product_name=product.name,
            unit_code=product.unit_code or "UN",
            quantity=item_in.quantity,
            unit_cost=item_in.unit_cost,
            total_cost=item_total,
        )
        purchase_items.append(p_item)

        # Lançamento de Estoque
        prev_qty = float(product.stock_qty)
        new_qty = prev_qty + item_in.quantity
        product.stock_qty = new_qty

        stk_mov = StockMovement(
            id=uuid.uuid4(),
            tenant_id=current_user.tenant_id,
            company_id=company_id,
            product_id=product.id,
            user_id=current_user.id,
            movement_type=StockMovementType.ENTRADA_NF.value,
            quantity=item_in.quantity,
            previous_qty=prev_qty,
            new_qty=new_qty,
            unit_cost=item_in.unit_cost,
            reference_doc=purchase_code,
            notes=f"Importação de NF-e #{confirm_in.nNF} (Chave: {confirm_in.chNFe})",
        )
        stock_movements.append(stk_mov)

    # 3. Criar Compra
    purchase = Purchase(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        company_id=company_id,
        supplier_id=supplier.id,
        user_id=current_user.id,
        code=purchase_code,
        status=PurchaseStatus.RECEIVED.value,
        subtotal=subtotal,
        discount_amount=0.0,
        total_amount=subtotal,
        notes=f"Importado via XML de NF-e Nº {confirm_in.nNF} (Chave: {confirm_in.chNFe})",
        items=purchase_items,
    )
    db.add(purchase)
    db.add_all(stock_movements)

    # 4. Gerar Contas a Pagar se solicitado
    if confirm_in.generate_payables and confirm_in.duplicatas:
        today = date.today()
        for dup in confirm_in.duplicatas:
            try:
                due_d = datetime.strptime(dup.dVenc, "%Y-%m-%d").date()
            except ValueError:
                due_d = today

            payable_status = AccountPayableStatus.OVERDUE.value if due_d < today else AccountPayableStatus.PENDING.value

            payable = AccountPayable(
                id=uuid.uuid4(),
                tenant_id=current_user.tenant_id,
                company_id=company_id,
                supplier_id=supplier.id,
                purchase_id=purchase.id,
                description=f"NF-e {confirm_in.nNF} - Dup {dup.nDup}",
                amount=dup.vDup,
                paid_amount=0.0,
                due_date=due_d,
                status=payable_status,
                notes=f"Gerado automaticamente via importação da NF-e Chave {confirm_in.chNFe}",
            )
            db.add(payable)

    db.commit()
    db.refresh(purchase)

    return PurchaseResponse(
        id=purchase.id,
        tenant_id=purchase.tenant_id,
        company_id=purchase.company_id,
        supplier_id=purchase.supplier_id,
        supplier_name=supplier.name,
        user_id=purchase.user_id,
        user_name=current_user.name,
        code=purchase.code,
        status=purchase.status,
        subtotal=float(purchase.subtotal),
        discount_amount=float(purchase.discount_amount),
        total_amount=float(purchase.total_amount),
        notes=purchase.notes,
        items=[
            PurchaseItemResponse(
                id=pi.id,
                purchase_id=pi.purchase_id,
                product_id=pi.product_id,
                item_number=pi.item_number,
                product_name=pi.product_name,
                unit_code=pi.unit_code,
                quantity=float(pi.quantity),
                unit_cost=float(pi.unit_cost),
                total_cost=float(pi.total_cost),
            )
            for pi in purchase.items
        ],
        created_at=purchase.created_at,
        updated_at=purchase.updated_at,
    )
