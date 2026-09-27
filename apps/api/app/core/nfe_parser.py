import xml.etree.ElementTree as ET
from datetime import datetime, date
from typing import Dict, List, Any, Optional

NFE_NAMESPACES = {
    "nfe": "http://www.portalfiscal.inf.br/nfe"
}


def find_text(element: ET.Element, path: str, default: str = "") -> str:
    """
    Busca o texto de um elemento com ou sem namespace NFe.
    """
    if element is None:
        return default

    # Tenta com o prefixo nfe:
    found = element.find(path, NFE_NAMESPACES)
    if found is not None and found.text:
        return found.text.strip()

    # Tenta sem namespace (para tags simplificadas)
    clean_path = "/".join(p.split(":")[-1] for p in path.split("/"))
    found = element.find(clean_path)
    if found is not None and found.text:
        return found.text.strip()

    return default


def parse_nfe_xml_bytes(xml_bytes: bytes) -> Dict[str, Any]:
    """
    Faz o parse completo dos dados de uma NF-e a partir dos bytes do arquivo XML.
    """
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as err:
        raise ValueError(f"Arquivo XML de NF-e inválido ou corrompido: {str(err)}")

    # Encontrar nó infNFe
    inf_nfe = root.find(".//nfe:infNFe", NFE_NAMESPACES)
    if inf_nfe is None:
        inf_nfe = root.find(".//infNFe")
    if inf_nfe is None:
        raise ValueError("Estrutura da NF-e não possui a tag <infNFe> válida.")

    # Extração da Chave de Acesso de 44 dígitos
    ch_nfe = ""
    raw_id = inf_nfe.attrib.get("Id", "")
    if raw_id.startswith("NFe"):
        ch_nfe = raw_id[3:]
    else:
        ch_nfe = raw_id

    if not ch_nfe:
        ch_nfe = find_text(root, ".//nfe:protNFe/nfe:infProt/nfe:chNFe")

    # Ide (Identificação do Documento)
    ide = inf_nfe.find("nfe:ide", NFE_NAMESPACES) or inf_nfe.find("ide")
    n_nf = find_text(ide, "nfe:nNF") or find_text(ide, "nNF")
    serie = find_text(ide, "nfe:serie") or find_text(ide, "serie")
    dh_emi_raw = find_text(ide, "nfe:dhEmi") or find_text(ide, "dEmi")

    # Emitente (Fornecedor)
    emit = inf_nfe.find("nfe:emit", NFE_NAMESPACES) or inf_nfe.find("emit")
    supplier_cnpj = find_text(emit, "nfe:CNPJ") or find_text(emit, "CNPJ") or find_text(emit, "nfe:CPF") or find_text(emit, "CPF")
    supplier_name = find_text(emit, "nfe:xNome") or find_text(emit, "xNome")
    supplier_trade = find_text(emit, "nfe:xFant") or find_text(emit, "xFant") or supplier_name
    supplier_ie = find_text(emit, "nfe:IE") or find_text(emit, "IE")

    ender_emit = emit.find("nfe:enderEmit", NFE_NAMESPACES) if emit is not None else None
    if ender_emit is None and emit is not None:
        ender_emit = emit.find("enderEmit")

    supplier_street = find_text(ender_emit, "nfe:xLgr") or find_text(ender_emit, "xLgr")
    supplier_number = find_text(ender_emit, "nfe:nro") or find_text(ender_emit, "nro")
    supplier_bairro = find_text(ender_emit, "nfe:xBairro") or find_text(ender_emit, "xBairro")
    supplier_city = find_text(ender_emit, "nfe:xMun") or find_text(ender_emit, "xMun")
    supplier_state = find_text(ender_emit, "nfe:UF") or find_text(ender_emit, "UF")
    supplier_cep = find_text(ender_emit, "nfe:CEP") or find_text(ender_emit, "CEP")
    supplier_phone = find_text(ender_emit, "nfe:fone") or find_text(ender_emit, "fone")

    # Itens (det)
    items: List[Dict[str, Any]] = []
    det_list = inf_nfe.findall("nfe:det", NFE_NAMESPACES) or inf_nfe.findall("det")

    for det in det_list:
        n_item = int(det.attrib.get("nItem", len(items) + 1))
        prod = det.find("nfe:prod", NFE_NAMESPACES) or det.find("prod")
        if prod is None:
            continue

        c_prod = find_text(prod, "nfe:cProd") or find_text(prod, "cProd")
        c_ean = find_text(prod, "nfe:cEAN") or find_text(prod, "cEAN")
        if c_ean.upper() in ["SEM GTIN", "SEM EAN", ""]:
            c_ean = ""

        x_prod = find_text(prod, "nfe:xProd") or find_text(prod, "xProd")
        ncm = find_text(prod, "nfe:NCM") or find_text(prod, "NCM")
        cest = find_text(prod, "nfe:CEST") or find_text(prod, "CEST")
        u_com = find_text(prod, "nfe:uCom") or find_text(prod, "uCom") or "UN"

        try:
            q_com = float(find_text(prod, "nfe:qCom") or find_text(prod, "qCom") or "0")
            v_un_com = float(find_text(prod, "nfe:vUnCom") or find_text(prod, "vUnCom") or "0")
            v_prod = float(find_text(prod, "nfe:vProd") or find_text(prod, "vProd") or "0")
        except ValueError:
            q_com, v_un_com, v_prod = 0.0, 0.0, 0.0

        items.append({
            "item_number": n_item,
            "cProd": c_prod,
            "cEAN": c_ean if c_ean else None,
            "xProd": x_prod,
            "ncm": ncm if ncm else None,
            "cest": cest if cest else None,
            "uCom": u_com.upper(),
            "qCom": q_com,
            "vUnCom": v_un_com,
            "vProd": v_prod,
        })

    # Duplicatas / Faturas (cobr / dup)
    duplicatas: List[Dict[str, Any]] = []
    dup_list = inf_nfe.findall(".//nfe:cobr/nfe:dup", NFE_NAMESPACES) or root.findall(".//cobr/dup")

    for dup in dup_list:
        n_dup = find_text(dup, "nfe:nDup") or find_text(dup, "nDup")
        d_venc = find_text(dup, "nfe:dVenc") or find_text(dup, "dVenc")
        try:
            v_dup = float(find_text(dup, "nfe:vDup") or find_text(dup, "vDup") or "0")
        except ValueError:
            v_dup = 0.0

        duplicatas.append({
            "nDup": n_dup,
            "dVenc": d_venc,
            "vDup": v_dup,
        })

    # Totais (ICMSTot)
    v_prod_total = 0.0
    v_nf_total = 0.0
    total = inf_nfe.find("nfe:total/nfe:ICMSTot", NFE_NAMESPACES) or inf_nfe.find("total/ICMSTot")
    if total is not None:
        try:
            v_prod_total = float(find_text(total, "nfe:vProd") or find_text(total, "vProd") or "0")
            v_nf_total = float(find_text(total, "nfe:vNF") or find_text(total, "vNF") or "0")
        except ValueError:
            pass

    return {
        "chNFe": ch_nfe,
        "nNF": n_nf,
        "serie": serie,
        "dhEmi": dh_emi_raw,
        "supplier": {
            "document": supplier_cnpj,
            "name": supplier_name,
            "trade_name": supplier_trade,
            "state_registration": supplier_ie,
            "phone": supplier_phone,
            "address_street": supplier_street,
            "address_number": supplier_number,
            "address_neighborhood": supplier_bairro,
            "city": supplier_city,
            "state": supplier_state,
            "postal_code": supplier_cep,
        },
        "items": items,
        "duplicatas": duplicatas,
        "total_vProd": v_prod_total,
        "total_vNF": v_nf_total,
    }
