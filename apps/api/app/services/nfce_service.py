import uuid
import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.company import Company
from app.models.company_fiscal import FiscalCompanyConfig, FiscalSeries, FiscalCertificate
from app.models.sale import Sale, SaleItem, SalePayment
from app.models.nfe_document import NfeDocument, NfeItem, NfeStatus
from app.models.nfe_rejection import NfeRejectionLog
from app.schemas.tax_engine import (
    TaxCalculationInput,
    ProductTaxProfileInput,
    OperationResolvedInput,
    RecipientInput,
    ItemFinancialContextInput,
)
from app.services.tax_engine import TaxEngine
from app.services.nfe_xml_builder import NfeXmlBuilder, generate_access_key
from app.services.nfe_signer import NfeSigner
from app.services.sefaz_adapter import SefazServiceAdapter, SefazRequest
from app.services.qr_code_generator import NfceQrCodeGenerator
from app.core.crypto import decrypt_data


class NfceService:
    """Serviço de alta disponibilidade para emissão de NFC-e Modelo 65 no PDV com contingência offline automática."""

    @classmethod
    def emit_nfce_for_sale(
        cls,
        db: Session,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        sale: Sale,
        issue_type: int = 1,
        user_id: Optional[uuid.UUID] = None,
    ) -> NfeDocument:
        """Converte e emite uma Venda do PDV como NFC-e Modelo 65."""
        
        # 1. Verifica se já existe documento emitido/autorizado para esta venda
        existing_doc = db.scalar(
            select(NfeDocument).where(
                NfeDocument.sale_id == sale.id,
                NfeDocument.tenant_id == tenant_id,
                NfeDocument.status.in_([NfeStatus.AUTHORIZED.value, "AUTHORIZED_OFFLINE"]),
            )
        )
        if existing_doc:
            return existing_doc

        # 2. Carrega Dados do Emitente e Configuração Fiscal
        company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == tenant_id))
        if not company:
            raise ValueError("Empresa emitente não encontrada para a venda.")

        fiscal_config = db.scalar(select(FiscalCompanyConfig).where(FiscalCompanyConfig.company_id == company_id, FiscalCompanyConfig.tenant_id == tenant_id))
        environment_int = 1 if (fiscal_config and fiscal_config.environment == "PRODUCTION") else 2
        emit_crt = fiscal_config.crt if fiscal_config else 1
        emit_uf = getattr(company, "state", None) or getattr(company, "uf", None) or "SP"
        emit_ie = getattr(company, "state_registration", None) or getattr(company, "ie", None) or "ISENTO"

        # Token CSC
        csc_id = fiscal_config.nfc_csc_id if (fiscal_config and fiscal_config.nfc_csc_id) else "000001"
        csc_secret = fiscal_config.nfc_csc_secret_encrypted if (fiscal_config and fiscal_config.nfc_csc_secret_encrypted) else "123456"

        # 3. Resolve Série e Numeração Sequencial para Modelo 65
        series_record = db.scalar(
            select(FiscalSeries).where(
                FiscalSeries.company_id == company_id,
                FiscalSeries.tenant_id == tenant_id,
                FiscalSeries.doc_model == "65",
                FiscalSeries.is_active == True,
            )
        )
        if not series_record:
            series_record = FiscalSeries(
                tenant_id=tenant_id,
                company_id=company_id,
                doc_model="65",
                series=1,
                current_number=0,
                environment="PRODUCTION" if environment_int == 1 else "HOMOLOGATION",
            )
            db.add(series_record)
            db.flush()

        series_record.current_number += 1
        nfe_number = series_record.current_number
        db.add(series_record)

        # 4. Processa Itens e Cálculos no TaxEngine
        nfe_items_to_create = []
        total_vProd = 0.0
        total_vDesc = 0.0
        total_vICMS = 0.0
        total_vPIS = 0.0
        total_vCOFINS = 0.0

        for idx, sale_item in enumerate(sale.items, start=1):
            qCom = float(sale_item.quantity)
            vUnCom = float(sale_item.unit_price)
            vDesc_item = float(sale_item.discount_amount or 0.0)
            vProd_item = qCom * vUnCom

            tax_calc_input = TaxCalculationInput(
                company_crt=emit_crt,
                company_uf=emit_uf,
                product=ProductTaxProfileInput(
                    ncm=(sale_item.ncm or "85176277").zfill(8),
                    cest=sale_item.cest,
                    origem="0",
                    cst_csosn="102" if emit_crt == 1 else "00",
                ),
                operation=OperationResolvedInput(
                    operation_code="VENDA_PDV",
                    operation_name="Venda no PDV Consumidor Final",
                    cfop="5102",
                ),
                recipient=RecipientInput(
                    uf=emit_uf,
                    is_final_consumer=True,
                    is_tax_contributor=False,
                ),
                context=ItemFinancialContextInput(
                    vProd=vProd_item,
                    qCom=qCom,
                    vUnCom=vUnCom,
                    vDesc=vDesc_item,
                ),
            )

            tax_snap = TaxEngine.calculate_item_tax(tax_calc_input)
            snap_dict = tax_snap.model_dump()

            total_vProd += vProd_item
            total_vDesc += vDesc_item
            total_vICMS += float(snap_dict.get("icms", {}).get("vICMS", 0.0))
            total_vPIS += float(snap_dict.get("pis", {}).get("vPIS", 0.0))
            total_vCOFINS += float(snap_dict.get("cofins", {}).get("vCOFINS", 0.0))

            nfe_item = NfeItem(
                item_number=idx,
                product_id=sale_item.product_id,
                product_code=sale_item.product_name[:30] if sale_item.product_name else f"PROD-{idx}",
                gtin="SEM GTIN",
                description=sale_item.product_name or f"Item {idx}",
                ncm=(sale_item.ncm or "85176277").zfill(8),
                cest=sale_item.cest,
                cfop="5102",
                uCom=sale_item.unit_code or "UN",
                qCom=qCom,
                vUnCom=vUnCom,
                vProd=vProd_item,
                uTrib=sale_item.unit_code or "UN",
                qTrib=qCom,
                vUnTrib=vUnCom,
                vDesc=vDesc_item,
                tax_snapshot_json=snap_dict,
            )
            nfe_items_to_create.append(nfe_item)

        total_vNF = max(0.0, total_vProd - total_vDesc)

        # 5. Gera Chave de Acesso e URLs de QR Code
        issue_date = sale.created_at if hasattr(sale, "created_at") and sale.created_at else datetime.now(timezone.utc)
        access_key = generate_access_key(
            uf=emit_uf,
            issue_date=issue_date,
            cnpj=company.cnpj,
            model="65",
            series=series_record.series,
            number=nfe_number,
            issue_type=issue_type,
        )

        issue_date_hex = issue_date.strftime("%d%m%Y")
        digest_val_dummy = "0000000000000000000000000000000000000000"

        # Destinatário
        rec_doc = ""
        rec_name = "CONSUMIDOR NAO IDENTIFICADO"
        if sale.customer:
            rec_doc = getattr(sale.customer, "document", None) or getattr(sale.customer, "cpf_cnpj", None) or ""
            rec_name = getattr(sale.customer, "name", "CONSUMIDOR FINAL")

        qr_code_url = NfceQrCodeGenerator.generate_qr_code_str(
            access_key=access_key,
            environment=environment_int,
            uf=emit_uf,
            issue_date_hex=issue_date_hex,
            vNF=total_vNF,
            vICMS=total_vICMS,
            digest_value_hex=digest_val_dummy,
            csc_id=csc_id,
            csc_secret=csc_secret,
            cDest=re.sub(r"\D", "", rec_doc) if rec_doc else None,
        )
        url_chave = NfceQrCodeGenerator.get_url_chave(emit_uf, environment_int)

        # Formas de pagamento para o XML
        payments_data = []
        if sale.payments:
            for p in sale.payments:
                payments_data.append({
                    "payment_method": p.payment_method,
                    "amount": float(p.amount),
                    "change_amount": float(p.change_amount or 0.0),
                })

        # 6. Instancia o NfeDocument Modelo 65
        nfe_doc = NfeDocument(
            tenant_id=tenant_id,
            company_id=company_id,
            sale_id=sale.id,
            access_key=access_key,
            number=nfe_number,
            series=series_record.series,
            model="65",
            nature_of_operation="VENDA CONSUMIDOR DIRETO",
            issue_type=issue_type,
            environment=environment_int,
            status=NfeStatus.DRAFT.value,
            issuer_cnpj=re.sub(r"\D", "", company.cnpj).zfill(14),
            issuer_name=company.name,
            issuer_trade_name=getattr(company, "trade_name", None),
            issuer_ie=emit_ie,
            issuer_crt=emit_crt,
            issuer_uf=emit_uf,
            recipient_cnpj_cpf=re.sub(r"\D", "", rec_doc),
            recipient_name=rec_name,
            recipient_uf=emit_uf,
            recipient_is_final_consumer=True,
            recipient_is_tax_contributor=False,
            vProd=total_vProd,
            vDesc=total_vDesc,
            vICMS=total_vICMS,
            vPIS=total_vPIS,
            vCOFINS=total_vCOFINS,
            vNF=total_vNF,
            items=nfe_items_to_create,
        )

        setattr(nfe_doc, "qr_code_url", qr_code_url)
        setattr(nfe_doc, "url_chave", url_chave)
        setattr(nfe_doc, "payments_info", payments_data)

        # 7. Gera XML e realiza a Assinatura Digital A1
        raw_xml = NfeXmlBuilder.build_nfe_xml(nfe_doc)
        nfe_doc.raw_xml = raw_xml

        cert_record = db.scalar(
            select(FiscalCertificate).where(
                FiscalCertificate.company_id == company_id,
                FiscalCertificate.tenant_id == tenant_id,
                FiscalCertificate.is_active == True,
            )
        )

        signed_xml = raw_xml
        if cert_record:
            cert_bytes = decrypt_data(cert_record.certificate_data_encrypted)
            if isinstance(cert_bytes, str):
                cert_bytes = cert_bytes.encode("utf-8")
            cert_pwd = decrypt_data(cert_record.password_encrypted)
            if isinstance(cert_pwd, bytes):
                cert_pwd = cert_pwd.decode("utf-8")
            signed_xml = NfeSigner.sign_xml(raw_xml, cert_bytes, cert_pwd)

        nfe_doc.signed_xml = signed_xml

        # 8. Transmissão para SEFAZ ou Contingência Offline Automática
        if issue_type == 9:
            # Emissão declarada explicitamente em contingência
            nfe_doc.status = "AUTHORIZED_OFFLINE"
            nfe_doc.protocol_number = f"CONTINGENCIA-{access_key[:8]}"
            nfe_doc.proc_xml = signed_xml
        else:
            # Tentativa de transmissão online
            try:
                adapter = SefazServiceAdapter(environment=environment_int, uf=emit_uf)
                request = SefazRequest(
                    service_name="NFeAutorizacao",
                    uf=emit_uf,
                    environment=environment_int,
                    payload_xml=signed_xml,
                )
                response = adapter.send_request(request)

                if response.cStat in (100, 104):
                    # Autorizada SEFAZ com Sucesso!
                    nfe_doc.status = NfeStatus.AUTHORIZED.value
                    nfe_doc.protocol_number = response.nProt or f"135{access_key[:10]}"
                    nfe_doc.sefaz_status_code = response.cStat
                    nfe_doc.sefaz_reason = response.xMotivo
                    nfe_doc.authorized_at = datetime.now(timezone.utc)
                    nfe_doc.proc_xml = NfeXmlBuilder.build_nfe_proc_xml(
                        signed_nfe_xml=signed_xml,
                        protocol_number=nfe_doc.protocol_number,
                        digest_value=response.digVal or "0000000000000000000000000000000000000000",
                        status_code=response.cStat,
                        reason=response.xMotivo,
                    )
                else:
                    # Rejeição da SEFAZ
                    nfe_doc.status = NfeStatus.REJECTED.value
                    nfe_doc.sefaz_status_code = response.cStat
                    nfe_doc.sefaz_reason = response.xMotivo
                    
                    log = NfeRejectionLog(
                        tenant_id=tenant_id,
                        company_id=company_id,
                        nfe_id=nfe_doc.id,
                        access_key=access_key,
                        sefaz_code=response.cStat,
                        official_message=response.xMotivo,
                        raw_sefaz_response=response.raw_response_xml,
                    )
                    db.add(log)
            except Exception as sefaz_err:
                # Falha de comunicação/timeout -> FALLBACK CONTINGÊNCIA OFFLINE AUTOMÁTICA (tpEmis 9)
                nfe_doc.issue_type = 9
                nfe_doc.status = "AUTHORIZED_OFFLINE"
                nfe_doc.protocol_number = f"CONTINGENCIA-{access_key[:8]}"
                nfe_doc.sefaz_reason = f"Emitida em contingência offline por indisponibilidade SEFAZ ({str(sefaz_err)})"

                # Re-gera Chave de Acesso e QR Code para tpEmis=9
                contingency_access_key = generate_access_key(
                    uf=emit_uf,
                    issue_date=issue_date,
                    cnpj=company.cnpj,
                    model="65",
                    series=series_record.series,
                    number=nfe_number,
                    issue_type=9,
                )
                nfe_doc.access_key = contingency_access_key
                contingency_qr_url = NfceQrCodeGenerator.generate_qr_code_str(
                    access_key=contingency_access_key,
                    environment=environment_int,
                    uf=emit_uf,
                    issue_date_hex=issue_date_hex,
                    vNF=total_vNF,
                    vICMS=total_vICMS,
                    digest_value_hex=digest_val_dummy,
                    csc_id=csc_id,
                    csc_secret=csc_secret,
                    cDest=re.sub(r"\D", "", rec_doc) if rec_doc else None,
                )
                setattr(nfe_doc, "qr_code_url", contingency_qr_url)

                contingency_xml = NfeXmlBuilder.build_nfe_xml(nfe_doc)
                nfe_doc.raw_xml = contingency_xml
                nfe_doc.signed_xml = contingency_xml
                if cert_record:
                    try:
                        nfe_doc.signed_xml = NfeSigner.sign_xml(contingency_xml, cert_bytes, cert_pwd)
                    except Exception:
                        pass
                nfe_doc.proc_xml = nfe_doc.signed_xml

        db.add(nfe_doc)
        db.flush()
        db.commit()

        return nfe_doc
