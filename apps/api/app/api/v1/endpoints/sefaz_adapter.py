from fastapi import APIRouter, Depends, Query, HTTPException
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.sefaz import SefazRequest, SefazResponse
from app.services.sefaz_adapter import SefazServiceAdapter

router = APIRouter()


@router.post("/autorizar", response_model=SefazResponse)
def autorizar_lote_sefaz(
    payload: SefazRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Transmite um lote de NF-e / NFC-e para o adaptador SEFAZ e retorna a resposta normalizada SefazResponse.
    """
    try:
        return SefazServiceAdapter.autorizar_nfe(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no adaptador SEFAZ: {str(e)}")


@router.get("/consultar", response_model=SefazResponse)
def consultar_nfe_sefaz(
    chave_acesso: str = Query(..., min_length=44, max_length=44, description="Chave de acesso de 44 dígitos"),
    uf: str = Query("SP", min_length=2, max_length=2, description="UF da empresa"),
    ambiente: int = Query(2, description="1=Produção, 2=Homologação"),
    current_user: User = Depends(get_current_user),
):
    """
    Consulta o status do processamento de uma nota fiscal por chave de acesso.
    """
    return SefazServiceAdapter.consultar_nfe(access_key=chave_acesso, uf=uf, environment=ambiente)


@router.get("/status-servico", response_model=SefazResponse)
def status_servico_sefaz(
    uf: str = Query("SP", min_length=2, max_length=2, description="UF da empresa"),
    ambiente: int = Query(2, description="1=Produção, 2=Homologação"),
    current_user: User = Depends(get_current_user),
):
    """
    Verifica a disponibilidade do servidor WebService SEFAZ da UF.
    """
    return SefazServiceAdapter.consultar_status_servico(uf=uf, environment=ambiente)
