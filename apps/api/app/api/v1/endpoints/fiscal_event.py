import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.fiscal_event import FiscalEvent, FiscalInutilization
from app.schemas.fiscal_event import (
    FiscalCancelRequest,
    FiscalCceRequest,
    FiscalInutilizationRequest,
    FiscalEventResponse,
    FiscalInutilizationResponse,
)
from app.services.fiscal_event_service import cancel_nfe, cce_nfe, inutilizar_numeracao

router = APIRouter()


@router.post("/cancel", response_model=FiscalEventResponse, status_code=status.HTTP_201_CREATED)
def execute_cancel(
    payload: FiscalCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Executa o cancelamento homologado de uma NF-e / NFC-e Autorizada (tpEvento 110111).
    Transiciona o status da nota para CANCELLED.
    """
    try:
        return cancel_nfe(db, current_user.tenant_id, payload, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao cancelar NF-e: {str(e)}")


@router.post("/cce", response_model=FiscalEventResponse, status_code=status.HTTP_201_CREATED)
def execute_cce(
    payload: FiscalCceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Registra uma Carta de Correção Eletrônica (CC-e - tpEvento 110110).
    """
    try:
        return cce_nfe(db, current_user.tenant_id, payload, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao transmitir Carta de Correção: {str(e)}")


@router.post("/inutilizar", response_model=FiscalInutilizationResponse, status_code=status.HTTP_201_CREATED)
def execute_inutilization(
    payload: FiscalInutilizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Transmite um pedido de Inutilização de Faixa de Numeração não utilizada para a SEFAZ.
    """
    try:
        return inutilizar_numeracao(db, current_user.tenant_id, payload, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao inutilizar numeração: {str(e)}")


@router.get("/nfe/{nfe_id}", response_model=List[FiscalEventResponse])
def list_nfe_events(
    nfe_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lista todos os eventos (Cancelamentos, CC-es, Manifestações) vinculados a uma Nota Fiscal.
    """
    events = db.scalars(
        select(FiscalEvent)
        .where(FiscalEvent.nfe_id == nfe_id, FiscalEvent.tenant_id == current_user.tenant_id)
        .order_by(FiscalEvent.seq_number.asc(), FiscalEvent.created_at.asc())
    ).all()
    return list(events)
