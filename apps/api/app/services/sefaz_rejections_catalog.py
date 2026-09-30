from typing import Dict, List, Optional
from app.schemas.rejections import SefazRejectionCatalogEntry


class SefazRejectionsCatalog:
    """Catálogo Oficial de Rejeições SEFAZ com diagnósticos e soluções operacionais.
    
    ATENÇÃO: Soluções operacionais apresentadas somente quando respaldadas
    pela documentação técnica oficial SEFAZ (MOC 7.0 / Notas Técnicas).
    """

    _CATALOG: Dict[int, SefazRejectionCatalogEntry] = {
        204: SefazRejectionCatalogEntry(
            code=204,
            official_message="Rejeição: Duplicidade de NF-e com diferença na Chave de Acesso",
            affected_fields=["chNFe", "nNF", "serie"],
            operational_solution=(
                "Verifique se a nota de mesmo número e série já foi autorizada na SEFAZ com outra chave de acesso. "
                "Altere o número da nota ou consulte a SEFAZ para reaver o XML autorizado."
            ),
        ),
        208: SefazRejectionCatalogEntry(
            code=208,
            official_message="Rejeição: CNPJ do emitente inválido",
            affected_fields=["emit.CNPJ"],
            operational_solution=(
                "Corrija o CNPJ do emitente no cadastro da empresa para um número de CNPJ válido "
                "com 14 dígitos e dígito verificador correto."
            ),
        ),
        215: SefazRejectionCatalogEntry(
            code=215,
            official_message="Rejeição: Falha no XML",
            affected_fields=["xml"],
            operational_solution=(
                "Verifique a estrutura do XML gerado contra o Schema XSD da SEFAZ v4.00, "
                "garantindo a codificação UTF-8 e a ausência de caracteres especiais incorretos."
            ),
        ),
        225: SefazRejectionCatalogEntry(
            code=225,
            official_message="Rejeição: Falha no Schema XML do lote de NFe",
            affected_fields=["xml"],
            operational_solution=(
                "Ajuste os nomes das tags, namespace (http://www.portalfiscal.inf.br/nfe) "
                "e ordem dos elementos de acordo com o Manual de Orientação do Contribuinte (MOC)."
            ),
        ),
        230: SefazRejectionCatalogEntry(
            code=230,
            official_message="Rejeição: IE do emitente não cadastrada",
            affected_fields=["emit.IE"],
            operational_solution=(
                "Confira o número da Inscrição Estadual (IE) do emitente no SINTEGRA ou CCC. "
                "Caso a empresa seja isenta ou alterou o cadastro, atualize a IE no perfil fiscal."
            ),
        ),
        232: SefazRejectionCatalogEntry(
            code=232,
            official_message="Rejeição: IE do destinatário não informada",
            affected_fields=["dest.IE", "dest.indIEDest"],
            operational_solution=(
                "Para destinatário contribuinte do ICMS (indIEDest=1), a Inscrição Estadual é obrigatória. "
                "Informe a IE válida do destinatário ou ajuste o indicador indIEDest conforme o cadastro."
            ),
        ),
        245: SefazRejectionCatalogEntry(
            code=245,
            official_message="Rejeição: CNPJ Emitente não cadastrado",
            affected_fields=["emit.CNPJ"],
            operational_solution=(
                "Verifique se o CNPJ está ativo e cadastrado na SEFAZ do estado de origem. "
                "Em ambiente de homologação, certifique-se de ter autorização no ambiente de testes."
            ),
        ),
        539: SefazRejectionCatalogEntry(
            code=539,
            official_message="Rejeição: Duplicidade de NF-e com diferença na Chave de Acesso",
            affected_fields=["chNFe", "nNF", "serie"],
            operational_solution=(
                "Nota fiscal já transmitida com este número e série mas com chave de acesso diferente. "
                "Altere a numeração sequencial da NF-e no ERP."
            ),
        ),
        610: SefazRejectionCatalogEntry(
            code=610,
            official_message="Rejeição: Total da NF difere do somatório dos valores que compõem o valor total da NF",
            affected_fields=["total.ICMSTot.vNF"],
            operational_solution=(
                "Recalcule o valor total da NF-e (vProd - vDesc - vICMSDeson + vST + vFCPST + vFrete + vSeg + vOutro + vII + vIPI). "
                "O valor informado na tag vNF deve ser idêntico ao somatório de seus componentes."
            ),
        ),
        778: SefazRejectionCatalogEntry(
            code=778,
            official_message="Rejeição: Informado nItemPedido para item que não possui numeração de item de pedido de compra",
            affected_fields=["det[].prod.nItemPed"],
            operational_solution=(
                "Remova a tag nItemPed se não houver um pedido de compra vinculado no item "
                "ou informe o número do item do pedido correspondente."
            ),
        ),
        805: SefazRejectionCatalogEntry(
            code=805,
            official_message="Rejeição: A SEFAZ do destinatário não permite a operação",
            affected_fields=["dest.UF"],
            operational_solution=(
                "Verifique se o destinatário está habilitado/ativo no Cadastro Central de Contribuintes (CCC) "
                "do estado de destino ou se há bloqueio fiscal/suspensão da IE."
            ),
        ),
        999: SefazRejectionCatalogEntry(
            code=999,
            official_message="Rejeição: Erro Não Catalogado / Falha de comunicação",
            affected_fields=["sefaz"],
            operational_solution=(
                "Consulte a disponibilidade do serviço no Portal da SEFAZ. "
                "Caso persista, tente novamente em instantes ou acione a contingência SVC."
            ),
        ),
    }

    @classmethod
    def get_rejection(cls, code: int) -> Optional[SefazRejectionCatalogEntry]:
        return cls._CATALOG.get(code)

    @classmethod
    def lookup_operational_solution(cls, code: int) -> Optional[str]:
        entry = cls._CATALOG.get(code)
        return entry.operational_solution if entry else None

    @classmethod
    def list_catalog(cls) -> List[SefazRejectionCatalogEntry]:
        return list(cls._CATALOG.values())
