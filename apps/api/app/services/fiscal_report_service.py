import uuid
import csv
import io
import json
from datetime import datetime, timezone, date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func

from app.models.nfe_document import NfeDocument, NfeItem, NfeStatus
from app.models.fiscal_event import FiscalEvent, FiscalInutilization
from app.schemas.fiscal_report import (
    FiscalReportFilterRequest,
    FiscalReportSummaryResponse,
    FiscalReportRowItem,
    FiscalReportGroupItem,
    TaxConsolidatedTotals,
)


def generate_fiscal_report(
    db: Session,
    tenant_id: uuid.UUID,
    payload: FiscalReportFilterRequest,
) -> FiscalReportSummaryResponse:
    """
    Gera relatórios fiscais parametrizados e consolidados:
    - EMITTED, RECEIVED, CANCELLED, INUTILIZED, REJECTED, CONTINGENCY,
      EVENTS, BY_CFOP, BY_CST, TAX_SUMMARY, RETURNS, PENDENCIES.
    """
    rep_type = payload.report_type.upper().strip()
    company_id = payload.company_id

    # Filtros de Data
    dt_from = datetime.combine(payload.start_date, datetime.min.time()).replace(tzinfo=timezone.utc) if payload.start_date else None
    dt_to = datetime.combine(payload.end_date, datetime.max.time()).replace(tzinfo=timezone.utc) if payload.end_date else None

    filter_dict = {
        "report_type": rep_type,
        "company_id": str(company_id),
        "start_date": payload.start_date.isoformat() if payload.start_date else None,
        "end_date": payload.end_date.isoformat() if payload.end_date else None,
        "model": payload.model,
        "cfop": payload.cfop,
        "cst_csosn": payload.cst_csosn,
        "recipient_cnpj_cpf": payload.recipient_cnpj_cpf,
        "issuer_cnpj": payload.issuer_cnpj,
        "purpose": payload.purpose,
    }

    rows: List[FiscalReportRowItem] = []
    grouped: List[FiscalReportGroupItem] = []
    totals = TaxConsolidatedTotals()

    # --- 1. Relatório de Inutilizações ---
    if rep_type == "INUTILIZED":
        inut_stmt = select(FiscalInutilization).where(
            FiscalInutilization.company_id == company_id,
            FiscalInutilization.tenant_id == tenant_id,
        )
        if dt_from:
            inut_stmt = inut_stmt.where(FiscalInutilization.created_at >= dt_from)
        if dt_to:
            inut_stmt = inut_stmt.where(FiscalInutilization.created_at <= dt_to)
        if payload.model:
            inut_stmt = inut_stmt.where(FiscalInutilization.model == payload.model)

        inut_list = list(db.scalars(inut_stmt).all())
        for inut in inut_list:
            dt_str = inut.created_at.strftime("%Y-%m-%d %H:%M:%S") if inut.created_at else ""
            rows.append(
                FiscalReportRowItem(
                    id=str(inut.id),
                    date=dt_str,
                    document_number=f"{inut.start_number} a {inut.end_number}",
                    series=str(inut.series),
                    model=inut.model,
                    access_key=None,
                    operation_type="INUTILIZACAO",
                    purpose="1",
                    status="INUTILIZADO" if inut.sefaz_status_code == 102 else "PENDENTE",
                    entity_name="SEFAZ - Inutilização de Série",
                    entity_cnpj_cpf="",
                    notes_or_reason=f"Justificativa: {inut.justification} | SEFAZ: {inut.sefaz_reason or 'Homologado'}",
                )
            )
        totals.total_documents = len(rows)

    # --- 2. Relatório de Eventos Fiscais ---
    elif rep_type == "EVENTS":
        evt_stmt = select(FiscalEvent).where(
            FiscalEvent.company_id == company_id,
            FiscalEvent.tenant_id == tenant_id,
        )
        if dt_from:
            evt_stmt = evt_stmt.where(FiscalEvent.created_at >= dt_from)
        if dt_to:
            evt_stmt = evt_stmt.where(FiscalEvent.created_at <= dt_to)

        evt_list = list(db.scalars(evt_stmt).all())
        for evt in evt_list:
            dt_str = evt.created_at.strftime("%Y-%m-%d %H:%M:%S") if evt.created_at else ""
            rows.append(
                FiscalReportRowItem(
                    id=str(evt.id),
                    date=dt_str,
                    document_number=f"Seq {evt.seq_number}",
                    series="1",
                    model="55",
                    access_key=evt.access_key,
                    operation_type=evt.event_name,
                    purpose="1",
                    status="REGISTRADO" if evt.sefaz_status_code in [135, 136] else "PROCESSADO",
                    entity_name=f"Evento: {evt.event_name}",
                    entity_cnpj_cpf="",
                    notes_or_reason=f"Justificativa/Conteúdo: {evt.justification_or_correction} | SEFAZ: {evt.sefaz_reason or ''}",
                )
            )
        totals.total_documents = len(rows)

    # --- 3. Relatórios por Agrupamento CFOP ---
    elif rep_type == "BY_CFOP":
        item_stmt = (
            select(
                NfeItem.cfop,
                func.count(NfeItem.id).label("cnt_items"),
                func.count(func.distinct(NfeItem.nfe_id)).label("cnt_docs"),
                func.sum(NfeItem.vProd).label("sum_vProd"),
            )
            .join(NfeDocument, NfeDocument.id == NfeItem.nfe_id)
            .where(
                NfeDocument.company_id == company_id,
                NfeDocument.tenant_id == tenant_id,
            )
        )
        if dt_from:
            item_stmt = item_stmt.where(NfeDocument.created_at >= dt_from)
        if dt_to:
            item_stmt = item_stmt.where(NfeDocument.created_at <= dt_to)
        if payload.model:
            item_stmt = item_stmt.where(NfeDocument.model == payload.model)
        if payload.cfop:
            item_stmt = item_stmt.where(NfeItem.cfop == payload.cfop)

        item_stmt = item_stmt.group_by(NfeItem.cfop)
        results = db.execute(item_stmt).all()

        tot_vprod = 0.0
        tot_docs = 0
        for r_cfop, c_items, c_docs, s_vprod in results:
            vprod_val = float(s_vprod or 0.0)
            tot_vprod += vprod_val
            tot_docs += c_docs
            grouped.append(
                FiscalReportGroupItem(
                    key_code=str(r_cfop),
                    description=f"CFOP {r_cfop} - Operação Fiscal",
                    count_docs=c_docs,
                    count_items=c_items,
                    vProd=vprod_val,
                    vBC=vprod_val,
                    vNF=vprod_val,
                )
            )

        totals.total_documents = tot_docs
        totals.total_vProd = round(tot_vprod, 2)
        totals.total_vNF = round(tot_vprod, 2)

    # --- 4. Relatórios por Agrupamento CST / CSOSN ---
    elif rep_type == "BY_CST":
        items_all = (
            db.query(NfeItem, NfeDocument)
            .join(NfeDocument, NfeDocument.id == NfeItem.nfe_id)
            .filter(
                NfeDocument.company_id == company_id,
                NfeDocument.tenant_id == tenant_id,
            )
        )
        if dt_from:
            items_all = items_all.filter(NfeDocument.created_at >= dt_from)
        if dt_to:
            items_all = items_all.filter(NfeDocument.created_at <= dt_to)
        if payload.model:
            items_all = items_all.filter(NfeDocument.model == payload.model)
        if payload.cst_csosn:
            items_all = items_all.filter(NfeItem.tax_snapshot_json.contains({"icms": {"cst_csosn": payload.cst_csosn}}))

        cst_map: Dict[str, Dict[str, Any]] = {}
        for item, doc in items_all.all():
            snap = item.tax_snapshot_json or {}
            cst_code = snap.get("icms", {}).get("cst_csosn", "102")
            if cst_code not in cst_map:
                cst_map[cst_code] = {
                    "count_items": 0,
                    "doc_ids": set(),
                    "vProd": 0.0,
                    "vBC": 0.0,
                    "vICMS": 0.0,
                }

            cst_map[cst_code]["count_items"] += 1
            cst_map[cst_code]["doc_ids"].add(str(doc.id))
            cst_map[cst_code]["vProd"] += float(item.vProd or 0.0)
            cst_map[cst_code]["vBC"] += float(snap.get("icms", {}).get("vBC_ICMS", 0.0))
            cst_map[cst_code]["vICMS"] += float(snap.get("icms", {}).get("vICMS", 0.0))

        tot_vprod = 0.0
        tot_vicms = 0.0
        for cst_code, data in sorted(cst_map.items()):
            c_docs = len(data["doc_ids"])
            vp = round(data["vProd"], 2)
            vbc = round(data["vBC"], 2)
            vicms = round(data["vICMS"], 2)
            tot_vprod += vp
            tot_vicms += vicms
            grouped.append(
                FiscalReportGroupItem(
                    key_code=cst_code,
                    description=f"CST/CSOSN {cst_code}",
                    count_docs=c_docs,
                    count_items=data["count_items"],
                    vProd=vp,
                    vBC=vbc,
                    vICMS=vicms,
                    vNF=vp,
                )
            )

        totals.total_documents = len(cst_map)
        totals.total_vProd = round(tot_vprod, 2)
        totals.total_vICMS = round(tot_vicms, 2)
        totals.total_vNF = round(tot_vprod, 2)

    # --- 5. Relatórios Baseados em NfeDocument (EMITTED, RECEIVED, CANCELLED, REJECTED, CONTINGENCY, TAX_SUMMARY, RETURNS, PENDENCIES) ---
    else:
        stmt = select(NfeDocument).where(
            NfeDocument.company_id == company_id,
            NfeDocument.tenant_id == tenant_id,
        )

        if dt_from:
            stmt = stmt.where(NfeDocument.created_at >= dt_from)
        if dt_to:
            stmt = stmt.where(NfeDocument.created_at <= dt_to)
        if payload.model:
            stmt = stmt.where(NfeDocument.model == payload.model)
        if payload.recipient_cnpj_cpf:
            stmt = stmt.where(NfeDocument.recipient_cnpj_cpf.contains(payload.recipient_cnpj_cpf))
        if payload.purpose:
            stmt = stmt.where(NfeDocument.purpose == payload.purpose)

        # Regras específicas por tipo de relatório
        if rep_type == "EMITTED":
            stmt = stmt.where(NfeDocument.operation_type_nfe == 1, NfeDocument.status.in_([NfeStatus.AUTHORIZED.value, NfeStatus.TRANSMITTED.value, NfeStatus.SIGNED.value]))
        elif rep_type == "RECEIVED":
            stmt = stmt.where(NfeDocument.operation_type_nfe == 0)
        elif rep_type == "CANCELLED":
            stmt = stmt.where(NfeDocument.status == NfeStatus.CANCELLED.value)
        elif rep_type == "REJECTED":
            stmt = stmt.where(NfeDocument.status == NfeStatus.REJECTED.value)
        elif rep_type == "CONTINGENCY":
            stmt = stmt.where(NfeDocument.issue_type == 9)
        elif rep_type == "RETURNS":
            stmt = stmt.where(NfeDocument.purpose == 4)
        elif rep_type == "PENDENCIES":
            stmt = stmt.where(
                or_(
                    NfeDocument.status.in_([NfeStatus.DRAFT.value, NfeStatus.SIGNED.value, NfeStatus.REJECTED.value]),
                    and_(NfeDocument.issue_type == 9, NfeDocument.status != NfeStatus.AUTHORIZED.value)
                )
            )

        stmt = stmt.order_by(NfeDocument.number.desc())
        docs = list(db.scalars(stmt).all())

        tot_vProd = 0.0
        tot_vBC = 0.0
        tot_vICMS = 0.0
        tot_vFCP = 0.0
        tot_vBCST = 0.0
        tot_vST = 0.0
        tot_vIPI = 0.0
        tot_vPIS = 0.0
        tot_vCOFINS = 0.0
        tot_vBC_IBS = 0.0
        tot_vIBS = 0.0
        tot_vBC_CBS = 0.0
        tot_vCBS = 0.0
        tot_vNF = 0.0

        for doc in docs:
            v_prod = float(doc.vProd or 0.0)
            v_bc = float(doc.vBC or 0.0)
            v_icms = float(doc.vICMS or 0.0)
            v_fcp = float(doc.vFCP or 0.0)
            v_st = float(doc.vST or 0.0)
            v_ipi = float(doc.vIPI or 0.0)
            v_pis = float(doc.vPIS or 0.0)
            v_cofins = float(doc.vCOFINS or 0.0)
            v_nf = float(doc.vNF or 0.0)

            # Acumular IBS/CBS dos itens a partir do TaxSnapshot
            v_ibs = 0.0
            v_cbs = 0.0
            v_bc_ibs = 0.0
            v_bc_cbs = 0.0

            for item in doc.items:
                snap = item.tax_snapshot_json or {}
                rtc = snap.get("rtc", {})
                v_ibs += float(rtc.get("vIBS", 0.0))
                v_cbs += float(rtc.get("vCBS", 0.0))
                v_bc_ibs += float(rtc.get("vBC_IBS", 0.0))
                v_bc_cbs += float(rtc.get("vBC_CBS", 0.0))

            tot_vProd += v_prod
            tot_vBC += v_bc
            tot_vICMS += v_icms
            tot_vFCP += v_fcp
            tot_vST += v_st
            tot_vIPI += v_ipi
            tot_vPIS += v_pis
            tot_vCOFINS += v_cofins
            tot_vBC_IBS += v_bc_ibs
            tot_vIBS += v_ibs
            tot_vBC_CBS += v_bc_cbs
            tot_vCBS += v_cbs
            tot_vNF += v_nf

            dt_str = doc.created_at.strftime("%Y-%m-%d %H:%M:%S") if doc.created_at else ""
            op_label = "SAIDA" if doc.operation_type_nfe == 1 else "ENTRADA"

            rows.append(
                FiscalReportRowItem(
                    id=str(doc.id),
                    date=dt_str,
                    document_number=str(doc.number),
                    series=str(doc.series),
                    model=doc.model,
                    access_key=doc.access_key,
                    operation_type=op_label,
                    purpose=str(doc.purpose),
                    status=doc.status,
                    entity_name=doc.recipient_name,
                    entity_cnpj_cpf=doc.recipient_cnpj_cpf,
                    cfop=doc.items[0].cfop if doc.items else "5102",
                    vProd=v_prod,
                    vBC=v_bc,
                    vICMS=v_icms,
                    vFCP=v_fcp,
                    vST=v_st,
                    vIPI=v_ipi,
                    vPIS=v_pis,
                    vCOFINS=v_cofins,
                    vIBS=v_ibs,
                    vCBS=v_cbs,
                    vNF=v_nf,
                    notes_or_reason=doc.sefaz_reason or doc.additional_information,
                )
            )

        totals.total_documents = len(docs)
        totals.total_vProd = round(tot_vProd, 2)
        totals.total_vBC_ICMS = round(tot_vBC, 2)
        totals.total_vICMS = round(tot_vICMS, 2)
        totals.total_vFCP = round(tot_vFCP, 2)
        totals.total_vST = round(tot_vST, 2)
        totals.total_vIPI = round(tot_vIPI, 2)
        totals.total_vPIS = round(tot_vPIS, 2)
        totals.total_vCOFINS = round(tot_vCOFINS, 2)
        totals.total_vBC_IBS = round(tot_vBC_IBS, 2)
        totals.total_vIBS = round(tot_vIBS, 2)
        totals.total_vBC_CBS = round(tot_vBC_CBS, 2)
        totals.total_vCBS = round(tot_vCBS, 2)
        totals.total_vNF = round(tot_vNF, 2)

    response = FiscalReportSummaryResponse(
        report_type=rep_type,
        company_id=company_id,
        generated_at=datetime.now(timezone.utc).isoformat(),
        filter_applied=filter_dict,
        totals=totals,
        rows=rows,
        grouped_rows=grouped,
    )

    if (payload.export_format or "").lower() == "csv":
        response.csv_content = export_fiscal_report_csv(response)

    return response


