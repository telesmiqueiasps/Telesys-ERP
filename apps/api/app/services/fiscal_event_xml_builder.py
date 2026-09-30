import re
from datetime import datetime, timezone
from typing import Optional
from xml.etree import ElementTree as ET

from app.services.nfe_xml_builder import UF_IBGE_CODES


class FiscalEventXmlBuilder:
    @staticmethod
    def build_event_xml(
        access_key: str,
        event_type: str,
        seq_number: int,
        uf: str,
        cnpj_or_cpf: str,
        justification_or_correction: str,
        protocol_number: Optional[str] = None,
        environment: int = 2,
        issue_date: Optional[datetime] = None
    ) -> str:
        """
        Constrói o XML rascunho de Evento SEFAZ v4.00 (Cancelamento 110111 ou CC-e 110110).
        """
        if issue_date is None:
            issue_date = datetime.now(timezone.utc)

        dh_str = issue_date.strftime("%Y-%m-%dT%H:%M:%S%z")
        if not dh_str.endswith("+00:00") and not re.search(r"[+-]\d{2}:\d{2}$", dh_str):
            dh_str += "-03:00"

        cUF = UF_IBGE_CODES.get(uf.upper().strip(), 35)
        clean_doc = re.sub(r"\D", "", cnpj_or_cpf).zfill(14)

        event_id = f"ID{event_type}{access_key}{seq_number:02d}"

        ns = "http://www.portalfiscal.inf.br/nfe"
        ET.register_namespace("", ns)

        envEvento = ET.Element("envEvento", attrib={"xmlns": ns, "versao": "1.00"})
        ET.SubElement(envEvento, "idLote").text = "1"

        evento = ET.SubElement(envEvento, "evento", attrib={"versao": "1.00"})
        infEvento = ET.SubElement(evento, "infEvento", attrib={"Id": event_id})
        
        ET.SubElement(infEvento, "cOrgao").text = str(cUF)
        ET.SubElement(infEvento, "tpAmb").text = str(environment)
        if len(clean_doc) == 11:
            ET.SubElement(infEvento, "CPF").text = clean_doc
        else:
            ET.SubElement(infEvento, "CNPJ").text = clean_doc
        
        ET.SubElement(infEvento, "chNFe").text = access_key
        ET.SubElement(infEvento, "dhEvento").text = dh_str
        ET.SubElement(infEvento, "tpEvento").text = event_type
        ET.SubElement(infEvento, "nSeqEvento").text = str(seq_number)
        ET.SubElement(infEvento, "verEvento").text = "1.00"

        detEvento = ET.SubElement(infEvento, "detEvento", attrib={"versao": "1.00"})

        if event_type == "110111":  # Cancelamento
            ET.SubElement(detEvento, "descEvento").text = "Cancelamento"
            ET.SubElement(detEvento, "nProt").text = protocol_number or "135260001234567"
            ET.SubElement(detEvento, "xJust").text = justification_or_correction
        elif event_type == "110110":  # CC-e
            ET.SubElement(detEvento, "descEvento").text = "Carta de Correcao"
            ET.SubElement(detEvento, "xCorrecao").text = justification_or_correction
            ET.SubElement(detEvento, "xCondUso").text = (
                "A Carta de Correcao e registrada no TP. Nao produz efeitos se a correcao for relacionada com: "
                "I - as variaveis que determinam o valor do imposto; II - a correcao de dados cadastrais que implique mudanca do remetente ou do destinatario; "
                "III - a data de emissao ou de saida."
            )

        raw_xml_str = ET.tostring(envEvento, encoding="utf-8").decode("utf-8")
        return raw_xml_str

    @staticmethod
    def build_inutilization_xml(
        uf: str,
        year: int,
        cnpj: str,
        model: str,
        series: int,
        start_number: int,
        end_number: int,
        justification: str,
        environment: int = 2
    ) -> str:
        """
        Constrói o XML de Inutilização de Faixa de Numeração <inutNFe versao="4.00">.
        """
        cUF = UF_IBGE_CODES.get(uf.upper().strip(), 35)
        clean_cnpj = re.sub(r"\D", "", cnpj).zfill(14)
        yy = str(year)[-2:]
        mod_str = str(model).zfill(2)
        serie_str = str(series).zfill(3)
        nIni_str = str(start_number).zfill(9)
        nFin_str = str(end_number).zfill(9)

        inut_id = f"ID{cUF:02d}{yy}{clean_cnpj}{mod_str}{serie_str}{nIni_str}{nFin_str}"

        ns = "http://www.portalfiscal.inf.br/nfe"
        ET.register_namespace("", ns)

        inutNFe = ET.Element("inutNFe", attrib={"xmlns": ns, "versao": "4.00"})
        infInut = ET.SubElement(inutNFe, "infInut", attrib={"Id": inut_id})

        ET.SubElement(infInut, "tpAmb").text = str(environment)
        ET.SubElement(infInut, "xServ").text = "INUTILIZAR"
        ET.SubElement(infInut, "cUF").text = str(cUF)
        ET.SubElement(infInut, "ano").text = str(yy)
        ET.SubElement(infInut, "CNPJ").text = clean_cnpj
        ET.SubElement(infInut, "mod").text = mod_str
        ET.SubElement(infInut, "serie").text = str(series)
        ET.SubElement(infInut, "nNFIni").text = str(start_number)
        ET.SubElement(infInut, "nNFFin").text = str(end_number)
        ET.SubElement(infInut, "xJust").text = justification

        return ET.tostring(inutNFe, encoding="utf-8").decode("utf-8")

    @staticmethod
    def build_proc_evento_xml(
        signed_event_xml: str,
        protocol_number: str,
        sefaz_status_code: int = 135,
        sefaz_reason: str = "Evento registrado e vinculado a NF-e",
        dh_rec: Optional[datetime] = None
    ) -> str:
        """
        Empacota o XML assinado do evento com a resposta da SEFAZ <retEvento> formando <procEventoNFe>.
        """
        if dh_rec is None:
            dh_rec = datetime.now(timezone.utc)

        dh_str = dh_rec.strftime("%Y-%m-%dT%H:%M:%S%z")
        if not dh_str.endswith("+00:00") and not re.search(r"[+-]\d{2}:\d{2}$", dh_str):
            dh_str += "-03:00"

        ret_evento_xml = f"""<retEvento versao="1.00" xmlns="http://www.portalfiscal.inf.br/nfe">
  <infEvento>
    <tpAmb>2</tpAmb>
    <verAplic>2.0.0</verAplic>
    <cOrgao>35</cOrgao>
    <cStat>{sefaz_status_code}</cStat>
    <xMotivo>{sefaz_reason}</xMotivo>
    <nProt>{protocol_number}</nProt>
    <dhRegEvento>{dh_str}</dhRegEvento>
  </infEvento>
</retEvento>"""

        proc_xml = f"""<procEventoNFe versao="1.00" xmlns="http://www.portalfiscal.inf.br/nfe">
{signed_event_xml}
{ret_evento_xml}
</procEventoNFe>"""

        return proc_xml
