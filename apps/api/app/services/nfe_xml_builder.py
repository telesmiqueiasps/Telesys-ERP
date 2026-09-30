import random
import re
from typing import Optional
from datetime import datetime, timezone
from xml.etree import ElementTree as ET
from xml.dom import minidom

# Mapeamento de UFs para Código Ibge (cUF)
UF_IBGE_CODES = {
    "RO": 11, "AC": 12, "AM": 13, "RR": 14, "PA": 15, "AP": 16, "TO": 17,
    "MA": 21, "PI": 22, "CE": 23, "RN": 24, "PB": 25, "PE": 26, "AL": 27,
    "SE": 28, "BA": 29, "MG": 31, "ES": 32, "RJ": 33, "SP": 35, "PR": 41,
    "SC": 42, "RS": 43, "MS": 50, "MT": 51, "GO": 52, "DF": 53
}


def calculate_mod11_dv(key_43: str) -> int:
    """
    Calcula o Dígito Verificador (cDV) Módulo 11 da Chave de Acesso SEFAZ.
    Pesos de 2 a 9 da direita para a esquerda.
    """
    if len(key_43) != 43 or not key_43.isdigit():
        raise ValueError("A chave de entrada para o cálculo do DV deve ter exatamente 43 dígitos numéricos.")

    multipliers = [2, 3, 4, 5, 6, 7, 8, 9]
    total_sum = 0
    weight_idx = 0

    for digit in reversed(key_43):
        total_sum += int(digit) * multipliers[weight_idx]
        weight_idx = (weight_idx + 1) % len(multipliers)

    remainder = total_sum % 11
    if remainder in [0, 1]:
        return 0
    else:
        return 11 - remainder


def generate_access_key(
    uf: str,
    issue_date: datetime,
    cnpj: str,
    model: int | str,
    series: int,
    number: int,
    issue_type: int = 1,
    cNF: int | str | None = None
) -> str:
    """
    Gera deterministicamente a Chave de Acesso de 44 dígitos da NF-e (Modelo 55 / 65).
    Estrutura: cUF(2) + AAMM(4) + CNPJ(14) + mod(2) + serie(3) + nNF(9) + tpEmis(1) + cNF(8) + cDV(1)
    """
    clean_uf = uf.upper().strip()
    cUF = UF_IBGE_CODES.get(clean_uf, 35)

    aamm = issue_date.strftime("%y%m")
    clean_cnpj = re.sub(r"\D", "", cnpj).zfill(14)
    mod_str = str(model).zfill(2)
    series_str = str(series).zfill(3)
    nNF_str = str(number).zfill(9)
    tpEmis_str = str(issue_type).zfill(1)

    if cNF is None:
        cNF_num = random.randint(10000000, 99999999)
    else:
        cNF_num = int(cNF)
    cNF_str = str(cNF_num).zfill(8)

    key_43 = f"{cUF:02d}{aamm}{clean_cnpj}{mod_str}{series_str}{nNF_str}{tpEmis_str}{cNF_str}"
    cDV = calculate_mod11_dv(key_43)

    return f"{key_43}{cDV}"