def export_fiscal_report_csv(report: FiscalReportSummaryResponse) -> str:
    """
    Exporta o relatório fiscal gerado para formato CSV (separado por ponto-e-vírgula).
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)

    # Cabeçalho do Relatório
    writer.writerow(["RELATORIO FISCAL TELE-SYS ERP"])
    writer.writerow(["Tipo do Relatorio", report.report_type])
    writer.writerow(["Empresa ID", str(report.company_id)])
    writer.writerow(["Gerado Em", report.generated_at])
    writer.writerow(["Filtros Aplicados", json.dumps(report.filter_applied)])
    writer.writerow([])

    # Totais Consolidados
    writer.writerow(["TOTAIS CONSOLIDADOS"])
    writer.writerow(["Total Documentos", report.totals.total_documents])
    writer.writerow(["Total vProd", f"{report.totals.total_vProd:.2f}"])
    writer.writerow(["Total vBC ICMS", f"{report.totals.total_vBC_ICMS:.2f}"])
    writer.writerow(["Total vICMS", f"{report.totals.total_vICMS:.2f}"])
    writer.writerow(["Total vFCP", f"{report.totals.total_vFCP:.2f}"])
    writer.writerow(["Total vST", f"{report.totals.total_vST:.2f}"])
    writer.writerow(["Total vIPI", f"{report.totals.total_vIPI:.2f}"])
    writer.writerow(["Total vPIS", f"{report.totals.total_vPIS:.2f}"])
    writer.writerow(["Total vCOFINS", f"{report.totals.total_vCOFINS:.2f}"])
    writer.writerow(["Total vIBS (RTC)", f"{report.totals.total_vIBS:.2f}"])
    writer.writerow(["Total vCBS (RTC)", f"{report.totals.total_vCBS:.2f}"])
    writer.writerow(["Total vNF", f"{report.totals.total_vNF:.2f}"])
    writer.writerow([])

    if report.grouped_rows:
        writer.writerow(["AGRUPAMENTOS"])
        writer.writerow(["Codigo", "Descricao", "Qtd Docs", "Qtd Itens", "vProd", "vBC", "vICMS", "vNF"])
        for g in report.grouped_rows:
            writer.writerow([
                g.key_code,
                g.description,
                g.count_docs,
                g.count_items,
                f"{g.vProd:.2f}",
                f"{g.vBC:.2f}",
                f"{g.vICMS:.2f}",
                f"{g.vNF:.2f}",
            ])
        writer.writerow([])

    if report.rows:
        writer.writerow(["DETALHAMENTO DOS DOCUMENTOS"])
        writer.writerow([
            "Data", "Numero", "Serie", "Modelo", "Chave de Acesso",
            "Tipo", "Finalidade", "Status", "Nome Destinatario/Emitente",
            "CNPJ/CPF", "CFOP", "vProd", "vBC", "vICMS", "vFCP", "vST",
            "vIPI", "vPIS", "vCOFINS", "vIBS", "vCBS", "vNF", "Observacoes/Motivo"
        ])
        for r in report.rows:
            writer.writerow([
                r.date,
                r.document_number,
                r.series,
                r.model,
                r.access_key or "",
                r.operation_type,
                r.purpose,
                r.status,
                r.entity_name,
                r.entity_cnpj_cpf,
                r.cfop or "",
                f"{r.vProd:.2f}",
                f"{r.vBC:.2f}",
                f"{r.vICMS:.2f}",
                f"{r.vFCP:.2f}",
                f"{r.vST:.2f}",
                f"{r.vIPI:.2f}",
                f"{r.vPIS:.2f}",
                f"{r.vCOFINS:.2f}",
                f"{r.vIBS:.2f}",
                f"{r.vCBS:.2f}",
                f"{r.vNF:.2f}",
                r.notes_or_reason or "",
            ])

    return output.getvalue()
