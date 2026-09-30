import re
import uuid
from datetime import datetime, date, timezone
from xml.etree import ElementTree as ET
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.company import Company
from app.models.customer import Supplier
from app.models.product import Product, ProductBarcode
from app.models.stock import StockMovement, StockMovementType
from app.models.purchase import Purchase, PurchaseItem, PurchaseStatus
from app.models.finance import AccountPayable, AccountPayableStatus
from app.models.audit import AuditLog
from app.schemas.purchase_import import (
    NfeSupplierPreviewDTO,
    NfeItemPreviewDTO,
    NfeInstallmentPreviewDTO,
    NfeImportPreviewResponse,
    PurchaseConfirmInput,
)


def _clean_str(val: Any) -> str:
    return str(val or "").strip()


def _clean_digits(val: Any) -> str:
    return re.sub(r"\D", "", str(val or ""))


class NfeXmlImportService:
    """Serviço de alta integridade para Importação e Efetivação de Entradas por XML de NF-e de Fornecedor (Modelo 55)."""

    @classmethod
    def parse_and_preview_xml(
        cls,
        db: Session,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        xml_content: str,
    ) -> NfeImportPreviewResponse:
        """FASE 1: Parse do XML, pré-validação estrita (chave duplicada, destinatário CNPJ),
        resolução de fornecedor, sugestão de de-para de produtos e extração de faturas.
        NÃO altera o estoque nem grava financeiro.
        """
        company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == tenant_id))
        if not company:
            raise ValueError("Empresa ativa não encontrada.")

        # Remove namespaces para facilidade de navegação no ElementTree
        xml_clean = re.sub(r'\sxmlns="[^"]+"', '', xml_content, count=1)
        try:
            root = ET.fromstring(xml_clean)
        except Exception as err:
            raise ValueError(f"XML corrompido ou formato inválido: {str(err)}")

        infNFe = root.find(".//infNFe")
        if infNFe is None:
            raise ValueError("Nó <infNFe> não encontrado no XML da NF-e.")

        # Chave de Acesso (44 dígitos)
        raw_id = infNFe.attrib.get("Id", "")
        access_key = re.sub(r"\D", "", raw_id)
        if len(access_key) != 44:
            # Tenta buscar tag <chNFe>
            ch_tag = root.find(".//chNFe")
            if ch_tag is not None and ch_tag.text:
                access_key = _clean_digits(ch_tag.text)

        if len(access_key) != 44:
            raise ValueError("Não foi possível extrair a Chave de Acesso válida de 44 dígitos do XML.")

        # Validação 1: Proteção Contra Chave Duplicada
        existing_purchase = db.scalar(
            select(Purchase).where(
                Purchase.company_id == company_id,
                Purchase.access_key == access_key,
                Purchase.status != PurchaseStatus.CANCELED.value,
            )
        )
        is_duplicate_key = existing_purchase is not None

        # Dados da Ide (<ide>)
        ide = infNFe.find("ide")
        nfe_number = int(ide.findtext("nNF", "0")) if ide is not None else 0
        nfe_series = int(ide.findtext("serie", "1")) if ide is not None else 1
        issue_date = ide.findtext("dhEmi", ide.findtext("dEmi", "")) if ide is not None else ""

        # Validação 2: CNPJ do Destinatário (<dest>)
        dest = infNFe.find("dest")
        recipient_cnpj = _clean_digits(dest.findtext("CNPJ", dest.findtext("CPF", ""))) if dest is not None else ""
        company_cnpj_clean = _clean_digits(company.cnpj)
        is_valid_recipient = (recipient_cnpj == company_cnpj_clean)

        validation_errors = []
        if is_duplicate_key:
            validation_errors.append(f"NF-e com Chave de Acesso {access_key} já foi importada e efetivada nesta empresa.")
        if not is_valid_recipient:
            validation_errors.append(f"CNPJ do destinatário da NF-e ({recipient_cnpj}) não corresponde ao CNPJ da empresa ativa ({company_cnpj_clean}).")

        # Dados do Emitente / Fornecedor (<emit>)
        emit = infNFe.find("emit")
        emit_cnpj = _clean_digits(emit.findtext("CNPJ", "")) if emit is not None else ""
        emit_name = _clean_str(emit.findtext("xNome", "FORNECEDOR DESTE XML")) if emit is not None else "FORNECEDOR"
        emit_trade = _clean_str(emit.findtext("xFant", "")) if emit is not None else ""
        emit_ie = _clean_str(emit.findtext("IE", "")) if emit is not None else ""
        
        ender = emit.find("enderEmit") if emit is not None else None
        emit_address = {
            "xLgr": _clean_str(ender.findtext("xLgr", "")) if ender is not None else "",
            "nro": _clean_str(ender.findtext("nro", "")) if ender is not None else "",
            "xBairro": _clean_str(ender.findtext("xBairro", "")) if ender is not None else "",
            "cMun": _clean_str(ender.findtext("cMun", "")) if ender is not None else "",
            "xMun": _clean_str(ender.findtext("xMun", "")) if ender is not None else "",
            "UF": _clean_str(ender.findtext("UF", "")) if ender is not None else "",
            "CEP": _clean_str(ender.findtext("CEP", "")) if ender is not None else "",
        }

        supplier_dto = NfeSupplierPreviewDTO(
            cnpj=emit_cnpj,
            name=emit_name,
            trade_name=emit_trade,
            ie=emit_ie,
            address=emit_address,
        )

        # Totais (<total><ICMSTot>)
        total_node = infNFe.find(".//ICMSTot")
        totals_dict = {}
        if total_node is not None:
            totals_dict = {
                "vProd": float(total_node.findtext("vProd", "0") or 0),
                "vDesc": float(total_node.findtext("vDesc", "0") or 0),
                "vFrete": float(total_node.findtext("vFrete", "0") or 0),
                "vSeguro": float(total_node.findtext("vSeguro", "0") or 0),
                "vOutro": float(total_node.findtext("vOutro", "0") or 0),
                "vICMS": float(total_node.findtext("vICMS", "0") or 0),
                "vST": float(total_node.findtext("vST", "0") or 0),
                "vIPI": float(total_node.findtext("vIPI", "0") or 0),
                "vPIS": float(total_node.findtext("vPIS", "0") or 0),
                "vCOFINS": float(total_node.findtext("vCOFINS", "0") or 0),
                "vNF": float(total_node.findtext("vNF", "0") or 0),
            }

        # Itens (<det>)
        items_dto: List[NfeItemPreviewDTO] = []
        for det in infNFe.findall("det"):
            nItem = int(det.attrib.get("nItem", "1"))
            prod = det.find("prod")
            if prod is None:
                continue

            cProd = _clean_str(prod.findtext("cProd", ""))
            cEAN = _clean_str(prod.findtext("cEAN", ""))
            xProd = _clean_str(prod.findtext("xProd", ""))
            ncm = _clean_str(prod.findtext("NCM", ""))
            cest = _clean_str(prod.findtext("CEST", ""))
            cfop = _clean_str(prod.findtext("CFOP", ""))
            uCom = _clean_str(prod.findtext("uCom", "UN"))
            qCom = float(prod.findtext("qCom", "1") or 1)
            vUnCom = float(prod.findtext("vUnCom", "0") or 0)
            vProd = float(prod.findtext("vProd", "0") or 0)
            vDesc = float(prod.findtext("vDesc", "0") or 0)

            # Tenta sugestão de produto local por GTIN/EAN ou cProd ou NCM
            suggested_prod = None
            if cEAN and cEAN != "SEM GTIN":
                suggested_prod = db.scalar(
                    select(Product)
                    .join(ProductBarcode)
                    .where(Product.company_id == company_id, ProductBarcode.barcode == cEAN)
                )
            if not suggested_prod and cProd:
                suggested_prod = db.scalar(select(Product).where(Product.company_id == company_id, Product.code == cProd))
            if not suggested_prod and xProd:
                suggested_prod = db.scalar(select(Product).where(Product.company_id == company_id, Product.name.ilike(f"%{xProd[:20]}%")))

            items_dto.append(
                NfeItemPreviewDTO(
                    item_number=nItem,
                    vendor_product_code=cProd,
                    description=xProd,
                    ncm=ncm,
                    cest=cest,
                    cfop=cfop,
                    uCom=uCom,
                    qCom=qCom,
                    vUnCom=vUnCom,
                    vProd=vProd,
                    vDesc=vDesc,
                    taxes={},
                    suggested_local_product_id=suggested_prod.id if suggested_prod else None,
                    suggested_local_product_name=suggested_prod.name if suggested_prod else None,
                    suggested_conversion_factor=1.0,
                )
            )

        # Faturas / Duplicatas (<cobr><dup>)
        installments_dto: List[NfeInstallmentPreviewDTO] = []
        for dup in infNFe.findall(".//dup"):
            nDup = _clean_str(dup.findtext("nDup", "1"))
            dVenc = _clean_str(dup.findtext("dVenc", ""))
            vDup = float(dup.findtext("vDup", "0") or 0)
            installments_dto.append(NfeInstallmentPreviewDTO(nDup=nDup, dVenc=dVenc, vDup=vDup))

        return NfeImportPreviewResponse(
            access_key=access_key,
            nfe_number=nfe_number,
            nfe_series=nfe_series,
            issue_date=issue_date,
            supplier=supplier_dto,
            recipient_cnpj=recipient_cnpj,
            is_valid_recipient=is_valid_recipient,
            is_duplicate_key=is_duplicate_key,
            validation_errors=validation_errors,
            totals=totals_dict,
            items=items_dto,
            installments=installments_dto,
            raw_xml=xml_content,
        )

    @classmethod
    def confirm_and_execute_import(
        cls,
        db: Session,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        confirm_input: PurchaseConfirmInput,
    ) -> Purchase:
        """FASE 2: Confirmação e Efetivação em Transação Atômica.
        Atualiza estoques, lança fornecedor, grava títulos no Contas a Pagar e gera Auditoria.
        """
        company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == tenant_id))
        if not company:
            raise ValueError("Empresa ativa não encontrada.")

        # Validação 1: Re-verifica chave duplicada na transação atômica
        existing = db.scalar(
            select(Purchase).where(
                Purchase.company_id == company_id,
                Purchase.access_key == confirm_input.access_key,
                Purchase.status != PurchaseStatus.CANCELED.value,
            )
        )
        if existing:
            raise ValueError(f"NF-e com Chave de Acesso {confirm_input.access_key} já foi efetivada no sistema.")

        # Validação 2: Resolve ou cadastra o Fornecedor
        clean_supplier_cnpj = _clean_digits(confirm_input.supplier_cnpj)
        supplier = db.scalar(
            select(Supplier).where(
                Supplier.company_id == company_id,
                Supplier.document == clean_supplier_cnpj,
            )
        )
        if not supplier:
            supplier = Supplier(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                company_id=company_id,
                name=confirm_input.supplier_name,
                document=clean_supplier_cnpj,
                state_registration=confirm_input.supplier_ie,
                is_active=True,
            )
            db.add(supplier)
            db.flush()

        # Gera Código Sequencial COMP-YYYYMMDD-XXXX
        now_str = datetime.now().strftime("%Y%m%d")
        rand_num = uuid.uuid4().hex[:4].upper()
        purchase_code = f"COMP-{now_str}-{rand_num}"

        # Cria a Compra
        purchase = Purchase(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            company_id=company_id,
            supplier_id=supplier.id,
            user_id=user_id,
            code=purchase_code,
            status=PurchaseStatus.RECEIVED.value,
            subtotal=0.0,
            discount_amount=0.0,
            total_amount=0.0,
            notes=confirm_input.notes or f"Importação NF-e {confirm_input.access_key}",
            access_key=confirm_input.access_key,
            raw_xml=confirm_input.raw_xml,
            import_status="CONFIRMED",
        )
        db.add(purchase)
        db.flush()

        # Mapeia Itens, Estoque e Custo Médio Ponderado
        subtotal_purchase = 0.0
        purchase_items = []

        for mapping in confirm_input.items_mapping:
            product = db.scalar(
                select(Product).where(
                    Product.id == mapping.local_product_id,
                    Product.company_id == company_id,
                )
            )
            if not product:
                raise ValueError(f"Produto local com ID {mapping.local_product_id} não encontrado.")

            conversion_factor = mapping.conversion_factor if mapping.conversion_factor > 0 else 1.0
            
            # Executa o parse no item correspondente do XML
            xml_clean = re.sub(r'\sxmlns="[^"]+"', '', confirm_input.raw_xml, count=1)
            root = ET.fromstring(xml_clean)
            det_node = root.find(f".//det[@nItem='{mapping.item_number}']")
            
            vProd = 0.0
            vDesc = 0.0
            qCom = 1.0
            vUnCom = 0.0
            uCom = "UN"

            if det_node is not None:
                prod_node = det_node.find("prod")
                if prod_node is not None:
                    vProd = float(prod_node.findtext("vProd", "0") or 0)
                    vDesc = float(prod_node.findtext("vDesc", "0") or 0)
                    qCom = float(prod_node.findtext("qCom", "1") or 1)
                    vUnCom = float(prod_node.findtext("vUnCom", "0") or 0)
                    uCom = _clean_str(prod_node.findtext("uCom", "UN"))

            # Quantidade Convertida = qCom * Fator de Conversão (ex: 1 caixa com 12 -> 12 unidades)
            converted_qty = qCom * conversion_factor
            
            # Custo Unitário Convertido
            if mapping.unit_cost_override is not None and mapping.unit_cost_override > 0:
                converted_unit_cost = mapping.unit_cost_override
            else:
                converted_unit_cost = (vProd - vDesc) / converted_qty if converted_qty > 0 else vUnCom

            total_item_cost = converted_qty * converted_unit_cost
            subtotal_purchase += total_item_cost

            # Atualiza estoque e Custo Médio Ponderado
            prev_qty = float(product.stock_qty or 0.0)
            new_qty = prev_qty + converted_qty
            old_cost = float(product.cost or 0.0)

            # Custo médio ponderado
            if new_qty > 0:
                new_weighted_cost = round(((prev_qty * old_cost) + (converted_qty * converted_unit_cost)) / new_qty, 2)
            else:
                new_weighted_cost = converted_unit_cost

            product.stock_qty = new_qty
            product.cost = new_weighted_cost
            db.add(product)

            # Movimentação de Estoque
            stock_mov = StockMovement(
                tenant_id=tenant_id,
                company_id=company_id,
                product_id=product.id,
                user_id=user_id,
                movement_type=StockMovementType.ENTRADA_NF,
                quantity=converted_qty,
                previous_qty=prev_qty,
                new_qty=new_qty,
                unit_cost=converted_unit_cost,
                reference_doc=purchase_code,
                notes=f"Entrada por Importação de NF-e {confirm_input.access_key[:10]}... (Fator {conversion_factor})",
            )
            db.add(stock_mov)

            # Item da Compra
            p_item = PurchaseItem(
                purchase_id=purchase.id,
                product_id=product.id,
                item_number=mapping.item_number,
                product_name=product.name,
                unit_code=product.unit.code if getattr(product, "unit", None) else uCom,
                quantity=converted_qty,
                unit_cost=converted_unit_cost,
                total_cost=total_item_cost,
                vendor_product_code=mapping.vendor_product_code,
                unit_conversion_factor=conversion_factor,
            )
            db.add(p_item)

        purchase.subtotal = subtotal_purchase
        purchase.total_amount = subtotal_purchase
        db.add(purchase)

        # Lançamento Financeiro no Contas a Pagar
        if confirm_input.generate_accounts_payable:
            xml_clean = re.sub(r'\sxmlns="[^"]+"', '', confirm_input.raw_xml, count=1)
            root = ET.fromstring(xml_clean)
            dups = root.findall(".//dup")
            
            if dups:
                for dup in dups:
                    nDup = _clean_str(dup.findtext("nDup", "1"))
                    dVenc_str = _clean_str(dup.findtext("dVenc", ""))
                    vDup = float(dup.findtext("vDup", "0") or 0)

                    try:
                        due_dt = datetime.strptime(dVenc_str, "%Y-%m-%d").date()
                    except Exception:
                        due_dt = date.today()

                    ap = AccountPayable(
                        tenant_id=tenant_id,
                        company_id=company_id,
                        supplier_id=supplier.id,
                        purchase_id=purchase.id,
                        description=f"NF-e {confirm_input.access_key[:10]} - Parcela {nDup} - {supplier.name[:30]}",
                        amount=vDup,
                        due_date=due_dt,
                        status=AccountPayableStatus.PENDING.value,
                        notes=f"Importado via NF-e Chave {confirm_input.access_key}",
                    )
                    db.add(ap)
            else:
                # Título único para o valor total
                ap = AccountPayable(
                    tenant_id=tenant_id,
                    company_id=company_id,
                    supplier_id=supplier.id,
                    purchase_id=purchase.id,
                    description=f"NF-e {confirm_input.access_key[:10]} - {supplier.name[:30]}",
                    amount=subtotal_purchase,
                    due_date=date.today(),
                    status=AccountPayableStatus.PENDING.value,
                    notes=f"Importado via NF-e Chave {confirm_input.access_key}",
                )
                db.add(ap)

        import json
        # Trilha de Auditoria
        audit = AuditLog(
            tenant_id=tenant_id,
            company_id=company_id,
            user_id=user_id,
            action="PURCHASE_NFE_IMPORTED",
            entity="purchase",
            entity_id=purchase.id,
            after_data=json.dumps({
                "access_key": confirm_input.access_key,
                "purchase_code": purchase_code,
                "supplier_name": supplier.name,
                "supplier_cnpj": supplier.document,
                "total_amount": subtotal_purchase,
                "items_count": len(confirm_input.items_mapping),
            }),
        )
        db.add(audit)

        db.commit()
        db.refresh(purchase)
        return purchase
