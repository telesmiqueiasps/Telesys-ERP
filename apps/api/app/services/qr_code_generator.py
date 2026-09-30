import hashlib
from typing import Optional


# Tabela oficial de URLs de QR Code da NFC-e por UF (Homologação e Produção)
SEFAZ_QRCODE_URLS = {
    "HOMOLOGATION": {
        "SP": "https://www.homologacao.nfce.fazenda.sp.gov.br/qrcode",
        "PR": "http://www.fazenda.pr.gov.br/nfce/qrcode",
        "RS": "https://www.sefaz.rs.gov.br/NFCE/NFCE-COM.aspx",
        "RJ": "http://www.fazenda.rj.gov.br/nfce/qrcode",
        "MG": "https://nfce.fazenda.mg.gov.br/portalnfce/sistema/qrcode.xhtml",
        "BA": "http://hnfce.sefaz.ba.gov.br/hdc/QRConNFCe.aspx",
        "GO": "http://hnfce.sefaz.go.gov.br/post/QRConNFCe",
        "PE": "https://nfcehomolog.sefaz.pe.gov.br/nfce-web/consultarNFCe",
        "DEFAULT": "https://www.homologacao.nfce.fazenda.sp.gov.br/qrcode",
    },
    "PRODUCTION": {
        "SP": "https://www.nfce.fazenda.sp.gov.br/qrcode",
        "PR": "http://www.fazenda.pr.gov.br/nfce/qrcode",
        "RS": "https://www.sefaz.rs.gov.br/NFCE/NFCE-COM.aspx",
        "RJ": "http://www.fazenda.rj.gov.br/nfce/qrcode",
        "MG": "https://nfce.fazenda.mg.gov.br/portalnfce/sistema/qrcode.xhtml",
        "BA": "http://nfc.sefaz.ba.gov.br/hdc/QRConNFCe.aspx",
        "GO": "http://nfc.sefaz.go.gov.br/post/QRConNFCe",
        "PE": "https://nfce.sefaz.pe.gov.br/nfce-web/consultarNFCe",
        "DEFAULT": "https://www.nfce.fazenda.sp.gov.br/qrcode",
    },
}

SEFAZ_CONSULTA_URLS = {
    "HOMOLOGATION": {
        "SP": "https://www.homologacao.nfce.fazenda.sp.gov.br/consulta",
        "PR": "http://www.fazenda.pr.gov.br/nfce/consulta",
        "RS": "https://www.sefaz.rs.gov.br/NFCE/NFCE-COM.aspx",
        "DEFAULT": "https://www.homologacao.nfce.fazenda.sp.gov.br/consulta",
    },
    "PRODUCTION": {
        "SP": "https://www.nfce.fazenda.sp.gov.br/consulta",
        "PR": "http://www.fazenda.pr.gov.br/nfce/consulta",
        "RS": "https://www.sefaz.rs.gov.br/NFCE/NFCE-COM.aspx",
        "DEFAULT": "https://www.nfce.fazenda.sp.gov.br/consulta",
    },
}


class NfceQrCodeGenerator:
    """Gerador oficial do QR Code da NFC-e Modelo 65 (NT 2015.002 / Padrão QR Code v5.0)."""

    @classmethod
    def get_qrcode_base_url(cls, uf: str, environment: int = 2) -> str:
        env_key = "PRODUCTION" if environment == 1 else "HOMOLOGATION"
        urls = SEFAZ_QRCODE_URLS.get(env_key, SEFAZ_QRCODE_URLS["HOMOLOGATION"])
        return urls.get(uf.upper(), urls["DEFAULT"])

    @classmethod
    def get_url_chave(cls, uf: str, environment: int = 2) -> str:
        env_key = "PRODUCTION" if environment == 1 else "HOMOLOGATION"
        urls = SEFAZ_CONSULTA_URLS.get(env_key, SEFAZ_CONSULTA_URLS["HOMOLOGATION"])
        return urls.get(uf.upper(), urls["DEFAULT"])

    @classmethod
    def generate_qr_code_str(
        cls,
        access_key: str,
        environment: int,
        uf: str,
        issue_date_hex: str,
        vNF: float,
        vICMS: float,
        digest_value_hex: str,
        csc_id: str = "000001",
        csc_secret: str = "123456",
        cDest: Optional[str] = None,
    ) -> str:
        """Gera a string completa do QR Code da NFC-e.
        
        Estrutura de dados:
        chNFe|2|tpAmb|cDest|dhEmi|vNF|vICMS|digVal|idCSC
        
        Seguida do cálculo do Hash SHA-1 (em hexadecimal maiúsculo) com a inclusão do csc_secret.
        """
        # Formatação dos valores monetários sem vírgula ou ponto, mantendo 2 casas decimais
        str_vNF = f"{vNF:.2f}"
        str_vICMS = f"{vICMS:.2f}"
        str_cDest = cDest or ""
        str_csc_id = str(csc_id or "000001").zfill(6)
        str_csc_secret = csc_secret or "123456"

        # 1. Monta os campos que compõem o payload do QR Code
        # Versão do QR Code: 2
        params = [
            access_key,
            "2",
            str(environment),
            str_cDest,
            issue_date_hex,
            str_vNF,
            str_vICMS,
            digest_value_hex,
            str_csc_id,
        ]

        raw_payload = "|".join(params)

        # 2. Concatena com a chave secreta do CSC para gerar o Hash SHA-1
        string_to_hash = raw_payload + str_csc_secret
        hash_sha1 = hashlib.sha1(string_to_hash.encode("utf-8")).hexdigest().upper()

        # 3. Monta a URL final com o parâmetro ?p=payload|hash
        base_url = cls.get_qrcode_base_url(uf, environment)
        separator = "&" if "?" in base_url else "?"
        final_qr_code_url = f"{base_url}{separator}p={raw_payload}|{hash_sha1}"

        return final_qr_code_url
