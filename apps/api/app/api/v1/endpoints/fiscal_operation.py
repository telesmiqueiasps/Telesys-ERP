import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.fiscal_operation import (
    FiscalOperationCreate,
    FiscalOperationUpdate,
    FiscalOperationResponse,
    FiscalScenarioRuleCreate,
    FiscalScenarioRuleUpdate,
    FiscalScenarioRuleResponse,
    FiscalScenarioMatchRequest,
    FiscalScenarioMatchResult,
)
from app.services.fiscal_operation import (
    get_company_fiscal_operations,
    create_fiscal_operation,
    update_fiscal_operation,
    add_scenario_rule,
    update_scenario_rule,
    delete_scenario_rule,
    resolve_fiscal_scenario,
)

router = APIRouter()


@router.get("", response_model=List[FiscalOperationResponse])
def list_fiscal_operations(
    company_id: uuid.UUID = Query(..., description="ID da Empresa/Filial"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lista todas as operações fiscais da empresa e suas regras de cenário.
    Se não existirem operações cadastradas, gera automaticamente as operações padrão.
    """
    return get_company_fiscal_operations(db, current_user.tenant_id, company_id)


@router.post("", response_model=FiscalOperationResponse, status_code=status.HTTP_211_CREATED if hasattr(status, 'HTTP_211_CREATED') else status.HTTP_201_CREATED)
def create_new_fiscal_operation(
    payload: FiscalOperationCreate,
    company_id: uuid.UUID = Query(..., description="ID da Empresa/Filial"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cria uma nova operação fiscal e suas regras de cenário.
    """
    try:
        return create_fiscal_operation(db, current_user.tenant_id, company_id, payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{operation_id}", response_model=FiscalOperationResponse)
def update_existing_fiscal_operation(
    operation_id: uuid.UUID,
    payload: FiscalOperationUpdate,
    company_id: uuid.UUID = Query(..., description="ID da Empresa/Filial"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Atualiza dados de uma operação fiscal.
    """
    try:
        return update_fiscal_operation(db, current_user.tenant_id, company_id, operation_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{operation_id}/rules", response_model=FiscalScenarioRuleResponse, status_code=status.HTTP_201_CREATED)
def create_scenario_rule(
    operation_id: uuid.UUID,
    payload: FiscalScenarioRuleCreate,
    company_id: uuid.UUID = Query(..., description="ID da Empresa/Filial"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Adiciona uma nova regra de cenário a uma operação fiscal existente.
    """
    try:
        return add_scenario_rule(db, current_user.tenant_id, company_id, operation_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/rules/{rule_id}", response_model=FiscalScenarioRuleResponse)
def update_existing_scenario_rule(
    rule_id: uuid.UUID,
    payload: FiscalScenarioRuleUpdate,
    company_id: uuid.UUID = Query(..., description="ID da Empresa/Filial"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Atualiza uma regra de cenário fiscal existente.
    """
    try:
        return update_scenario_rule(db, current_user.tenant_id, company_id, rule_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_scenario_rule(
    rule_id: uuid.UUID,
    company_id: uuid.UUID = Query(..., description="ID da Empresa/Filial"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove uma regra de cenário fiscal.
    """
    try:
        delete_scenario_rule(db, current_user.tenant_id, company_id, rule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/match-scenario", response_model=FiscalScenarioMatchResult)
def match_fiscal_scenario(
    payload: FiscalScenarioMatchRequest,
    company_id: uuid.UUID = Query(..., description="ID da Empresa/Filial"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Testa e simula o motor de resolução de cenário fiscal e CFOP.
    """
    return resolve_fiscal_scenario(db, current_user.tenant_id, company_id, payload)