class NfeXmlBuilder:
    @staticmethod
    def build_nfe_xml(doc) -> str:
        """
        Constrói o XML da NF-e v4.00 em conformidade com o Manual de Integração SEFAZ.
        Separação estrita de lógica: consome o NfeDocument e os TaxSnapshots.
        """
        ns = "http://www.portalfiscal.inf.br/nfe"
        ET.register_namespace("", ns)

        NFe = ET.Element("NFe", attrib={"xmlns": ns})
        infNFe = ET.SubElement(NFe, "infNFe", attrib={
            "Id": f"NFe{doc.access_key}",
            "versao": "4.00"
        })

        # --- <ide> Identificação da NF-e / NFC-e ---
        ide = ET.SubElement(infNFe, "ide")
        cUF_val = UF_IBGE_CODES.get(doc.issuer_uf.upper(), 35)
        ET.SubElement(ide, "cUF").text = str(cUF_val)
        ET.SubElement(ide, "cNF").text = doc.access_key[35:43]
        ET.SubElement(ide, "natOp").text = doc.nature_of_operation[:60]
        model_str = str(doc.model).zfill(2)
        ET.SubElement(ide, "mod").text = model_str
        ET.SubElement(ide, "serie").text = str(doc.series)
        ET.SubElement(ide, "nNF").text = str(doc.number)
        
        created_dt = getattr(doc, "created_at", None) or datetime.now(timezone.utc)
        issue_dh = created_dt.strftime("%Y-%m-%dT%H:%M:%S%z")
        if not issue_dh.endswith("+00:00") and not re.search(r"[+-]\d{2}:\d{2}$", issue_dh):
            issue_dh += "-03:00"
        ET.SubElement(ide, "dhEmi").text = issue_dh

        tpNF_val = str(getattr(doc, "operation_type_nfe", 1))
        ET.SubElement(ide, "tpNF").text = tpNF_val
        ET.SubElement(ide, "idDest").text = "1" if doc.issuer_uf.upper() == doc.recipient_uf.upper() else "2"  # 1=Interna, 2=Interestadual
        ET.SubElement(ide, "cMunFG").text = "3550308"  # Ex: São Paulo
        
        # tpImp: 1=DANFE Retrato (Modelo 55), 4=DANFE NFC-e (Modelo 65)
        tpImp_val = "4" if model_str == "65" else "1"
        ET.SubElement(ide, "tpImp").text = tpImp_val
        ET.SubElement(ide, "tpEmis").text = str(doc.issue_type)
        ET.SubElement(ide, "cDV").text = doc.access_key[43]
        ET.SubElement(ide, "tpAmb").text = str(doc.environment)
        finNFe_val = str(getattr(doc, "purpose", 1))
        ET.SubElement(ide, "finNFe").text = finNFe_val
        ET.SubElement(ide, "indFinal").text = "1" if (model_str == "65" or doc.recipient_is_final_consumer) else "0"
        ET.SubElement(ide, "indPres").text = "1"   # Presencial
        ET.SubElement(ide, "procEmi").text = "0"   # Aplicativo do Contribuinte
        ET.SubElement(ide, "verProc").text = "2.0.0"

        # Nota Referenciada (se houver)
        if doc.referenced_nfe_key:
            NFref = ET.SubElement(ide, "NFref")
            ET.SubElement(NFref, "refNFe").text = doc.referenced_nfe_key

        # --- <emit> Emitente ---
        emit = ET.SubElement(infNFe, "emit")
        ET.SubElement(emit, "CNPJ").text = re.sub(r"\D", "", doc.issuer_cnpj).zfill(14)
        ET.SubElement(emit, "xNome").text = doc.issuer_name[:60]
        if doc.issuer_trade_name:
            ET.SubElement(emit, "xFant").text = doc.issuer_trade_name[:60]

        enderEmit = ET.SubElement(emit, "enderEmit")
        addr = doc.issuer_address or {}
        ET.SubElement(enderEmit, "xLgr").text = str(addr.get("xLgr", "Rua Principal"))[:60]
        ET.SubElement(enderEmit, "nro").text = str(addr.get("nro", "100"))[:60]
        ET.SubElement(enderEmit, "xBairro").text = str(addr.get("xBairro", "Centro"))[:60]
        ET.SubElement(enderEmit, "cMun").text = str(addr.get("cMun", "3550308"))
        ET.SubElement(enderEmit, "xMun").text = str(addr.get("xMun", "Sao Paulo"))[:60]
        ET.SubElement(enderEmit, "UF").text = doc.issuer_uf.upper()
        ET.SubElement(enderEmit, "CEP").text = str(addr.get("CEP", "01001000")).replace("-", "")

        if doc.issuer_ie:
            ET.SubElement(emit, "IE").text = re.sub(r"\D", "", doc.issuer_ie)
        else:
            ET.SubElement(emit, "IE").text = "ISENTO"
        ET.SubElement(emit, "CRT").text = str(doc.issuer_crt)

        # --- <dest> Destinatário ---
        # No modelo 65, o destinatário pode ser opcional se venda para consumidor não identificado
        clean_rec_doc = re.sub(r"\D", "", doc.recipient_cnpj_cpf or "")
        if clean_rec_doc or (doc.recipient_name and doc.recipient_name != "CONSUMIDOR NAO IDENTIFICADO"):
            dest = ET.SubElement(infNFe, "dest")
            if len(clean_rec_doc) == 11:
                ET.SubElement(dest, "CPF").text = clean_rec_doc
            elif len(clean_rec_doc) == 14:
                ET.SubElement(dest, "CNPJ").text = clean_rec_doc.zfill(14)
            ET.SubElement(dest, "xNome").text = (doc.recipient_name or "CONSUMIDOR FINAL")[:60]

            if model_str != "65":
                enderDest = ET.SubElement(dest, "enderDest")
                r_addr = doc.recipient_address or {}
                ET.SubElement(enderDest, "xLgr").text = str(r_addr.get("xLgr", "Av Central"))[:60]
                ET.SubElement(enderDest, "nro").text = str(r_addr.get("nro", "500"))[:60]
                ET.SubElement(enderDest, "xBairro").text = str(r_addr.get("xBairro", "Bairro"))[:60]
                ET.SubElement(enderDest, "cMun").text = str(r_addr.get("cMun", "3550308"))
                ET.SubElement(enderDest, "xMun").text = str(r_addr.get("xMun", "Sao Paulo"))[:60]
                ET.SubElement(enderDest, "UF").text = doc.recipient_uf.upper()

            if doc.recipient_is_tax_contributor and doc.recipient_ie:
                ET.SubElement(dest, "indIEDest").text = "1"
                ET.SubElement(dest, "IE").text = re.sub(r"\D", "", doc.recipient_ie)
            else:
                ET.SubElement(dest, "indIEDest").text = "9"  # Não Contribuinte

        # --- <det> Itens da Nota ---
        for item in doc.items:
            det = ET.SubElement(infNFe, "det", attrib={"nItem": str(item.item_number)})
            
            prod = ET.SubElement(det, "prod")
            ET.SubElement(prod, "cProd").text = str(item.product_code)[:60]
            ET.SubElement(prod, "cEAN").text = item.gtin if item.gtin else "SEM GTIN"
            ET.SubElement(prod, "xProd").text = str(item.description)[:120]
            ET.SubElement(prod, "NCM").text = str(item.ncm).zfill(8)
            if item.cest:
                ET.SubElement(prod, "CEST").text = str(item.cest).zfill(7)
            ET.SubElement(prod, "CFOP").text = str(item.cfop).zfill(4)
            ET.SubElement(prod, "uCom").text = str(item.uCom)[:6]
            ET.SubElement(prod, "qCom").text = f"{float(item.qCom):.4f}"
            ET.SubElement(prod, "vUnCom").text = f"{float(item.vUnCom):.4f}"
            ET.SubElement(prod, "vProd").text = f"{float(item.vProd):.2f}"
            ET.SubElement(prod, "cEANTrib").text = item.gtin if item.gtin else "SEM GTIN"
            ET.SubElement(prod, "uTrib").text = str(item.uCom)[:6]
            ET.SubElement(prod, "qTrib").text = f"{float(item.qCom):.4f}"
            ET.SubElement(prod, "vUnTrib").text = f"{float(item.vUnCom):.4f}"
            ET.SubElement(prod, "indTot").text = "1"

            # <imposto> Tributação a partir do TaxSnapshot
            snap = item.tax_snapshot_json or {}
            imposto = ET.SubElement(det, "imposto")

            # <ICMS>
            icms_wrapper = ET.SubElement(imposto, "ICMS")
            icms_data = snap.get("icms", {})
            cst_csosn = icms_data.get("cst_csosn", "102")

            if len(cst_csosn) == 3:  # Simples Nacional (ICMSSN102 / ICMSSN101)
                tag_name = f"ICMSSN{cst_csosn}"
                icms_sn = ET.SubElement(icms_wrapper, tag_name)
                ET.SubElement(icms_sn, "orig").text = str(snap.get("origem", "0"))
                ET.SubElement(icms_sn, "CSOSN").text = cst_csosn
                if cst_csosn == "101":
                    ET.SubElement(icms_sn, "pCredSN").text = f"{float(icms_data.get('pCredSN', 0.0)):.2f}"
                    ET.SubElement(icms_sn, "vCredICMSSN").text = f"{float(icms_data.get('vCredICMSSN', 0.0)):.2f}"
            else:  # Regime Normal (ICMS00 / ICMS40 / ICMS60)
                tag_name = f"ICMS{cst_csosn.zfill(2)}"
                icms_rn = ET.SubElement(icms_wrapper, tag_name)
                ET.SubElement(icms_rn, "orig").text = str(snap.get("origem", "0"))
                ET.SubElement(icms_rn, "CST").text = cst_csosn.zfill(2)
                if cst_csosn == "00":
                    ET.SubElement(icms_rn, "modBC").text = "3"
                    ET.SubElement(icms_rn, "vBC").text = f"{float(icms_data.get('vBC_ICMS', 0.0)):.2f}"
                    ET.SubElement(icms_rn, "pICMS").text = f"{float(icms_data.get('pICMS', 0.0)):.2f}"
                    ET.SubElement(icms_rn, "vICMS").text = f"{float(icms_data.get('vICMS', 0.0)):.2f}"

            # <PIS>
            pis_wrapper = ET.SubElement(imposto, "PIS")
            pis_data = snap.get("pis", {})
            cst_pis = pis_data.get("cst_pis", "07")
            if cst_pis in ["01", "02"]:
                pis_aliq = ET.SubElement(pis_wrapper, "PISAliq")
                ET.SubElement(pis_aliq, "CST").text = cst_pis
                ET.SubElement(pis_aliq, "vBC").text = f"{float(pis_data.get('vBC_PIS', 0.0)):.2f}"
                ET.SubElement(pis_aliq, "pPIS").text = f"{float(pis_data.get('pPIS', 0.0)):.2f}"
                ET.SubElement(pis_aliq, "vPIS").text = f"{float(pis_data.get('vPIS', 0.0)):.2f}"
            else:
                pis_nt = ET.SubElement(pis_wrapper, "PISNT")
                ET.SubElement(pis_nt, "CST").text = cst_pis

            # <COFINS>
            cofins_wrapper = ET.SubElement(imposto, "COFINS")
            cofins_data = snap.get("cofins", {})
            cst_cofins = cofins_data.get("cst_cofins", "07")
            if cst_cofins in ["01", "02"]:
                cofins_aliq = ET.SubElement(cofins_wrapper, "COFINSAliq")
                ET.SubElement(cofins_aliq, "CST").text = cst_cofins
                ET.SubElement(cofins_aliq, "vBC").text = f"{float(cofins_data.get('vBC_COFINS', 0.0)):.2f}"
                ET.SubElement(cofins_aliq, "pCOFINS").text = f"{float(cofins_data.get('pCOFINS', 0.0)):.2f}"
                ET.SubElement(cofins_aliq, "vCOFINS").text = f"{float(cofins_data.get('vCOFINS', 0.0)):.2f}"
            else:
                cofins_nt = ET.SubElement(cofins_wrapper, "COFINSNT")
                ET.SubElement(cofins_nt, "CST").text = cst_cofins

        # --- <total> Totais Consolidados ---
        total = ET.SubElement(infNFe, "total")
        ICMSTot = ET.SubElement(total, "ICMSTot")
        ET.SubElement(ICMSTot, "vBC").text = f"{float(getattr(doc, 'vBC', 0.0) or 0.0):.2f}"
        ET.SubElement(ICMSTot, "vICMS").text = f"{float(getattr(doc, 'vICMS', 0.0) or 0.0):.2f}"
        ET.SubElement(ICMSTot, "vICMSDeson").text = "0.00"
        ET.SubElement(ICMSTot, "vFCP").text = f"{float(getattr(doc, 'vFCP', 0.0) or 0.0):.2f}"
        ET.SubElement(ICMSTot, "vBCST").text = f"{float(getattr(doc, 'vBCST', 0.0) or 0.0):.2f}"
        ET.SubElement(ICMSTot, "vST").text = f"{float(getattr(doc, 'vST', 0.0) or 0.0):.2f}"
        ET.SubElement(ICMSTot, "vFCPST").text = "0.00"
        ET.SubElement(ICMSTot, "vFCPSTRet").text = "0.00"
        ET.SubElement(ICMSTot, "vProd").text = f"{float(getattr(doc, 'vProd', 0.0) or 0.0):.2f}"
        ET.SubElement(ICMSTot, "vFrete").text = f"{float(getattr(doc, 'vFrete', 0.0) or 0.0):.2f}"
        ET.SubElement(ICMSTot, "vSeguro").text = f"{float(getattr(doc, 'vSeguro', 0.0) or 0.0):.2f}"
        ET.SubElement(ICMSTot, "vDesc").text = f"{float(getattr(doc, 'vDesc', 0.0) or 0.0):.2f}"
        ET.SubElement(ICMSTot, "vII").text = "0.00"
        ET.SubElement(ICMSTot, "vIPI").text = f"{float(getattr(doc, 'vIPI', 0.0) or 0.0):.2f}"
        ET.SubElement(ICMSTot, "vIPIDevol").text = "0.00"
        ET.SubElement(ICMSTot, "vPIS").text = f"{float(getattr(doc, 'vPIS', 0.0) or 0.0):.2f}"
        ET.SubElement(ICMSTot, "vCOFINS").text = f"{float(getattr(doc, 'vCOFINS', 0.0) or 0.0):.2f}"
        ET.SubElement(ICMSTot, "vOutro").text = f"{float(getattr(doc, 'vOutro', 0.0) or 0.0):.2f}"
        ET.SubElement(ICMSTot, "vNF").text = f"{float(getattr(doc, 'vNF', 0.0) or 0.0):.2f}"

        # --- <transp> Modalidade de Transporte ---
        transp = ET.SubElement(infNFe, "transp")
        ET.SubElement(transp, "modFrete").text = "9"  # 9=Sem Ocorrência de Transporte

        # --- <pag> Pagamentos ---
        pag = ET.SubElement(infNFe, "pag")
        payments_list = getattr(doc, "payments_info", None) or []
        
        if payments_list:
            t_pag_map = {
                "MONEY": "01",
                "CREDIT_CARD": "03",
                "DEBIT_CARD": "04",
                "PIX": "17",
                "OTHER": "99",
            }
            total_change = 0.0
            for p in payments_list:
                detPag = ET.SubElement(pag, "detPag")
                t_pag = t_pag_map.get(str(p.get("payment_method", "MONEY")).upper(), "01")
                v_pag = float(p.get("amount", doc.vNF))
                change = float(p.get("change_amount", 0.0))
                total_change += change
                ET.SubElement(detPag, "tPag").text = t_pag
                ET.SubElement(detPag, "vPag").text = f"{v_pag:.2f}"

            if total_change > 0:
                ET.SubElement(pag, "vTroco").text = f"{total_change:.2f}"
        else:
            detPag = ET.SubElement(pag, "detPag")
            ET.SubElement(detPag, "tPag").text = "01"  # 01=Dinheiro/Vista
            ET.SubElement(detPag, "vPag").text = f"{float(doc.vNF):.2f}"

        # --- <infAdic> Informações Adicionais ---
        add_info = getattr(doc, "additional_information", None)
        if add_info:
            infAdic = ET.SubElement(infNFe, "infAdic")
            ET.SubElement(infAdic, "infCpl").text = str(add_info)[:5000]

        # --- <infNFeSupl> Apenas para NFC-e Modelo 65 ---
        qr_code_url = getattr(doc, "qr_code_url", None)
        url_chave = getattr(doc, "url_chave", None)

        if model_str == "65" and qr_code_url:
            infNFeSupl = ET.SubElement(NFe, "infNFeSupl")
            ET.SubElement(infNFeSupl, "qrCode").text = qr_code_url
            if url_chave:
                ET.SubElement(infNFeSupl, "urlChave").text = url_chave

        # Formatação XML limpa sem declarações extras
        raw_xml_str = ET.tostring(NFe, encoding="utf-8").decode("utf-8")
        return raw_xml_str

    @staticmethod
    def build_nfe_proc_xml(
        signed_nfe_xml: str,
        protocol_number: str,
        digest_value: str,
        status_code: int = 100,
        reason: str = "Autorizado o uso da NF-e",
        dh_rec: Optional[datetime] = None
    ) -> str:
        """
        Empacota o XML assinado da NF-e com o nó de protocolo SEFAZ <protNFe> formando o <nfeProc>.
        """
        if dh_rec is None:
            dh_rec = datetime.now(timezone.utc)

        dh_str = dh_rec.strftime("%Y-%m-%dT%H:%M:%S%z")
        if not dh_str.endswith("+00:00") and not re.search(r"[+-]\d{2}:\d{2}$", dh_str):
            dh_str += "-03:00"

        # Extrair a chave de acesso do XML assinado
        access_key_match = re.search(r'Id="NFe(\d{44})"', signed_nfe_xml)
        access_key = access_key_match.group(1) if access_key_match else "0" * 44

        prot_xml = f"""<protNFe versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe">
  <infProt>
    <tpAmb>2</tpAmb>
    <verAplic>2.0.0</verAplic>
    <chNFe>{access_key}</chNFe>
    <dhRecBto>{dh_str}</dhRecBto>
    <nProt>{protocol_number}</nProt>
    <digVal>{digest_value}</digVal>
    <cStat>{status_code}</cStat>
    <xMotivo>{reason}</xMotivo>
  </infProt>
</protNFe>"""

        proc_xml = f"""<nfeProc versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe">
{signed_nfe_xml}
{prot_xml}
</nfeProc>"""

        return proc_xml
