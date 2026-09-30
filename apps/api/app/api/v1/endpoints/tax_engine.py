from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.tax_engine import TaxCalculationInput, TaxSnapshot
from app.services.tax_engine import TaxEngine

router = APIRouter()


@router.post("/calculate", response_model=TaxSnapshot)
def calculate_tax_snapshot(
    payload: TaxCalculationInput,
    current_user: User = Depends(get_current_user),
):
    """
    Executa o cálculo fiscal determinístico e imutável para um item.
    Retorna o TaxSnapshot completo com a memória de cálculo e audit_trail.
    """
    try:
        return TaxEngine.calculate_item_tax(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no cálculo fiscal: {str(e)}")
