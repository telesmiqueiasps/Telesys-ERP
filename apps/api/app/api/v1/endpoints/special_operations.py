import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.special_operation import SpecialOperationCreateRequest, ComplementaryAdjustmentCreateRequest
from app.schemas.nfe import NfeDocumentResponse
from app.services.special_operation_service import (
    create_special_operation_nfe,
    create_complementary_adjustment_nfe,
)

router = APIRouter()

# Fixed tenant ID mock for current stage
MOCK_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post("/nfe-draft", response_model=NfeDocumentResponse, status_code=201)
def create_special_operation_draft(
    payload: SpecialOperationCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Cria rascunho de NF-e para Operações Especiais e Não-Vendas:
    - Devolução de Compra / Venda (exige Chave Referenciada)
    - Remessa para Conserto / Demonstração (sem lançamento financeiro)
    - Transferência entre Filiais (sem lançamento financeiro)
    - Bonificação / Doação (sem lançamento financeiro)
    """
    try:
        doc = create_special_operation_nfe(
            db=db,
            tenant_id=MOCK_TENANT_ID,
            payload=payload,
        )
        return doc
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no processamento da Operação Especial: {str(e)}")


@router.post("/complementary-adjustment", response_model=NfeDocumentResponse, status_code=201)
def create_complementary_adjustment_draft(
    payload: ComplementaryAdjustmentCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Cria NF-e Complementar (finNFe 2) ou de Ajuste (finNFe 3):
    - Requer obrigatoriamente a Chave de Acesso da NF-e original (44 dígitos numéricos)
    - Requer motivo/justificativa detalhado (armazenado nas Informações Adicionais / <infAdic><infCpl>)
    - Valida a finalidade (2=Complementar, 3=Ajuste)
    - NÃO substitui ou altera o documento original
    """
    try:
        doc = create_complementary_adjustment_nfe(
            db=db,
            tenant_id=MOCK_TENANT_ID,
            payload=payload,
        )
        return doc
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no processamento de NF-e Complementar/Ajuste: {str(e)}")

