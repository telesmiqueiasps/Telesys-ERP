import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.fiscal_homologation import HomologationSuiteReportResponse
from app.services.fiscal_homologation_service import run_fiscal_homologation_suite

router = APIRouter()

# Fixed tenant ID mock for current stage
MOCK_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post("/run", response_model=HomologationSuiteReportResponse, status_code=200)
def run_fiscal_homologation_endpoint(
    company_id: uuid.UUID = Query(..., description="ID da Empresa a ser homologada"),
    db: Session = Depends(get_db),
):
    """
    Executa a Suíte Completa de Homologação e Validação Fiscal End-to-End.
    Testa os 12 Módulos Fiscais Fundamentais:
    1. Certificado Digital A1 & Criptografia
    2. Autorização de NF-e (55) e NFC-e (65)
    3. Tratamento e Normalização de Rejeições SEFAZ
    4. Cancelamento de Documentos Fiscais
    5. Carta de Correção Eletrônica (CC-e 110110)
    6. Inutilização de Faixas Numéricas
    7. Contingência Offline & Fila Local
    8. Proteção Contra Duplicidade de Chave
    9. Operações de Devolução (finNFe 4 com Chave Referenciada)
    10. Importação de Compras por XML (Fase 1 e 2)
    11. Nota Fiscal de Serviços Eletrônica (NFS-e Padrão Nacional)
    12. Reconciliação, Idempotência e Recuperação de Rede
    """
    try:
        report = run_fiscal_homologation_suite(
            db=db,
            tenant_id=MOCK_TENANT_ID,
            company_id=company_id,
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro durante a execução da suíte de homologação fiscal: {str(e)}")
