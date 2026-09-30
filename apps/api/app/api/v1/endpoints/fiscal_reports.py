import uuid
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.fiscal_report import FiscalReportFilterRequest, FiscalReportSummaryResponse
from app.services.fiscal_report_service import generate_fiscal_report, export_fiscal_report_csv

router = APIRouter()

# Fixed tenant ID mock for current stage
MOCK_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post("/generate", response_model=FiscalReportSummaryResponse, status_code=200)
def generate_fiscal_report_endpoint(
    payload: FiscalReportFilterRequest,
    db: Session = Depends(get_db),
):
    """
    Gera relatório fiscal consolidado e detalhado em formato JSON (ou CSV se export_format='csv'):
    Tipos suportados:
    - EMITTED (Notas Emitidas / Saídas)
    - RECEIVED (Notas Recebidas / Compras)
    - CANCELLED (Notas Canceladas)
    - INUTILIZED (Faixas de Numeração Inutilizadas)
    - REJECTED (Notas Rejeitadas pela SEFAZ)
    - CONTINGENCY (Vendas / Notas em Contingência Offline)
    - EVENTS (Histórico de Eventos Fiscais - CC-e, Cancelamento, Ciência, Confirmação)
    - BY_CFOP (Agrupamento por Código CFOP)
    - BY_CST (Agrupamento por CST / CSOSN)
    - TAX_SUMMARY (Consolidado Geral de Tributos - ICMS, FCP, ST, DIFAL, IPI, PIS, COFINS, IBS, CBS)
    - RETURNS (Devoluções de Compra e Venda)
    - PENDENCIES (Pendências / Rascunhos / Inconformidades Fiscais)
    """
    try:
        report = generate_fiscal_report(
            db=db,
            tenant_id=MOCK_TENANT_ID,
            payload=payload,
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na geração do relatório fiscal: {str(e)}")


@router.post("/export-csv", status_code=200)
def export_fiscal_report_csv_endpoint(
    payload: FiscalReportFilterRequest,
    db: Session = Depends(get_db),
):
    """
    Gera e faz o download direto do relatório fiscal formatado em arquivo CSV.
    """
    try:
        payload.export_format = "csv"
        report = generate_fiscal_report(
            db=db,
            tenant_id=MOCK_TENANT_ID,
            payload=payload,
        )
        csv_str = report.csv_content or export_fiscal_report_csv(report)
        filename = f"relatorio_fiscal_{payload.report_type.lower()}.csv"

        return Response(
            content=csv_str,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na exportação em CSV: {str(e)}")
