import re
from typing import Dict, Any, List
from datetime import datetime


class DanfeNfceRenderer:
    """Renderizador do DANFE NFC-e (Modelo 65) em formato HTML/CSS responsivo para impressoras térmicas (80mm/58mm)."""

    @classmethod
    def render_html(cls, doc: Any, qr_code_url: str = "", url_chave: str = "") -> str:
        """Gera o HTML pronto para impressão em bobina térmica (80mm)."""
        
        # Formatador de Chave de Acesso (44 dígitos agrupados de 4 em 4)
        access_key_raw = re.sub(r"\D", "", getattr(doc, "access_key", "") or "")
        formatted_key = " ".join([access_key_raw[i:i+4] for i in range(0, len(access_key_raw), 4)])

        is_contingency = getattr(doc, "issue_type", 1) == 9 or getattr(doc, "status", "") == "AUTHORIZED_OFFLINE"

        # Itens
        items: List[Any] = list(getattr(doc, "items", []) or [])
        items_html = ""
        total_items_qty = 0

        for idx, item in enumerate(items, start=1):
            prod_code = getattr(item, "product_code", "") or f"PROD{idx}"
            description = getattr(item, "description", "") or "PRODUTO"
            qCom = float(getattr(item, "qCom", 1.0) or 1.0)
            uCom = getattr(item, "uCom", "UN") or "UN"
            vUnCom = float(getattr(item, "vUnCom", 0.0) or 0.0)
            vProd = float(getattr(item, "vProd", 0.0) or 0.0)
            total_items_qty += int(qCom)

            items_html += f"""
            <tr>
              <td colspan="4" class="prod-desc">{prod_code} {description[:40]}</td>
            </tr>
            <tr class="item-values">
              <td class="col-qty">{qCom:.3f} {uCom}</td>
              <td class="col-x">x</td>
              <td class="col-unit">R$ {vUnCom:.2f}</td>
              <td class="col-total">R$ {vProd:.2f}</td>
            </tr>
            """

        # Formas de pagamento
        payments = getattr(doc, "payments_info", []) or []
        payments_html = ""
        if payments:
            for p in payments:
                method_name = str(p.get("payment_method", "DINHEIRO")).upper()
                amount = float(p.get("amount", 0.0))
                payments_html += f"""
                <div class="row">
                  <span>{method_name}</span>
                  <span>R$ {amount:.2f}</span>
                </div>
                """
        else:
            vNF = float(getattr(doc, "vNF", 0.0) or 0.0)
            payments_html = f"""
            <div class="row">
              <span>DINHEIRO</span>
              <span>R$ {vNF:.2f}</span>
            </div>
            """

        # Consumidor
        rec_doc = getattr(doc, "recipient_cnpj_cpf", "") or getattr(doc, "recipient_document", "") or ""
        rec_name = getattr(doc, "recipient_name", "") or "CONSUMIDOR NAO IDENTIFICADO"
        if rec_doc:
            rec_str = f"CPF/CNPJ: {rec_doc} - {rec_name}"
        else:
            rec_str = "CONSUMIDOR NÃO IDENTIFICADO"

        created_at = getattr(doc, "created_at", None)
        issue_str = created_at.strftime("%d/%m/%Y %H:%M:%S") if isinstance(created_at, datetime) else str(created_at or "")

        protocol = getattr(doc, "protocol_number", None) or "EMISSÃO EM CONTINGÊNCIA (PENDENTE)"
        authorized_at = getattr(doc, "authorized_at", None)
        auth_str = authorized_at.strftime("%d/%m/%Y %H:%M:%S") if isinstance(authorized_at, datetime) else issue_str

        contingency_banner = ""
        if is_contingency:
            contingency_banner = """
            <div class="contingency-banner">
              EMITIDA EM CONTINGÊNCIA OFFLINE<br/>
              Via do Consumidor
            </div>
            """

        html_template = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>DANFE NFC-e - {getattr(doc, 'number', '')}</title>
  <style>
    @page {{
      margin: 0;
      size: 80mm auto;
    }}
    body {{
      font-family: 'Courier New', Courier, monospace;
      font-size: 11px;
      width: 76mm;
      margin: 2mm auto;
      padding: 0;
      color: #000;
      background: #fff;
    }}
    .center {{ text-align: center; }}
    .bold {{ font-weight: bold; }}
    .border-top {{ border-top: 1px dashed #000; padding-top: 4px; margin-top: 4px; }}
    .border-bottom {{ border-bottom: 1px dashed #000; padding-bottom: 4px; margin-bottom: 4px; }}
    .company-title {{ font-size: 13px; font-weight: bold; text-transform: uppercase; }}
    .doc-title {{ font-size: 12px; font-weight: bold; margin: 4px 0; }}
    .contingency-banner {{
      background: #000;
      color: #fff;
      font-weight: bold;
      text-align: center;
      padding: 4px;
      margin: 4px 0;
      font-size: 11px;
    }}
    table {{ width: 100%; border-collapse: collapse; }}
    .prod-desc {{ font-size: 10px; font-weight: bold; text-align: left; padding-top: 2px; }}
    .item-values td {{ font-size: 10px; }}
    .col-qty {{ width: 35%; text-align: left; }}
    .col-x {{ width: 5%; text-align: center; }}
    .col-unit {{ width: 30%; text-align: right; }}
    .col-total {{ width: 30%; text-align: right; font-weight: bold; }}
    .row {{ display: flex; justify-content: space-between; margin: 2px 0; }}
    .key-box {{
      font-size: 9px;
      word-break: break-all;
      text-align: center;
      letter-spacing: 0.5px;
      margin: 4px 0;
    }}
    .qr-container {{
      text-align: center;
      margin: 8px 0;
    }}
    .qr-placeholder {{
      display: inline-block;
      width: 140px;
      height: 140px;
      border: 2px solid #000;
      line-height: 140px;
      font-size: 10px;
      font-weight: bold;
    }}
  </style>
</head>
<body>
  <!-- CABEÇALHO EMITENTE -->
  <div class="center border-bottom">
    <div class="company-title">{getattr(doc, 'issuer_name', 'EMPRESA EMITENTE')[:50]}</div>
    <div>CNPJ: {getattr(doc, 'issuer_cnpj', '')}  IE: {getattr(doc, 'issuer_ie', 'ISENTO')}</div>
    <div>{getattr(doc, 'issuer_uf', 'SP')} - BRASIL</div>
  </div>

  {contingency_banner}

  <div class="center doc-title">
    DANFE NFC-e - Nota Fiscal de Consumidor Eletrônica
  </div>
  <div class="center border-bottom" style="font-size: 9px;">
    Não permite aproveitamento de crédito de ICMS
  </div>

  <!-- TABELA DE ITENS -->
  <table>
    <thead>
      <tr class="border-bottom" style="font-size: 9px; text-align: left;">
        <th colspan="2">ITEM / CÓDIGO / DESCRIÇÃO</th>
        <th style="text-align: right;">QTD x UN</th>
        <th style="text-align: right;">V.TOTAL</th>
      </tr>
    </thead>
    <tbody>
      {items_html}
    </tbody>
  </table>

  <!-- TOTAIS -->
  <div class="border-top">
    <div class="row bold">
      <span>QTD. TOTAL DE ITENS</span>
      <span>{len(items)}</span>
    </div>
    <div class="row">
      <span>VALOR TOTAL R$</span>
      <span>{float(getattr(doc, 'vProd', 0.0) or 0.0):.2f}</span>
    </div>
    <div class="row">
      <span>DESCONTOS R$</span>
      <span>{float(getattr(doc, 'vDesc', 0.0) or 0.0):.2f}</span>
    </div>
    <div class="row bold" style="font-size: 13px;">
      <span>VALOR A PAGAR R$</span>
      <span>{float(getattr(doc, 'vNF', 0.0) or 0.0):.2f}</span>
    </div>
  </div>

  <!-- FORMAS DE PAGAMENTO -->
  <div class="border-top">
    <div class="bold">FORMA DE PAGAMENTO</div>
    {payments_html}
  </div>

  <!-- CONSUMIDOR -->
  <div class="border-top border-bottom center">
    <div class="bold">CONSUMIDOR</div>
    <div>{rec_str}</div>
  </div>

  <!-- INFORMACÕES DA SEFAZ -->
  <div class="center" style="margin-top: 4px;">
    <div>NFC-e Nº {getattr(doc, 'number', 0)}  Série {getattr(doc, 'series', 1)}  Emissão: {issue_str}</div>
    <div class="bold">CHAVE DE ACESSO</div>
    <div class="key-box">{formatted_key}</div>
    <div>Consulta em: {url_chave or 'https://www.homologacao.nfce.fazenda.sp.gov.br/consulta'}</div>
    <div style="margin-top: 4px;">Protocolo: {protocol} - {auth_str}</div>
  </div>

  <!-- QR CODE SEFAZ -->
  <div class="qr-container">
    <div class="qr-placeholder">
      [ QR CODE SEFAZ ]
    </div>
    <div style="font-size: 8px; word-break: break-all; margin-top: 2px;">{qr_code_url[:80]}...</div>
  </div>

  <div class="center border-top" style="font-size: 9px; margin-top: 6px;">
    Telesys ERP + PDV Fiscal v2.0
  </div>
</body>
</html>
"""
        return html_template
